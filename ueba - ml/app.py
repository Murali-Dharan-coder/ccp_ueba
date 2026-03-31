from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
import numpy as np
import os

app = FastAPI(title="UEBA ML Service")

# Load model and scaler
MODEL_PATH = "model/ueba_model.pkl"

if not os.path.exists(MODEL_PATH):
    raise RuntimeError(f"Model file not found at {MODEL_PATH}. Please run train.py first.")

with open(MODEL_PATH, "rb") as f:
    data = pickle.load(f)
    model = data["model"]
    scaler = data["scaler"]

class UserFeatures(BaseModel):
    failed_logins: int
    location_change: int
    public_wifi: int
    data_usage_mb: float
    sensitive_access: int

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_version": "1.0.0"}

@app.post("/predict")
def predict_anomaly(features: UserFeatures):
    try:
        # Prepare features for the model
        X = np.array([[
            features.failed_logins,
            features.location_change,
            features.public_wifi,
            features.data_usage_mb,
            features.sensitive_access
        ]])
        
        # Scale features
        X_scaled = scaler.transform(X)
        
        # Predict anomaly (-1 for anomaly, 1 for normal)
        prediction = model.predict(X_scaled)[0]
        
        # Calculate decision function (lower is more anomalous)
        score = model.decision_function(X_scaled)[0]
        
        # Convert decision function to a 0-100 risk score
        # Isolation Forest decision_function ranges roughly from -0.5 to 0.5
        # We want to map it so that higher risk score (80+) means anomaly
        risk_score = 100 * (0.5 - score) # Rough mapping
        risk_score = max(0, min(100, risk_score))
        
        return {
            "is_anomaly": bool(prediction == -1),
            "anomaly_score": float(risk_score),
            "raw_decision": float(score)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
