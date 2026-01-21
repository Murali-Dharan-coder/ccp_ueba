package com.company.ueba.service.insider;

import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Service
public class PostResignationActivityService {

    // Threshold for activity after resignation
    private static final int MAX_ALLOWED_ACTIVITY = 5;

    // userId → activity count
    private final Map<String, Integer> activityCounter = new HashMap<>();

    public boolean recordActivity(String userId) {

        int count = activityCounter.getOrDefault(userId, 0) + 1;
        activityCounter.put(userId, count);

        System.out.println("Post-resignation activity for " + userId + ": " + count);

        return count <= MAX_ALLOWED_ACTIVITY;
    }

    public int getActivityCount(String userId) {
        return activityCounter.getOrDefault(userId, 0);
    }
}
