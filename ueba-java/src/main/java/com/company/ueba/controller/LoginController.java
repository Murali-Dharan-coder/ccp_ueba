package com.company.ueba.controller;

import com.company.ueba.model.User;
import com.company.ueba.service.alert.AlertService;
import com.company.ueba.service.auth.FailedLoginService;
import com.company.ueba.service.auth.LoginValidationService;
import com.company.ueba.service.network.WifiDetectionService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@CrossOrigin(origins = "*")
@RestController
@RequestMapping("/login")
public class LoginController {

    private final LoginValidationService loginValidationService;
    private final FailedLoginService failedLoginService;
    private final WifiDetectionService wifiDetectionService;
    private final AlertService alertService;

    public LoginController(LoginValidationService loginValidationService,
                           FailedLoginService failedLoginService,
                           WifiDetectionService wifiDetectionService,
                           AlertService alertService) {
        this.loginValidationService = loginValidationService;
        this.failedLoginService = failedLoginService;
        this.wifiDetectionService = wifiDetectionService;
        this.alertService = alertService;
    }

    @PostMapping
    public ResponseEntity<String> login(
            @RequestBody User user,
            @RequestParam(defaultValue = "false") boolean success,
            @RequestHeader("X-WIFI-SECURITY") String wifiSecurity,
            @RequestHeader("X-CLIENT-IP") String clientIp,
            @RequestHeader("X-LOCATION") String location
    ) {

        if (wifiDetectionService.isInsecureWifi(wifiSecurity)) {
            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Unsecured Wi-Fi network detected");
        }

        if (!loginValidationService.isValidOfficeEmail(user)) {

            alertService.raiseAlert(
                    user.getUserId(),
                    "LOGIN POLICY VIOLATION: Personal email used",
                    "MEDIUM"
            );

            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Personal email login detected");
        }

        boolean allowed = failedLoginService.recordLoginAttempt(
                user.getUserId(), success
        );

        if (!allowed) {

            alertService.raiseAlert(
                    user.getUserId(),
                    "AUTHENTICATION ANOMALY: Multiple failed logins",
                    "HIGH"
            );

            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Multiple failed login attempts detected");
        }

        return ResponseEntity.ok("LOGIN SUCCESS");
    }
}
