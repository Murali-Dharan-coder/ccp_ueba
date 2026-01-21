package com.company.ueba.controller;

import com.company.ueba.service.network.WebsiteBlockingService;
import com.company.ueba.service.usage.DataUsageMonitorService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/network")
public class NetworkController {

    private final WebsiteBlockingService websiteBlockingService;
    private final DataUsageMonitorService dataUsageMonitorService;

    public NetworkController(WebsiteBlockingService websiteBlockingService,
                             DataUsageMonitorService dataUsageMonitorService) {
        this.websiteBlockingService = websiteBlockingService;
        this.dataUsageMonitorService = dataUsageMonitorService;
    }

    @PostMapping("/access")
    public ResponseEntity<String> checkNetworkAccess(
            @RequestHeader(value = "X-REQUESTED-URL", required = false) String requestedUrl,
            @RequestHeader(value = "X-DATA-USAGE-MB", defaultValue = "0") int dataUsageMb
    ) {

        // Rule #5: Website Blocking
        if (websiteBlockingService.isBlockedWebsite(requestedUrl)) {
            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Access to restricted website");
        }

        // Rule #6: Data Usage Limit
        if (!dataUsageMonitorService.isDataUsageAllowed(dataUsageMb)) {
            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Data usage exceeded allowed limit");
        }

        return ResponseEntity.ok("NETWORK ACCESS ALLOWED");
    }
}
