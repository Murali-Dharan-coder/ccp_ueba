package com.company.ueba.service.auth;

import com.company.ueba.model.SecurityAlert;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class FailedLoginService {

    private static final int MAX_FAILED_ATTEMPTS = 5;

    private final Map<String, Integer> failedAttempts = new HashMap<>();
    private final List<SecurityAlert> alerts = new ArrayList<>();

    public boolean recordLoginAttempt(String userId, boolean success) {

        if (success) {
            failedAttempts.remove(userId);
            return true;
        }

        int attempts = failedAttempts.getOrDefault(userId, 0) + 1;
        failedAttempts.put(userId, attempts);

        if (attempts >= MAX_FAILED_ATTEMPTS) {
            alerts.add(new SecurityAlert(
                    userId,
                    "Multiple failed login attempts detected",
                    "HIGH"
            ));
            return false;
        }

        return true;
    }

    public List<SecurityAlert> getAlerts() {
        return alerts;
    }
}
