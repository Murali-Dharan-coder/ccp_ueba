package com.company.ueba.model;

public class RiskScore {

    private int score;
    private String level;

    public RiskScore(int score, String level) {
        this.score = score;
        this.level = level;
    }

    public int getScore() {
        return score;
    }

    public String getLevel() {
        return level;
    }
}
