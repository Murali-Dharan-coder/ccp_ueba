package com.company.ueba.controller;

import com.company.ueba.model.User;
import com.company.ueba.service.access.AccessControlService;
import com.company.ueba.service.access.SensitiveAccessMonitorService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/access")
public class AccessController {

    private final AccessControlService accessControlService;
    private final SensitiveAccessMonitorService sensitiveAccessMonitorService;

    public AccessController(AccessControlService accessControlService,
                            SensitiveAccessMonitorService sensitiveAccessMonitorService) {
        this.accessControlService = accessControlService;
        this.sensitiveAccessMonitorService = sensitiveAccessMonitorService;
    }

    @PostMapping("/resource")
    public ResponseEntity<String> accessResource(
            @RequestBody User user,
            @RequestHeader("X-RESOURCE") String resource
    ) {

        /* 🔐 Rule #9: Role-Based Access Control */
        boolean allowed = accessControlService.isAccessAllowed(
                user.getRole(), resource
        );

        if (!allowed) {
            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Access denied for role " + user.getRole());
        }

        /* 🔐 Rule #10: Repeated Sensitive Data Access */
        if (sensitiveAccessMonitorService.isSensitiveResource(resource)) {

            boolean withinLimit = sensitiveAccessMonitorService.recordAccess(
                    user.getUserId()
            );

            if (!withinLimit) {
                return ResponseEntity
                        .status(HttpStatus.FORBIDDEN)
                        .body("BLOCKED: Repeated access to sensitive data detected");
            }
        }

        return ResponseEntity.ok(
                "ACCESS GRANTED to " + resource
        );
    }
}
