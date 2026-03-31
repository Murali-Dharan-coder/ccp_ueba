package com.company.ueba.controller;

import com.company.ueba.model.RiskScore;
import com.company.ueba.service.ml.MLAnomalyService;
import com.company.ueba.service.risk.RiskScoringService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@CrossOrigin(origins = "*")
@RequestMapping("/risk")
public class RiskController {

    private final RiskScoringService riskScoringService;
    private final MLAnomalyService mlAnomalyService;

    public RiskController(RiskScoringService riskScoringService,
                          MLAnomalyService mlAnomalyService) {
        this.riskScoringService = riskScoringService;
        this.mlAnomalyService = mlAnomalyService;
    }

    @PostMapping("/evaluate")
    public ResponseEntity<RiskScore> evaluateRisk(

            @RequestParam(defaultValue = "false") boolean personalEmail,
            @RequestParam(defaultValue = "false") boolean invalidIp,
            @RequestParam(defaultValue = "false") boolean publicWifi,
            @RequestParam(defaultValue = "false") boolean bruteForce,
            @RequestParam(defaultValue = "false") boolean sensitiveDataAbuse,
            @RequestParam(defaultValue = "false") boolean systemTampering,
            @RequestParam(defaultValue = "false") boolean postResignationActivity,

            @RequestParam(defaultValue = "0") int failedLogins,
            @RequestParam(defaultValue = "0") int dataUsageMb,
            @RequestParam(defaultValue = "false") boolean locationChange
    ) {

        boolean mlAnomaly = mlAnomalyService.isAnomalous(
                failedLogins, dataUsageMb, locationChange
        );

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
