package com.company.ueba.service.network;

import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Service
public class LocationDetectionService {

    // Stores last known location per user
    private final Map<String, String> userLastLocation = new HashMap<>();

    public boolean isSuspiciousLocation(String userId, String location) {

        if (!userLastLocation.containsKey(userId)) {
            userLastLocation.put(userId, location);
            return false;
        }

        String previousLocation = userLastLocation.get(userId);

        if (!previousLocation.equals(location)) {
            userLastLocation.put(userId, location);
            return true; // sudden location change
        }

        return false;
    }
}
