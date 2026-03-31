package com.company.ueba.service.alert;

import com.company.ueba.model.SecurityAlert;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class AlertService {

    private final List<SecurityAlert> alerts = new ArrayList<>();

    public void raiseAlert(String userId, String type, String severity) {
        alerts.add(new SecurityAlert(userId, type, severity));
    }

    public List<SecurityAlert> getAllAlerts() {
        return alerts;
    }
}
