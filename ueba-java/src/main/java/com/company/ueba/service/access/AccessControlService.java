package com.company.ueba.service.access;

import org.springframework.stereotype.Service;

@Service
public class AccessControlService {

    public boolean isAccessAllowed(String role, String resource) {

        if (role == null || resource == null) {
            return false;
        }

        // STUDENT permissions
        if (role.equalsIgnoreCase("STUDENT")) {
            return resource.equals("/marks");
        }

        // STAFF permissions
        if (role.equalsIgnoreCase("STAFF")) {
            return resource.equals("/marks");
        }

        // ADMIN permissions
        if (role.equalsIgnoreCase("ADMIN")) {
            return true; // admin can access all
        }

        return false;
    }
}
