from pathlib import Path
from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score

app = Flask(__name__, template_folder=str(Path(__file__).resolve().parent / 'templates'))

# Global variables for model and data
model = None
df_full = None
driver_info = None
circuits = None

# Model metadata
feature_columns = []
categorical_columns = []
numeric_columns = []
q3_median_value = None


def load_and_train_model():
    global model, df_full, driver_info, circuits, feature_columns, categorical_columns, numeric_columns, q3_median_value

    # Load data
    df = pd.read_csv(Path(__file__).resolve().parent.parent / 'data/processed/f1_combined_2021_2025_final.csv')

    # Convert q3 time strings to seconds
    df['q3'] = df['q3'].apply(time_string_to_seconds)

    # Prepare data
    df["race_position"] = pd.to_numeric(df["position"], errors="coerce").fillna(20)
    df["position_num"] = df["race_position"]

    # Define good performance (top 10)
    df["good_performance"] = (df["position_num"] <= 10).astype(int)

    # Features
    features = ["driverId", "constructorId", "engineManufacturerId", "grand", "turns", "courseLength", "q3"]
    categorical_cols = ["driverId", "constructorId", "engineManufacturerId", "grand"]
    numeric_cols = ["turns", "courseLength", "q3"]

    # Prepare model data
    model_df = df[features + ["good_performance", "date", "position_num"]].copy()
    model_df['engineManufacturerId'] = model_df['engineManufacturerId'].fillna('Unknown')
    q3_median = None

    if "q3" in model_df.columns:
        valid_q3 = model_df['q3'].notna().sum()
        if valid_q3 > 0:
            q3_median = model_df['q3'].median()
            model_df['q3'] = model_df['q3'].fillna(q3_median)
        else:
            model_df = model_df.drop(columns=['q3'])
            features.remove('q3')
            numeric_cols.remove('q3')

    # Remove any remaining rows with NaN values
    model_df = model_df.dropna()

    if model_df.empty:
        missing_report = df[features + ["good_performance"]].isnull().sum()
        raise ValueError(f"No valid data after removing NaN values. Missing values per column:\n{missing_report}")

    X = model_df[features]
    y = model_df["good_performance"]

    # Preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
            ("num", StandardScaler(), numeric_cols)
        ]
    )

    # Train-test split
    stratify_target = y if y.nunique() > 1 else None
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify_target
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=None
        )

    # Model
    knn_model = Pipeline(steps=[
        ("preprocess", preprocessor),
        ("knn", KNeighborsClassifier(n_neighbors=15))
    ])

    # Train
    knn_model.fit(X_train, y_train)

    # Accuracy
    y_pred = knn_model.predict(X_test)
    accuracy = round(accuracy_score(y_test, y_pred), 3)

    # Probability-based Top 3 ranking
    proba = knn_model.predict_proba(X_test)[:, 1]

    results = X_test.copy()
    results["score"] = proba
    results["grand"] = df.loc[X_test.index, "grand"].values
    results["date"] = df.loc[X_test.index, "date"].values
    results["position_num"] = df.loc[X_test.index, "position_num"].values

    # Evaluate Top-3 podium hits
    top3_hits = []
    for (g, d), group in results.groupby(["grand", "date"]):
        true_winner = group[group["position_num"] == 1]
        if true_winner.empty:
            continue
        predicted_top3 = group.sort_values("score", ascending=False).head(3)
        top3_hits.append(true_winner.index[0] in predicted_top3.index)

    top3_accuracy = float(np.mean(top3_hits)) if top3_hits else np.nan

    print(f"Dataset size: {len(model_df)} rows")
    print(f"Accuracy: {accuracy}")
    if not np.isnan(top3_accuracy):
        print(f"Top-3 Accuracy: {round(top3_accuracy, 3)}")
    else:
        print("Top-3 Accuracy: insufficient grouped data")

    # Store global data
    model = knn_model
    df_full = df
    feature_columns = features
    categorical_columns = categorical_cols
    numeric_columns = numeric_cols
    q3_median_value = q3_median

    # Get driver info
    df_sorted = df.sort_values('date', ascending=False)
    driver_columns = ['driverId', 'constructorId', 'engineManufacturerId']
    if 'driverNumber' in df_sorted.columns:
        driver_columns.insert(1, 'driverNumber')
    driver_info = df_sorted.drop_duplicates('driverId')[driver_columns].copy()
    driver_info = driver_info.dropna(subset=['driverId'])

    # Get circuits
    circuits = sorted(df['grand'].dropna().unique().tolist())

    print("Model trained successfully!")

