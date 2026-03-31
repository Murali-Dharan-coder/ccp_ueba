def build_feature_vector(
        failed_logins,
        location_change,
        public_wifi,
        data_usage_mb,
        sensitive_access_count):

    return [
        failed_logins,
        int(location_change),
        int(public_wifi),
        data_usage_mb,
        sensitive_access_count
    ]
