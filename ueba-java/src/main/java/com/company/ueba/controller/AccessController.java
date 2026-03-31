package com.company.ueba.controller;

import com.company.ueba.model.User;
import com.company.ueba.service.access.AccessControlService;
import com.company.ueba.service.access.SensitiveAccessMonitorService;
import com.company.ueba.service.alert.AlertService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@CrossOrigin(origins = "*")   // ✅ ADD THIS
@RestController
@RequestMapping("/access")
public class AccessController {

    private final AccessControlService accessControlService;
    private final SensitiveAccessMonitorService sensitiveAccessMonitorService;

   private final AlertService alertService;

public AccessController(AccessControlService accessControlService,
                        SensitiveAccessMonitorService sensitiveAccessMonitorService,
                        AlertService alertService) {
    this.accessControlService = accessControlService;
    this.sensitiveAccessMonitorService = sensitiveAccessMonitorService;
    this.alertService = alertService;
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

    alertService.raiseAlert(
            user.getUserId(),
            "RBAC VIOLATION: Unauthorized resource access",
            "HIGH"
    );

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

    alertService.raiseAlert(
            user.getUserId(),
            "SENSITIVE DATA ABUSE",
            "HIGH"
    );

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
