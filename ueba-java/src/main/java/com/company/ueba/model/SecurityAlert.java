package com.company.ueba.model;

import java.time.LocalDateTime;

public class SecurityAlert {

    private String userId;
    private String type;
    private String severity;
    private LocalDateTime time;

    public SecurityAlert(String userId, String type, String severity) {
        this.userId = userId;
        this.type = type;
        this.severity = severity;
        this.time = LocalDateTime.now();
    }

    public String getUserId() {
        return userId;
    }

    public String getType() {
        return type;
    }

    public String getSeverity() {
        return severity;
    }

    public LocalDateTime getTime() {
        return time;
    }
}
