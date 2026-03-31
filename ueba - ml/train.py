import numpy as np
import pandas as pd
import pickle
from sklearn.ensemble import IsolationForest
from utils.scaler import FeatureScaler
from utils.logger import log

# Load datasets
access_logs = pd.read_csv('../dataset/access_logs.csv')
login_logs = pd.read_csv('../dataset/login_logs.csv')
network_logs = pd.read_csv('../dataset/network_logs.csv')
system_events = pd.read_csv('../dataset/system_events.csv')

# Process features per user
users = pd.concat([access_logs['user_id'], login_logs['user_id'], network_logs['user_id'], system_events['user_id']]).unique()

features_list = []
for user in users:
    # Failed logins
    failed_logins = login_logs[(login_logs['user_id'] == user) & (login_logs['login_success'] == False)].shape[0]
    
    # Location change (simplified: if more than one unique location)
    locations = login_logs[login_logs['user_id'] == user]['location'].unique()
    location_change = 1 if len(locations) > 1 else 0
    
    # Public wifi usage
    public_wifi = 1 if network_logs[(network_logs['user_id'] == user) & (network_logs['wifi_name'].str.contains('Public', na=False))].shape[0] > 0 else 0
    
    # Data usage
    data_usage_mb = network_logs[network_logs['user_id'] == user]['data_usage_mb'].sum()
    
    # Sensitive access (e.g., admin_panel)
    sensitive_access = access_logs[(access_logs['user_id'] == user) & (access_logs['resource_accessed'].str.contains('admin', na=False))].shape[0]
    
    features_list.append([failed_logins, location_change, public_wifi, data_usage_mb, sensitive_access])

X_train = np.array(features_list)

log("Starting UEBA ML training")

# Scale features
scaler = FeatureScaler()
X_scaled = scaler.fit_transform(X_train)

# Train Isolation Forest
model = IsolationForest(
    contamination=0.1,
    random_state=42
)
model.fit(X_scaled)

# Save model + scaler together
with open("model/ueba_model.pkl", "wb") as f:
    pickle.dump({
        "model": model,
        "scaler": scaler
    }, f)

log("UEBA Isolation Forest model trained and saved successfully")
