package com.company.ueba.service.risk;

import com.company.ueba.model.RiskScore;
import org.springframework.stereotype.Service;

@Service
public class RiskScoringService {

    public RiskScore calculateRisk(
            boolean personalEmail,
            boolean invalidIp,
            boolean publicWifi,
            boolean bruteForce,
            boolean sensitiveDataAbuse,
            boolean systemTampering,
            boolean postResignationActivity,
            boolean mlAnomaly
    ) {

        int score = 0;

        if (personalEmail) score += 30;
        if (invalidIp) score += 20;
        if (publicWifi) score += 15;
        if (bruteForce) score += 25;
        if (sensitiveDataAbuse) score += 30;
        if (systemTampering) score += 40;
        if (postResignationActivity) score += 50;
        if (mlAnomaly) score += 40;

        String level;
        if (score >= 80) {
            level = "HIGH";
        } else if (score >= 40) {
            level = "MEDIUM";
        } else {
            level = "LOW";
        }

        return new RiskScore(score, level);
    }
}
