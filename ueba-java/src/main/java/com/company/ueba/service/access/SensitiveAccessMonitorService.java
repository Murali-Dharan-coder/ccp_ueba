package com.company.ueba.service.access;

import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

@Service
public class SensitiveAccessMonitorService {

    private static final int MAX_ALLOWED_ACCESSES = 5;

    private static final Set<String> SENSITIVE_RESOURCES = Set.of(
            "/marks",
            "/confidential",
            "/admin-data"
    );

    // userId → count
    private final Map<String, Integer> accessCount = new HashMap<>();

    public boolean isSensitiveResource(String resource) {
        return SENSITIVE_RESOURCES.contains(resource);
    }

    public boolean recordAccess(String userId) {

        int count = accessCount.getOrDefault(userId, 0) + 1;
        accessCount.put(userId, count);

        System.out.println("User " + userId +
                " sensitive access count: " + count);

        return count <= MAX_ALLOWED_ACCESSES;
    }

    public int getAccessCount(String userId) {
        return accessCount.getOrDefault(userId, 0);
    }
}
