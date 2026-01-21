package com.company.ueba.service.auth;

import com.company.ueba.model.User;
import org.springframework.stereotype.Service;

@Service
public class LoginValidationService {

    private static final String OFFICIAL_DOMAIN = "@company.com";

    public boolean isValidOfficeEmail(User user) {
        return user.getEmail().endsWith(OFFICIAL_DOMAIN);
    }
}
