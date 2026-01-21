package com.company.ueba.service.alert;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
public class AlertService {

    public static class Alert {
        private String userId;
        private String type;
        private String severity;
        private String description;
        private LocalDateTime time;

        public Alert(String userId, String type,
                     String severity, String description) {
            this.userId = userId;
            this.type = type;
            this.severity = severity;
            this.description = description;
            this.time = LocalDateTime.now();
        }

        public String getUserId() { return userId; }
        public String getType() { return type; }
        public String getSeverity() { return severity; }
        public String getDescription() { return description; }
        public LocalDateTime getTime() { return time; }
    }

    private final List<Alert> alerts = new ArrayList<>();

    public void addAlert(String userId,
                         String type,
                         String severity,
                         String description) {

        alerts.add(new Alert(userId, type, severity, description));
    }

    public List<Alert> getAllAlerts() {
        return alerts;
    }

    public List<Alert> getAlertsByUser(String userId) {
        return alerts.stream()
                .filter(a -> a.getUserId().equals(userId))
                .toList();
    }
}
