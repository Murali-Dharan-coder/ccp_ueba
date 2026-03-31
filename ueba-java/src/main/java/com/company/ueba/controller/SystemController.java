package com.company.ueba.controller;

import com.company.ueba.model.User;
import com.company.ueba.service.alert.AlertService;
import com.company.ueba.service.system.LogIntegrityService;
import com.company.ueba.service.system.SystemSecurityService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@CrossOrigin(origins = "*")
@RequestMapping("/system")
public class SystemController {

    private final SystemSecurityService systemSecurityService;
    private final LogIntegrityService logIntegrityService;
    private final AlertService alertService;

    public SystemController(SystemSecurityService systemSecurityService,
                            LogIntegrityService logIntegrityService,
                            AlertService alertService) {
        this.systemSecurityService = systemSecurityService;
        this.logIntegrityService = logIntegrityService;
        this.alertService = alertService;
    }

    @PostMapping("/action")
    public ResponseEntity<String> performSystemAction(
            @RequestBody User user,
            @RequestHeader("X-ACTION") String action
    ) {

        // 🔐 Rule #11: Unauthorized Security Configuration Change
        if (systemSecurityService.isSensitiveAction(action)
                && !systemSecurityService.isAllowedToPerform(user.getRole())) {

            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Unauthorized system security change detected");
        }

        // 🧹 Rule #12: Log Clearing / Tampering Detection
        if (logIntegrityService.isLogClearingAttempt(action)) {

            boolean allowed = logIntegrityService.recordLogClearAttempt(
                    user.getUserId()
            );

            if (!allowed) {

                alertService.raiseAlert(
                        user.getUserId(),
                        "SYSTEM TAMPERING: Log clearing attempt",
                        "HIGH"
                );

                return ResponseEntity
                        .status(HttpStatus.FORBIDDEN)
                        .body("BLOCKED: Log tampering detected");
            }
        }

        return ResponseEntity.ok(
                "SYSTEM ACTION PERFORMED: " + action
        );
    }
}
