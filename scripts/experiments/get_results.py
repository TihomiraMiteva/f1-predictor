import requests
import pandas as pd

SEASON = 2023  # change as needed

url = f"http://ergast.com/api/f1/{SEASON}/results.json?limit=1000"
resp = requests.get(url)
resp.raise_for_status()
data = resp.json()

races = data["MRData"]["RaceTable"]["Races"]

rows = []
for race in races:
    round_no = int(race["round"])
    race_name = race["raceName"]
    date = race["date"]
    circuit = race["Circuit"]["circuitName"]

    for result in race["Results"]:
        driver = result["Driver"]
        constructor = result["Constructor"]

        rows.append({
            "season": SEASON,
            "round": round_no,
            "race_name": race_name,
            "date": date,
            "circuit": circuit,
            "position": int(result["position"]),
            "driver_code": driver.get("code"),
            "driver_name": f'{driver["givenName"]} {driver["familyName"]}',
            "constructor": constructor["name"],
            "grid": int(result["grid"]),
            "laps": int(result["laps"]),
            "status": result["status"],
            "points": float(result["points"]),
        })

df = pd.DataFrame(rows)
df.to_csv(f"f1_{SEASON}_results.csv", index=False)
print(df.head())
print(f"\nSaved f1_{SEASON}_results.csv with {len(df)} rows")
