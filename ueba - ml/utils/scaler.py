import numpy as np
from sklearn.preprocessing import StandardScaler

class FeatureScaler:
    """
    Scales UEBA feature vectors for ML models.
    """

    def __init__(self):
        self.scaler = StandardScaler()

    def fit(self, X):
        self.scaler.fit(X)

    def transform(self, X):
        return self.scaler.transform(X)

    def fit_transform(self, X):
        return self.scaler.fit_transform(X)
