package com.company.ueba.service.usage;

import org.springframework.stereotype.Service;

@Service
public class DataUsageMonitorService {

    // Max allowed data per request/session (in MB) — demo value
    private static final int MAX_ALLOWED_MB = 500000;

    public boolean isDataUsageAllowed(int dataUsedMb) {
        return dataUsedMb <= MAX_ALLOWED_MB;
    }

    public int getMaxAllowedMb() {
        return MAX_ALLOWED_MB;
    }
}
