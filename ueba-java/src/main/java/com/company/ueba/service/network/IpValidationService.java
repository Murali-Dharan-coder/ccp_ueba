package com.company.ueba.service.network;

import org.springframework.stereotype.Service;

@Service
public class IpValidationService {

    // Check if IP belongs to private/internal network
    public boolean isValidIp(String ipAddress) {

        if (ipAddress == null || ipAddress.isEmpty()) {
            return false;
        }

        return ipAddress.startsWith("192.168.")
                || ipAddress.startsWith("10.");
    }
}
