package com.company.ueba.model;

public class User {

    private String userId;
    private String email;
    private String role; // STUDENT, STAFF, ADMIN

    public User() {}

    public User(String userId, String email, String role) {
        this.userId = userId;
        this.email = email;
        this.role = role;
    }

    public String getUserId() {
        return userId;
    }

    public String getEmail() {
        return email;
    }

    public String getRole() {
        return role;
    }
}
