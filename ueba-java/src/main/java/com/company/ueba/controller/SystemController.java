package com.company.ueba.controller;

import com.company.ueba.model.User;
import com.company.ueba.service.system.LogIntegrityService;
import com.company.ueba.service.system.SystemSecurityService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/system")
public class SystemController {

    private final SystemSecurityService systemSecurityService;
    private final LogIntegrityService logIntegrityService;

    public SystemController(SystemSecurityService systemSecurityService,
                            LogIntegrityService logIntegrityService) {
        this.systemSecurityService = systemSecurityService;
        this.logIntegrityService = logIntegrityService;
    }

    @PostMapping("/action")
    public ResponseEntity<String> performSystemAction(
            @RequestBody User user,
            @RequestHeader("X-ACTION") String action
    ) {

        /* 🔐 Rule #11: Unauthorized Security Configuration Change */
        if (systemSecurityService.isSensitiveAction(action)
                && !systemSecurityService.isAllowedToPerform(user.getRole())) {

            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Unauthorized system security change detected");
        }

        /* 🧹 Rule #12: Log Clearing / Tampering Detection */
        if (logIntegrityService.isLogClearingAttempt(action)) {

            boolean allowed = logIntegrityService.recordLogClearAttempt(
                    user.getUserId()
            );

            if (!allowed) {
                return ResponseEntity
                        .status(HttpStatus.FORBIDDEN)
                        .body("BLOCKED: Repeated log clearing activity detected");
            }
        }

        return ResponseEntity.ok(
                "SYSTEM ACTION PERFORMED: " + action
        );
    }
}
