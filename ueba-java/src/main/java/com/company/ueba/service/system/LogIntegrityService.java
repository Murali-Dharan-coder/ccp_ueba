package com.company.ueba.service.system;

import org.springframework.stereotype.Service;

import java.util.HashSet;
import java.util.Set;

@Service
public class LogIntegrityService {

    private final Set<String> usersWhoClearedLogs = new HashSet<>();

    public boolean isLogClearingAttempt(String action) {
        return "CLEAR_LOGS".equalsIgnoreCase(action)
                || "DELETE_LOGS".equalsIgnoreCase(action);
    }

    public boolean recordLogClearAttempt(String userId) {

        if (usersWhoClearedLogs.contains(userId)) {
            return false; // repeated log clearing = suspicious
        }

        usersWhoClearedLogs.add(userId);
        return true;
    }
}
