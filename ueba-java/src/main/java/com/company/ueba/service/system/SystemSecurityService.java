package com.company.ueba.service.system;

import org.springframework.stereotype.Service;

import java.util.Set;

@Service
public class SystemSecurityService {

    private static final Set<String> SENSITIVE_ACTIONS = Set.of(
            "DISABLE_FIREWALL",
            "CHANGE_SECURITY_POLICY",
            "MODIFY_AUDIT_SETTINGS",
            "TURN_OFF_LOGGING"
    );

    public boolean isSensitiveAction(String action) {
        return SENSITIVE_ACTIONS.contains(action);
    }

    public boolean isAllowedToPerform(String role) {
        return "ADMIN".equalsIgnoreCase(role);
    }
}
