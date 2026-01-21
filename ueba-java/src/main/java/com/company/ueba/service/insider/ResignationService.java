package com.company.ueba.service.insider;

import org.springframework.stereotype.Service;

import java.util.HashSet;
import java.util.Set;

@Service
public class ResignationService {

    private final Set<String> resignedUsers = new HashSet<>();

    public void markResigned(String userId) {
        resignedUsers.add(userId);
    }

    public boolean isResignedUser(String userId) {
        return resignedUsers.contains(userId);
    }
}
