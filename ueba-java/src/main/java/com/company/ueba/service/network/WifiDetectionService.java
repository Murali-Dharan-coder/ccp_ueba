package com.company.ueba.service.network;

import org.springframework.stereotype.Service;

import java.util.Set;

@Service
public class WifiDetectionService {

    // Insecure Wi-Fi security types
    private static final Set<String> INSECURE_WIFI_TYPES = Set.of(
            "OPEN"  ,   // No password
            "WEP"       // Weak encryption
    );

    /**
     * Returns true if Wi-Fi is insecure (open or weak encryption)
     */
    public boolean isInsecureWifi(String wifiSecurityType) {

        if (wifiSecurityType == null || wifiSecurityType.isEmpty()) {
            // Unknown security → treat as risky
            return true;
        }

        return INSECURE_WIFI_TYPES.contains(
                wifiSecurityType.toUpperCase()
        );
    }
}
