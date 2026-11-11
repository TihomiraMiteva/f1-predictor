# Evaluation notes

The implemented target is a **top-10 finish**, encoded as 1; other results are encoded as 0. KNN with 15 neighbors predicts this target, and its positive-class output is reused as a ranking score. It is not a winner classifier or a finishing-position regressor.

The original full notebook stored test accuracy of approximately 0.759 and a training/testing gap of 0.023. After fixing a missing early NumPy import and portable data paths, the repository validation run produced training accuracy 0.780 and test accuracy 0.768. The run used pandas 2.2.3 and scikit-learn 1.5.2. The app separately produced test accuracy 0.774 in that environment. Its time parsing and fallback logic differ from the notebook. The original application dependency pins are retained, and exact results may vary by environment. These numbers are different experiments, not interchangeable scores.

## Why the top-three diagnostic is limited

The code splits individual driver-race rows. It groups only the held-out rows by Grand Prix/date, ranks up to three drivers within each group, and counts success if the actual winner is included. Groups without the winner are omitted. Many groups contain only a few held-out drivers, so this is easier than choosing three names from a complete starting grid. The recorded 0.917 therefore should not be advertised as 91.7% real-world podium or winner accuracy.

## Other limitations

- Drivers from the same race can appear in training and testing; this is not an independent future-race test.
- The Q3 median is computed before splitting. A future version should fit imputation on training data only.
- The candidate list is entered by the user, and equal scores can affect ordering.
- The latest stored driver/team association is historical and may be outdated.
- Weather, strategy, reliability and several race-day factors are not included.
- A small training/testing gap alone does not establish reliable generalization.

The repository preserves the original learning experiment rather than silently replacing it. These notes distinguish the evidence from the longer-term product idea. Recommended next steps are chronological, race-grouped splits, full-grid ranking evaluation, baselines and better-documented source coverage.
