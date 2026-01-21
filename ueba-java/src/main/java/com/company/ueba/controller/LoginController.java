package com.company.ueba.controller;

import com.company.ueba.model.User;
import com.company.ueba.service.auth.FailedLoginService;
import com.company.ueba.service.auth.LoginValidationService;
import com.company.ueba.service.network.IpValidationService;
import com.company.ueba.service.network.LocationDetectionService;
import com.company.ueba.service.network.WifiDetectionService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/login")
public class LoginController {

    private final LoginValidationService loginValidationService;
    private final FailedLoginService failedLoginService;
    private final IpValidationService ipValidationService;
    private final WifiDetectionService wifiDetectionService;
    private final LocationDetectionService locationDetectionService;

    public LoginController(LoginValidationService loginValidationService,
                           FailedLoginService failedLoginService,
                           IpValidationService ipValidationService,
                           WifiDetectionService wifiDetectionService,
                           LocationDetectionService locationDetectionService) {
        this.loginValidationService = loginValidationService;
        this.failedLoginService = failedLoginService;
        this.ipValidationService = ipValidationService;
        this.wifiDetectionService = wifiDetectionService;
        this.locationDetectionService = locationDetectionService;
    }

    @PostMapping
    public ResponseEntity<String> login(
            @RequestBody User user,
            @RequestParam(defaultValue = "false") boolean success,
            @RequestHeader(value = "X-Client-IP", required = false) String ipAddress,
            @RequestHeader(value = "X-WIFI-NAME", required = false) String wifiName,
            @RequestHeader(value = "X-LOCATION", required = false) String location
    ) {

        /* 🔐 Rule #4: Public Wi-Fi Blocking */
        if (wifiDetectionService.isPublicWifi(wifiName)) {
            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Login from public Wi-Fi is not allowed");
        }

        /* 🔐 Rule #3: Invalid IP Detection */
        if (!ipValidationService.isValidIp(ipAddress)) {
            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Invalid or untrusted IP address detected");
        }

        /* 🔐 Rule #8: Location Change Detection */
        if (locationDetectionService.isSuspiciousLocation(
                user.getUserId(), location)) {
            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Suspicious login location detected");
        }

        /* 🔐 Rule #1: Office vs Personal Email */
        if (!loginValidationService.isValidOfficeEmail(user)) {
            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Personal email login detected");
        }

        /* 🔐 Rule #2 & #7: Multiple Failed Login + Alert */
        boolean allowed = failedLoginService.recordLoginAttempt(
                user.getUserId(), success);

        if (!allowed) {
            return ResponseEntity
                    .status(HttpStatus.FORBIDDEN)
                    .body("BLOCKED: Multiple failed login attempts detected");
        }

        /* ✅ Final Login Result */
        if (success) {
            return ResponseEntity.ok("LOGIN SUCCESS");
        } else {
            return ResponseEntity
                    .status(HttpStatus.UNAUTHORIZED)
                    .body("LOGIN FAILED");
        }
    }
}
