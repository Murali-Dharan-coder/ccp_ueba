package com.company.ueba.service.network;

import org.springframework.stereotype.Service;

import java.util.Set;

@Service
public class WebsiteBlockingService {

    // Demo list of blocked websites
    private static final Set<String> BLOCKED_DOMAINS = Set.of(
            "facebook.com",
            "instagram.com",
            "youtube.com",
            "netflix.com",
            "torrent",
            "pirate"
    );

    public boolean isBlockedWebsite(String requestedUrl) {

        if (requestedUrl == null || requestedUrl.isEmpty()) {
            return false;
        }

        String lowerUrl = requestedUrl.toLowerCase();

        return BLOCKED_DOMAINS.stream()
                .anyMatch(lowerUrl::contains);
    }
}
