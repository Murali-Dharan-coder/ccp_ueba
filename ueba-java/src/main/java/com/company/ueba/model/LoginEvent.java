package com.company.ueba.model;

import java.time.LocalDateTime;

public class LoginEvent {

    private String userId;
    private boolean success;
    private LocalDateTime time;

    public LoginEvent(String userId, boolean success) {
        this.userId = userId;
        this.success = success;
        this.time = LocalDateTime.now();
    }

    public String getUserId() {
        return userId;
    }

    public boolean isSuccess() {
        return success;
    }

    public LocalDateTime getTime() {
        return time;
    }
}
