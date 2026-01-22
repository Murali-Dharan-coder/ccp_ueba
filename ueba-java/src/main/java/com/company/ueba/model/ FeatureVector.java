package com.company.ueba.model;

/*
 * Normalized behavioral features for ML anomaly detection
 * (Used in UEBA analytics module)
 */
public class FeatureVector {

    private String userId;
    private int failedLoginCount;
    private boolean locationChange;
    private boolean publicWifiUsed;
    private int dataUsageMb;
    private int sensitiveAccessCount;

    public FeatureVector(String userId,
                         int failedLoginCount,
                         boolean locationChange,
                         boolean publicWifiUsed,
                         int dataUsageMb,
                         int sensitiveAccessCount) {
        this.userId = userId;
        this.failedLoginCount = failedLoginCount;
        this.locationChange = locationChange;
        this.publicWifiUsed = publicWifiUsed;
        this.dataUsageMb = dataUsageMb;
        this.sensitiveAccessCount = sensitiveAccessCount;
    }

    public String getUserId() { return userId; }
    public int getFailedLoginCount() { return failedLoginCount; }
    public boolean isLocationChange() { return locationChange; }
    public boolean isPublicWifiUsed() { return publicWifiUsed; }
    public int getDataUsageMb() { return dataUsageMb; }
    public int getSensitiveAccessCount() { return sensitiveAccessCount; }
}
