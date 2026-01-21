package com.company.ueba.service.network;

import org.springframework.stereotype.Service;

import java.util.Set;

@Service
public class WifiDetectionService {

    // Known public Wi-Fi names (demo list)
    private static final Set<String> PUBLIC_WIFI_NAMES = Set.of(
            "Public_WiFi",
            "Free_WiFi",
            "Railway_WiFi",
            "Airport_Free_WiFi",
            "Cafe_WiFi"
    );

    public boolean isPublicWifi(String wifiName) {
        if (wifiName == null || wifiName.isEmpty()) {
            return false; // assume wired / unknown is safe for demo
        }
        return PUBLIC_WIFI_NAMES.contains(wifiName);
    }
}
