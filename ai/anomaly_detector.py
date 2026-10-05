"""Isolation Forest trained ONLY on normal behavior: outliers are isolated in fewer random splits."""
import numpy as np
from sklearn.ensemble import IsolationForest
from .twin_model import features

class TwinDetector:
    def __init__(self, baseline, normal_df):
        self.b = baseline
        X = np.array([features(r, baseline) for r in normal_df.to_dict("records")])
        self.model = IsolationForest(n_estimators=200, contamination=0.02, random_state=42).fit(X)
        raw = -self.model.score_samples(X)  # higher = more abnormal
        # Calibrate: median training sample -> 0, just beyond the worst training sample -> 100
        self.lo = float(np.percentile(raw, 50))
        self.hi = float(np.percentile(raw, 99.5)) + 0.12

    def score(self, e):
        """Anomaly score 0-100 for one event."""
        raw = -self.model.score_samples(np.array([features(e, self.b)]))[0]
        return float(np.clip((raw - self.lo) / (self.hi - self.lo), 0, 1) * 100)
