package com.company.ueba.service.ml;

import org.springframework.stereotype.Service;

@Service
public class MLAnomalyService {

    // Simulated ML output (Isolation Forest)
    public boolean isAnomalous(
            int failedLogins,
            int dataUsageMb,
            boolean locationChange
    ) {
        return failedLogins >= 5 || dataUsageMb > 100 || locationChange;
    }
}
