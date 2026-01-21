package com.company.ueba.model;

import java.time.LocalDateTime;

public class SecurityAlert {

    private String userId;
    private String message;
    private String severity;
    private LocalDateTime time;

    public SecurityAlert(String userId, String message, String severity) {
        this.userId = userId;
        this.message = message;
        this.severity = severity;
        this.time = LocalDateTime.now();
    }

    public String getUserId() { return userId; }
    public String getMessage() { return message; }
    public String getSeverity() { return severity; }
    public LocalDateTime getTime() { return time; }
}
