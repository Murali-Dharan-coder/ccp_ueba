package com.company.ueba.model;

import java.time.LocalDateTime;

/*
 * Represents network activity by a user
 */
public class NetworkEvent {

    private String userId;
    private String url;
    private int dataUsageMb;
    private LocalDateTime timestamp;

    public NetworkEvent(String userId, String url, int dataUsageMb) {
        this.userId = userId;
        this.url = url;
        this.dataUsageMb = dataUsageMb;
        this.timestamp = LocalDateTime.now();
    }

    public String getUserId() { return userId; }
    public String getUrl() { return url; }
    public int getDataUsageMb() { return dataUsageMb; }
    public LocalDateTime getTimestamp() { return timestamp; }
}
