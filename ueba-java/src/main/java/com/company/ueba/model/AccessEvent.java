package com.company.ueba.model;

import java.time.LocalDateTime;

/*
 * Represents a user accessing a protected resource
 */
public class AccessEvent {

    private String userId;
    private String resource;
    private LocalDateTime timestamp;

    public AccessEvent(String userId, String resource) {
        this.userId = userId;
        this.resource = resource;
        this.timestamp = LocalDateTime.now();
    }

    public String getUserId() { return userId; }
    public String getResource() { return resource; }
    public LocalDateTime getTimestamp() { return timestamp; }
}
