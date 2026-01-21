package com.company.ueba.service.access;

import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.Set;

@Service
public class AccessControlService {

    // Role → allowed resources mapping
    private static final Map<String, Set<String>> ROLE_ACCESS_MAP = Map.of(
            "STUDENT", Set.of("/notes", "/assignments"),
            "STAFF", Set.of("/notes", "/assignments", "/marks"),
            "ADMIN", Set.of("*") // wildcard = all access
    );

    public boolean isAccessAllowed(String role, String resource) {

        if (role == null || resource == null) {
            return false;
        }

        Set<String> allowedResources = ROLE_ACCESS_MAP.get(role.toUpperCase());

        if (allowedResources == null) {
            return false;
        }

        // Admin wildcard access
        if (allowedResources.contains("*")) {
            return true;
        }

        return allowedResources.contains(resource);
    }
}
