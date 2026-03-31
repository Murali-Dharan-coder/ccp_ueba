import numpy as np
import pickle
from utils.logger import log

# Load trained model
with open("model/ueba_model.pkl", "rb") as f:
    saved_objects = pickle.load(f)

model = saved_objects["model"]
scaler = saved_objects["scaler"]

# Example UEBA feature vector
# [failed_logins, location_change, public_wifi, data_usage_mb, sensitive_access]
new_event = np.array([
    [0, 0, 0, 15, 1]
])

# Scale input
new_event_scaled = scaler.transform(new_event)

# Predict anomaly
prediction = model.predict(new_event_scaled)

if prediction[0] == -1:
    log("ANOMALY DETECTED: Suspicious user behavior")
else:
    log("NORMAL BEHAVIOR")
