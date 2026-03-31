package com.company.ueba.controller;

import com.company.ueba.model.SecurityAlert;
import com.company.ueba.service.alert.AlertService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@CrossOrigin(origins = "*")
@RestController
@RequestMapping("/admin/soc")
public class AdminSocController {

    private final AlertService alertService;

    public AdminSocController(AlertService alertService) {
        this.alertService = alertService;
    }

    @GetMapping("/alerts")
    public List<SecurityAlert> getAlerts() {
        return alertService.getAllAlerts();
    }
}
