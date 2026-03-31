package com.company.ueba.service.access;

import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class SensitiveAccessMonitorService {

    private static final int MAX_SENSITIVE_ACCESS = 5;

    private final Map<String, Integer> accessCount = new ConcurrentHashMap<>();

    public boolean isSensitiveResource(String resource) {

        // ❗ ONLY THESE ARE SENSITIVE
        return resource.equals("/admin_panel");
    }

    public boolean recordAccess(String userId) {

        int count = accessCount.getOrDefault(userId, 0) + 1;
        accessCount.put(userId, count);

        return count <= MAX_SENSITIVE_ACCESS;
    }
}
