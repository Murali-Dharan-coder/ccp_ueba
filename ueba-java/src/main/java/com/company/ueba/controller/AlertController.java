package com.company.ueba.controller;

import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@CrossOrigin(origins = "*")
@RequestMapping("/alerts")
public class AlertController {

    @GetMapping
    public List<String> getAlerts() {
        return List.of(
                "Suspicious login detected",
                "Multiple failed login attempts"
        );
    }
}
