from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

from .features import FEATURE_NAMES, host_features, friendly_name, parse_host

MODEL_DIR = Path(__file__).resolve().parent.parent / 'models'
DEFAULT_THRESHOLD = 0.5


class Detector:
    def __init__(self, model_dir=MODEL_DIR, threshold=None):
        model_dir = Path(model_dir)
        self.booster = xgb.Booster()
        self.booster.load_model(str(model_dir / 'qrshield_xgb.json'))
        self.ngram = joblib.load(model_dir / 'qrshield_ngram.joblib')
        saved = self.booster.attr('threshold')
        self.threshold = threshold if threshold is not None else float(saved) if saved else DEFAULT_THRESHOLD

    def reasons(self, row, matrix, top):
        contribs = self.booster.predict(matrix, pred_contribs=True)[0][:-1]
        found = []
        for i in np.argsort(contribs)[::-1]:
            if contribs[i] <= 0 or len(found) == top:
                break
            name = FEATURE_NAMES[i]
            if name.startswith('tld_') and row.iloc[0, i] == 0:
                continue
            text = friendly_name(name, None)
            if text not in found:
                found.append(text)
        return found

    def check(self, url, top=3):
        host = parse_host(url)
        row = pd.DataFrame([host_features(url)], columns=FEATURE_NAMES)
        matrix = xgb.DMatrix(row)
        risk_features = float(self.booster.predict(matrix)[0])
        risk_text = float(self.ngram.predict_proba([host])[0, 1])
        risk = (risk_features + risk_text) / 2
        return {
            'url': url,
            'host': host,
            'risk': risk,
            'verdict': 'PHISHING' if risk >= self.threshold else 'SAFE',
            'reasons': self.reasons(row, matrix, top) if risk >= self.threshold else [],
        }
