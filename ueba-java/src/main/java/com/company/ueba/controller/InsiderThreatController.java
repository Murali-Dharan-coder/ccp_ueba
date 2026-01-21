package com.company.ueba.controller;

import com.company.ueba.model.User;
import com.company.ueba.service.insider.PostResignationActivityService;
import com.company.ueba.service.insider.ResignationService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/insider")
public class InsiderThreatController {

    private final ResignationService resignationService;
    private final PostResignationActivityService postResignationActivityService;

    public InsiderThreatController(ResignationService resignationService,
                                   PostResignationActivityService postResignationActivityService) {
        this.resignationService = resignationService;
        this.postResignationActivityService = postResignationActivityService;
    }

    /* Endpoint to mark resignation */
    @PostMapping("/resign")
    public ResponseEntity<String> resign(@RequestBody User user) {

        resignationService.markResigned(user.getUserId());

        return ResponseEntity.ok(
                "User marked as resigned: " + user.getUserId()
        );
    }

    /* Rule #13: Monitor post-resignation activity */
    @PostMapping("/activity")
    public ResponseEntity<String> recordActivity(@RequestBody User user) {

        if (resignationService.isResignedUser(user.getUserId())) {

            boolean allowed = postResignationActivityService.recordActivity(
                    user.getUserId()
            );

            if (!allowed) {
                return ResponseEntity
                        .status(HttpStatus.FORBIDDEN)
                        .body("BLOCKED: Abnormal activity detected after resignation");
            }
        }

        return ResponseEntity.ok(
                "ACTIVITY RECORDED"
        );
    }
}