def time_string_to_seconds(time_str):
    """Convert times like '1:21.352' or '81.352' to seconds as float."""
    if time_str is None or (isinstance(time_str, float) and np.isnan(time_str)):
        return np.nan
    try:
        if isinstance(time_str, str):
            value = time_str.strip()
            if not value:
                return np.nan
            if ':' in value:
                minutes, seconds = value.split(':', 1)
                return int(minutes) * 60 + float(seconds)
            return float(value)
        return float(time_str)
    except (ValueError, TypeError):
        return np.nan

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/circuits')
def get_circuits():
    return jsonify(circuits)

@app.route('/api/drivers')
def get_drivers():
    driver_list = []
    for _, row in driver_info.iterrows():
        driver_number = None
        if 'driverNumber' in row and pd.notna(row['driverNumber']):
            try:
                driver_number = int(row['driverNumber'])
            except (TypeError, ValueError):
                driver_number = None
        driver = {
            'id': row['driverId'],
            'number': driver_number,
            'team': row['constructorId'],
            'engine': row['engineManufacturerId'] if pd.notna(row['engineManufacturerId']) else 'Unknown'
        }
        driver_list.append(driver)
    return jsonify(driver_list)

@app.route('/api/circuit-info/<circuit>')
def get_circuit_info(circuit):
    circuit_data = df_full[df_full['grand'] == circuit]
    if circuit_data.empty:
        return jsonify({'error': f'Circuit {circuit} not found'}), 404
    circuit_row = circuit_data.iloc[0]
    return jsonify({
        'turns': int(circuit_row['turns']),
        'courseLength': float(circuit_row['courseLength'])
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 503

    gp_name = data['gpName']
    drivers_data = data['drivers']
    
    # Get circuit info
    circuit_info_df = df_full[df_full['grand'] == gp_name]
    if circuit_info_df.empty:
        return jsonify({'error': f'Circuit {gp_name} not found'}), 400
    circuit_info = circuit_info_df.iloc[0]
    turns = circuit_info['turns']
    course_length = circuit_info['courseLength']
    
    # Prepare prediction data
    prediction_data = []
    
    for driver_data in drivers_data:
        time_seconds = time_string_to_seconds(driver_data.get('time'))
        if 'q3' in feature_columns and np.isnan(time_seconds) and q3_median_value is not None:
            time_seconds = q3_median_value

        prediction_data.append({
            'driverId': driver_data['driverId'],
            'constructorId': driver_data['team'],
            'engineManufacturerId': driver_data.get('engine') or 'Unknown',
            'grand': gp_name,
            'turns': turns,
            'courseLength': course_length,
            'q3': time_seconds,
            'qual_position': driver_data['position']
        })
    
    # Create DataFrame
    pred_df = pd.DataFrame(prediction_data)
    pred_df['engineManufacturerId'] = pred_df['engineManufacturerId'].fillna('Unknown')
    if 'q3' in feature_columns and q3_median_value is not None:
        pred_df['q3'] = pred_df['q3'].fillna(q3_median_value)
    else:
        pred_df = pred_df.drop(columns=['q3'], errors='ignore')
    
    # Get predictions
    X_pred = pred_df[feature_columns]
    
    # Get probability scores
    proba = model.predict_proba(X_pred)[:, 1]
    
    pred_df['score'] = proba
    pred_df = pred_df.sort_values('score', ascending=False).reset_index(drop=True)
    
    # Prepare results
    results = []
    for idx, row in pred_df.iterrows():
        results.append({
            'position': idx + 1,
            'driverId': row['driverId'],
            'team': row['constructorId'],
            'engine': row['engineManufacturerId'],
            'score': float(row['score']),
            'qualPosition': int(row['qual_position']),
            'positionChange': int(row['qual_position']) - (idx + 1)
        })
    
    return jsonify(results)

if __name__ == '__main__':
    print("Loading data and training model...")
    load_and_train_model()
    print("Starting Flask server...")
    app.run(host='127.0.0.1', debug=False, port=5000)
