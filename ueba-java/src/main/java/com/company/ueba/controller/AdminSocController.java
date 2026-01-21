
package com.company.ueba.controller;

import com.company.ueba.model.RiskScore;
import com.company.ueba.service.alert.AlertService;
import com.company.ueba.service.risk.RiskScoringService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/admin/soc")
public class AdminSocController {

    private final AlertService alertService;
    private final RiskScoringService riskScoringService;

    public AdminSocController(AlertService alertService,
                              RiskScoringService riskScoringService) {
        this.alertService = alertService;
        this.riskScoringService = riskScoringService;
    }

    /* 🔍 View ALL security alerts */
    @GetMapping("/alerts")
    public ResponseEntity<List<AlertService.Alert>> getAllAlerts() {
        return ResponseEntity.ok(alertService.getAllAlerts());
    }

    /* 🔍 View alerts for specific user */
    @GetMapping("/alerts/{userId}")
    public ResponseEntity<List<AlertService.Alert>> getAlertsByUser(
            @PathVariable String userId) {
        return ResponseEntity.ok(alertService.getAlertsByUser(userId));
    }

    /* 📊 View risk level (manual aggregation demo) */
    @GetMapping("/risk-summary")
    public ResponseEntity<RiskScore> getRiskSummary(
            @RequestParam(defaultValue = "false") boolean personalEmail,
            @RequestParam(defaultValue = "false") boolean invalidIp,
            @RequestParam(defaultValue = "false") boolean publicWifi,
            @RequestParam(defaultValue = "false") boolean bruteForce,
            @RequestParam(defaultValue = "false") boolean sensitiveDataAbuse,
            @RequestParam(defaultValue = "false") boolean systemTampering,
            @RequestParam(defaultValue = "false") boolean postResignationActivity,
            @RequestParam(defaultValue = "false") boolean mlAnomaly
    ) {

        RiskScore riskScore = riskScoringService.calculateRisk(
                personalEmail,
                invalidIp,
                publicWifi,
                bruteForce,
                sensitiveDataAbuse,
                systemTampering,
                postResignationActivity,
                mlAnomaly
        );

        return ResponseEntity.ok(riskScore);
    }
}
