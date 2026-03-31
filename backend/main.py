from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import timedelta
import asyncio
import json
import datetime
import random
import httpx

import models, schemas, auth, database, report
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="UEBA Engine API")
ML_SERVICE_URL = "http://localhost:8001"
ADMIN_PIN = "230806"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# SSE Event Bus — in-memory queue for real-time push to admin portal
# ─────────────────────────────────────────────────────────────────────────────
_sse_subscribers: list[asyncio.Queue] = []

async def push_event(payload: dict):
    """Push a JSON payload to ALL connected SSE clients."""
    msg = f"data: {json.dumps(payload)}\n\n"
    dead = []
    for q in _sse_subscribers:
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _sse_subscribers.remove(q)


# ─────────────────────────────────────────────────────────────────────────────
# UEBA RULE ENGINE  (ported from Java service classes)
# ─────────────────────────────────────────────────────────────────────────────

UEBA_RULES = [
    # ── From FailedLoginService ──────────────────────────────────────────
    {
        "action": "brute_force_login",
        "type": "Brute Force Login",
        "severity": "CRITICAL",
        "score_delta": 28,
        "descriptions": [
            "6 consecutive failed authentication attempts in 90 seconds — account under brute-force attack.",
            "Rapid credential stuffing detected: 8 failed logins from the same subnet.",
            "Threshold exceeded: 5+ failed login attempts triggered lockout protocol."
        ]
    },
    # ── From LocationDetectionService ────────────────────────────────────
    {
        "action": "impossible_travel",
        "type": "Impossible Travel",
        "severity": "HIGH",
        "score_delta": 22,
        "descriptions": [
            "Login registered in Mumbai, India — 12 minutes after session closed in London, UK. Physically impossible.",
            "Geolocation conflict: New York (09:14 UTC) → Tokyo (09:51 UTC). Velocity: 14,200 km/h.",
            "Simultaneous session detected from two geographically distant locations."
        ]
    },
    # ── From WifiDetectionService ─────────────────────────────────────────
    {
        "action": "insecure_network",
        "type": "Insecure Network Access",
        "severity": "MEDIUM",
        "score_delta": 14,
        "descriptions": [
            "Corporate credentials used over OPEN Wi-Fi hotspot 'CafeNet_Free' — WEP encryption detected.",
            "Unencrypted network access: employee authenticated from public airport Wi-Fi without VPN.",
            "WEP-secured network detected: session origin violates corporate network policy."
        ]
    },
    # ── From LogIntegrityService ──────────────────────────────────────────
    {
        "action": "log_tampering",
        "type": "Log Tampering",
        "severity": "CRITICAL",
        "score_delta": 35,
        "descriptions": [
            "CLEAR_LOGS action detected in audit trail — 847 security log entries deleted.",
            "System log integrity check FAILED — DELETE_LOGS called on SIEM integration tables.",
            "Anti-forensic activity: audit logs wiped 4 minutes before scheduled compliance scan."
        ]
    },
    # ── From SensitiveAccessMonitorService ───────────────────────────────
    {
        "action": "admin_panel_abuse",
        "type": "Sensitive Resource Abuse",
        "severity": "HIGH",
        "score_delta": 20,
        "descriptions": [
            "Admin panel accessed 9 times in 6 minutes — exceeds MAX_SENSITIVE_ACCESS threshold of 5.",
            "Repeated access to /admin_panel endpoint: 7 requests in rapid succession.",
            "Privilege boundary violated: sensitive resource polled 11 times outside authorized window."
        ]
    },
    # ── From DataUsageMonitorService ─────────────────────────────────────
    {
        "action": "data_exfiltration",
        "type": "Data Exfiltration",
        "severity": "CRITICAL",
        "score_delta": 32,
        "descriptions": [
            "4.7 GB uploaded to external S3 bucket in 18 minutes — DLP threshold exceeded.",
            "Bulk download: 312 sensitive files transferred to personal OneDrive outside corporate perimeter.",
            "Anomalous outbound data spike: 2.1 GB egress to unregistered IP — potential data theft."
        ]
    },
    # ── From PostResignationActivityService ──────────────────────────────
    {
        "action": "post_resignation",
        "type": "Post-Resignation Activity",
        "severity": "HIGH",
        "score_delta": 25,
        "descriptions": [
            "Account activity recorded 72 hours after resignation date logged in HR system.",
            "Terminated employee credential used to access internal wiki — post-offboarding breach.",
            "Post-resignation access: 6 resource requests after MAX_ALLOWED_ACTIVITY threshold exceeded."
        ]
    },
    # ── From AccessControlService / off-hours ────────────────────────────
    {
        "action": "off_hours_login",
        "type": "Off-Hours Access",
        "severity": "MEDIUM",
        "score_delta": 12,
        "descriptions": [
            "System login at 02:47 AM — 4.3 standard deviations from this user's baseline activity window.",
            "Weekend access: full admin session initiated Saturday 01:12 AM from unrecognized device.",
            "Night-shift anomaly: user authenticated at 03:30 AM during scheduled maintenance blackout."
        ]
    },
    # ── From RoleAccessService / privilege escalation ────────────────────
    {
        "action": "privilege_escalation",
        "type": "Privilege Escalation",
        "severity": "CRITICAL",
        "score_delta": 30,
        "descriptions": [
            "Non-admin account attempted sudo elevation on production server — rejected, alert raised.",
            "Role modification detected: user self-assigned ADMIN group in LDAP directory.",
            "Unauthorized permission grant: account now has write access to payroll DB without approval."
        ]
    },
    # ── Lateral movement / network anomaly ──────────────────────────────
    {
        "action": "lateral_movement",
        "type": "Lateral Movement",
        "severity": "HIGH",
        "score_delta": 18,
        "descriptions": [
            "SSH pivoting detected: account connected to 14 internal hosts in 8 minutes.",
            "Unusual RDP chain: workstation → file server → domain controller traversed in 3 minutes.",
            "Port scanning from user endpoint: 1,024 ports probed on internal subnet."
        ]
    },
    # ── From LoginValidationService ──────────────────────────────────────
    {
        "action": "suspicious_login",
        "type": "Suspicious Login Pattern",
        "severity": "MEDIUM",
        "score_delta": 15,
        "descriptions": [
            "Login from new device fingerprint — browser agent never seen in 90-day baseline.",
            "Token reuse detected: JWT presented from 3 different IPs within 60 seconds.",
            "Credential forwarding suspected: login from anonymizing proxy (Tor exit node)."
        ]
    },
    # ── From SoftwareScanService ─────────────────────────────────────────
    {
        "action": "unauthorized_software",
        "type": "Unauthorized Software Detected",
        "severity": "MEDIUM",
        "score_delta": 10,
        "descriptions": [
            "Keylogger-class software 'KLog32.exe' detected in running processes — quarantine recommended.",
            "Unapproved remote-access tool 'AnyDesk' installed outside IT provisioning workflow.",
            "Network sniffer 'Wireshark' launched on corporate endpoint — policy violation flagged."
        ]
    },
]

# Map action string → rule dict for fast lookup
ACTION_TO_RULE: dict = {r["action"]: r for r in UEBA_RULES}
ALL_ACTIONS = list(ACTION_TO_RULE.keys())


def apply_ueba_rule(action: str, user: models.User, db: Session) -> dict | None:
    """
    Evaluate one UEBA rule against a user.
    Writes AnomalyRecord to DB, updates user score, commits.
    Returns the anomaly dict, or None if action unknown.
    """
    rule = ACTION_TO_RULE.get(action)
    if not rule:
        return None

    desc = random.choice(rule["descriptions"])
    now = datetime.datetime.now()

    record = models.AnomalyRecord(
        user_id=user.id,
        type=rule["type"],
        description=desc,
        timestamp=now,
        features_json=json.dumps({"action": action, "severity": rule["severity"]})
    )
    db.add(record)

    # Update user anomaly score (cap at 99)
    user.anomaly_score = min(99.0, user.anomaly_score + rule["score_delta"])
    if user.anomaly_score > 80:
        user.critical_level = "Critical"
    elif user.anomaly_score > 60:
        user.critical_level = "High"
    elif user.anomaly_score > 40:
        user.critical_level = "Medium"
    else:
        user.critical_level = "Low"

    db.commit()

    return {
        "user_id": user.id,
        "user_name": user.name,
        "employee_id": user.employee_id,
        "type": rule["type"],
        "severity": rule["severity"],
        "description": desc,
        "timestamp": now.isoformat(),
        "score": round(user.anomaly_score, 1),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Background Auto-Randomizer Task
# ─────────────────────────────────────────────────────────────────────────────

async def _auto_anomaly_loop():
    """Every 18-30 s, inject a random UEBA rule event for a random user."""
    await asyncio.sleep(8)  # warm-up delay on startup
    while True:
        try:
            db = database.SessionLocal()
            users = db.query(models.User).filter(models.User.status == "Active").all()
            if users:
                target = random.choice(users)
                action = random.choice(ALL_ACTIONS)
                anomaly = apply_ueba_rule(action, target, db)
                if anomaly:
                    await push_event({"event": "new_anomaly", "data": anomaly})
            db.close()
        except Exception as e:
            print(f"[AutoRandomizer] Error: {e}")
        await asyncio.sleep(random.randint(18, 30))


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(_auto_anomaly_loop())


# ─────────────────────────────────────────────────────────────────────────────
# Mock Data Seeder
# ─────────────────────────────────────────────────────────────────────────────

def create_mock_data():
    db = database.SessionLocal()
    existing = db.query(models.User).count()
    if existing > 0:
        db.close()
        return  # Don't wipe data on restart — keep accumulated anomalies

    users = [
        ("E001", "employee1@ueba.local", "John Doe",      "Engineering", 15.0, "Low",      "Active"),
        ("E002", "hacker@ueba.local",    "Alice Smith",   "Finance",     85.0, "Critical", "Locked"),
        ("E003", "bob@ueba.local",       "Bob Johnson",   "Sales",       45.0, "Medium",   "Active"),
        ("E004", "sarah@ueba.local",     "Sarah Wilson",  "HR",          25.0, "Low",      "Active"),
        ("E005", "mike@ueba.local",      "Mike Brown",    "IT Support",  65.0, "High",     "Active"),
        ("E006", "emma@ueba.local",      "Emma Davis",    "Marketing",   10.0, "Low",      "Active"),
        ("E007", "david@ueba.local",     "David Clark",   "Operations",  55.0, "Medium",   "Active"),
        ("E008", "linda@ueba.local",     "Linda White",   "Legal",       35.0, "Low",      "Active"),
    ]

    for eid, email, name, dept, score, level, st in users:
        db.add(models.User(
            employee_id=eid, email=email, name=name, department=dept,
            hashed_password=auth.get_password_hash("password123"),
            anomaly_score=score, critical_level=level, status=st
        ))
    db.commit()

    # Seed some initial anomalies so the tables aren't empty on first load
    all_users = db.query(models.User).all()
    for u in all_users:
        num_initial = random.randint(2, 5)
        for _ in range(num_initial):
            rule = random.choice(UEBA_RULES)
            hours_ago = random.randint(1, 72)
            db.add(models.AnomalyRecord(
                user_id=u.id,
                type=rule["type"],
                description=random.choice(rule["descriptions"]),
                timestamp=datetime.datetime.now() - datetime.timedelta(hours=hours_ago),
                features_json=json.dumps({"seeded": True, "severity": rule["severity"]})
            ))
    db.commit()
    db.close()

create_mock_data()


# ─────────────────────────────────────────────────────────────────────────────
# SSE Streaming Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/events/stream")
async def sse_stream():
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _sse_subscribers.append(queue)

    async def event_generator():
        # Send a heartbeat immediately so the connection is established
        yield "data: {\"event\": \"connected\", \"ts\": \"" + datetime.datetime.now().isoformat() + "\"}\n\n"
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=25)
                    yield msg
                except asyncio.TimeoutError:
                    # Heartbeat to keep connection alive
                    yield f"data: {{\"event\": \"heartbeat\"}}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if queue in _sse_subscribers:
                _sse_subscribers.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# Authentication Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=schemas.Token)
def login_employee(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        (models.User.email == req.employee_id_or_email) |
        (models.User.employee_id == req.employee_id_or_email)
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    if user.status == "Locked":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={
            "message": "Account Locked",
            "reason": user.lock_reason or "Suspicious activity detected.",
            "user_id": user.id
        })

    if not auth.verify_password(req.password, user.hashed_password):
        user.login_attempts += 1
        if user.login_attempts >= 5:
            # FailedLoginService rule: MAX_FAILED_ATTEMPTS = 5
            apply_ueba_rule("brute_force_login", user, db)
        else:
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    user.login_attempts = 0
    db.commit()

    access_token = auth.create_access_token(
        data={"sub": user.employee_id, "role": "employee", "user_id": user.id},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer", "role": "employee", "user_id": user.id}


@app.post("/api/admin/login", response_model=schemas.Token)
def login_admin(req: schemas.AdminLoginRequest):
    if req.pin != ADMIN_PIN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN")
    access_token = auth.create_access_token(
        data={"sub": "admin", "role": "admin"},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer", "role": "admin"}


# ─────────────────────────────────────────────────────────────────────────────
# Simulation Endpoint  (employee portal behavior triggers)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/simulate/{user_id}")
async def simulate_event(user_id: int, body: dict, db: Session = Depends(get_db)):
    """
    POST body: { "action": "data_exfiltration" }
    Evaluates UEBA rule, writes anomaly to DB, pushes SSE event.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    action = body.get("action", random.choice(ALL_ACTIONS))
    anomaly = apply_ueba_rule(action, user, db)

    if anomaly:
        await push_event({"event": "new_anomaly", "data": anomaly})
        return {"status": "ok", "anomaly": anomaly}

    raise HTTPException(status_code=400, detail=f"Unknown action: {action}")


# ─────────────────────────────────────────────────────────────────────────────
# Admin User Management Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/admin/users", response_model=list[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@app.post("/api/admin/lock/{user_id}")
def lock_user(user_id: int, req: schemas.LockUserRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = "Locked"
    user.lock_reason = req.reason
    db.commit()
    return {"message": "User locked", "user_id": user.id, "status": user.status, "reason": user.lock_reason}


@app.post("/api/admin/unlock/{user_id}")
def unlock_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = "Active"
    # Reset behavioural score and all counters to zero on unlock
    user.anomaly_score = 0.0
    user.critical_level = "Low"
    user.login_attempts = 0
    user.lock_reason = None
    db.commit()
    return {"message": "User unlocked and score reset", "user_id": user.id, "status": user.status}



@app.post("/api/admin/users", response_model=schemas.UserResponse)
def create_user(req: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.employee_id == req.employee_id).first():
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    new_user = models.User(
        employee_id=req.employee_id, email=req.email, name=req.name,
        department=req.department,
        hashed_password=auth.get_password_hash(req.password),
        anomaly_score=req.anomaly_score, critical_level=req.critical_level,
        status=req.status
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.patch("/api/admin/users/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, req: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if req.name is not None:
        user.name = req.name
    if req.department is not None:
        user.department = req.department
    db.commit()
    db.refresh(user)
    return user


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard Statistics Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/stats/overview")
def get_stats_overview(db: Session = Depends(get_db)):
    total_users = db.query(models.User).count()
    # Count actual CRITICAL anomaly records
    critical_alerts = db.query(models.AnomalyRecord).filter(
        models.AnomalyRecord.features_json.contains("CRITICAL")
    ).count()
    locked_accounts = db.query(models.User).filter(models.User.status == "Locked").count()
    total_anomalies = db.query(models.AnomalyRecord).count()

    return {
        "total_users": total_users,
        "critical_alerts": critical_alerts,
        "locked_accounts": locked_accounts,
        "total_anomalies": total_anomalies,
        "system_status": "Healthy",
        "last_update": datetime.datetime.now().isoformat()
    }


@app.get("/api/stats/alerts-trend")
def get_alerts_trend(db: Session = Depends(get_db)):
    """Return actual anomaly counts per day for the last 7 days."""
    labels = []
    data = []
    for i in range(6, -1, -1):
        day = datetime.datetime.now() - datetime.timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + datetime.timedelta(days=1)
        count = db.query(models.AnomalyRecord).filter(
            models.AnomalyRecord.timestamp >= day_start,
            models.AnomalyRecord.timestamp < day_end
        ).count()
        labels.append(day.strftime("%Y-%m-%d"))
        data.append(count)
    return {"labels": labels, "data": data}


@app.get("/api/stats/risk-distribution")
def get_risk_distribution(db: Session = Depends(get_db)):
    critical = db.query(models.User).filter(models.User.critical_level == "Critical").count()
    high = db.query(models.User).filter(models.User.critical_level == "High").count()
    medium = db.query(models.User).filter(models.User.critical_level == "Medium").count()
    low = db.query(models.User).filter(models.User.critical_level == "Low").count()
    return {
        "labels": ["Critical", "High", "Medium", "Low"],
        "data": [critical, high, medium, low]
    }


@app.get("/api/stats/alerts-by-type")
def get_alerts_by_type(db: Session = Depends(get_db)):
    """Return anomaly counts grouped by type (for admin bar chart)."""
    records = db.query(models.AnomalyRecord).all()
    counts: dict = {}
    for r in records:
        counts[r.type] = counts.get(r.type, 0) + 1
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:8]
    return {
        "labels": [x[0] for x in sorted_counts],
        "data": [x[1] for x in sorted_counts]
    }


@app.get("/api/stats/recent-alerts")
def get_recent_alerts(db: Session = Depends(get_db), limit: int = 10):
    """Return the most recent anomaly records with user info."""
    records = (
        db.query(models.AnomalyRecord)
        .order_by(models.AnomalyRecord.timestamp.desc())
        .limit(limit)
        .all()
    )
    result = []
    for r in records:
        user = db.query(models.User).filter(models.User.id == r.user_id).first()
        severity = json.loads(r.features_json).get("severity", "MEDIUM") if r.features_json else "MEDIUM"
        result.append({
            "id": r.id,
            "user_name": user.name if user else "Unknown",
            "employee_id": user.employee_id if user else "?",
            "type": r.type,
            "severity": severity,
            "description": r.description,
            "timestamp": r.timestamp.isoformat()
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly API  (per-user, used by employee portal)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/anomalies/{user_id}")
async def get_user_anomalies(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Optionally call ML service for score update
    try:
        features = {
            "failed_logins": user.login_attempts,
            "location_change": 1 if user.anomaly_score > 60 else 0,
            "public_wifi": 1 if user.anomaly_score > 40 else 0,
            "data_usage_mb": float(random.randint(1000, 5000)) if user.anomaly_score > 70 else float(random.randint(100, 500)),
            "sensitive_access": 1 if user.anomaly_score > 80 else 0
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{ML_SERVICE_URL}/predict", json=features, timeout=3.0)
            if resp.status_code == 200:
                ml_result = resp.json()
                new_score = ml_result.get("anomaly_score", user.anomaly_score)
                user.anomaly_score = max(user.anomaly_score, new_score)
                if user.anomaly_score > 80: user.critical_level = "Critical"
                elif user.anomaly_score > 60: user.critical_level = "High"
                elif user.anomaly_score > 40: user.critical_level = "Medium"
                else: user.critical_level = "Low"
                db.commit()
    except Exception:
        pass  # ML service optional

    db_anomalies = (
        db.query(models.AnomalyRecord)
        .filter(models.AnomalyRecord.user_id == user.id)
        .order_by(models.AnomalyRecord.timestamp.desc())
        .all()
    )

    anomalies = []
    for a in db_anomalies:
        severity = "MEDIUM"
        if a.features_json:
            try:
                severity = json.loads(a.features_json).get("severity", "MEDIUM")
            except Exception:
                pass
        anomalies.append({
            "type": a.type,
            "description": a.description,
            "severity": severity,
            "timestamp": a.timestamp.isoformat()
        })

    return {
        "user_id": user.id,
        "anomalies": anomalies,
        "status": user.status,
        "score": round(user.anomaly_score, 1)
    }


# ─────────────────────────────────────────────────────────────────────────────
# PDF Report Generation
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/report/{user_id}")
async def download_user_report(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    anom_data = (await get_user_anomalies(user_id, db))["anomalies"]
    user_data = {
        "name": user.name, "employee_id": user.employee_id,
        "department": user.department, "status": user.status,
        "anomaly_score": user.anomaly_score, "critical_level": user.critical_level
    }
    pdf_buffer = report.generate_user_pdf_report(user_data, anom_data)
    return StreamingResponse(
        pdf_buffer,
        headers={"Content-Disposition": f'attachment; filename="ueba_report_{user.employee_id}.pdf"'},
        media_type="application/pdf"
    )



@app.get("/api/stats/threat-map")
def get_threat_map(db: Session = Depends(get_db)):
    """
    Returns simulated geo-origin attack data for the attack map widget.
    In production this would come from real IP geolocation lookups.
    """
    LOCATIONS = [
        {"city": "Moscow",    "country": "RU", "lat": 55.75,  "lng": 37.62,  "risk": "critical"},
        {"city": "Beijing",   "country": "CN", "lat": 39.91,  "lng": 116.39, "risk": "high"},
        {"city": "Bucharest", "country": "RO", "lat": 44.43,  "lng": 26.10,  "risk": "high"},
        {"city": "Lagos",     "country": "NG", "lat": 6.52,   "lng": 3.38,   "risk": "medium"},
        {"city": "São Paulo", "country": "BR", "lat": -23.55, "lng": -46.63, "risk": "medium"},
        {"city": "Tehran",    "country": "IR", "lat": 35.69,  "lng": 51.39,  "risk": "critical"},
        {"city": "Pyongyang", "country": "KP", "lat": 39.02,  "lng": 125.75, "risk": "critical"},
        {"city": "Kiev",      "country": "UA", "lat": 50.45,  "lng": 30.52,  "risk": "medium"},
        {"city": "Jakarta",   "country": "ID", "lat": -6.21,  "lng": 106.85, "risk": "low"},
        {"city": "Hanoi",     "country": "VN", "lat": 21.03,  "lng": 105.83, "risk": "medium"},
    ]
    total_records = db.query(models.AnomalyRecord).count()
    result = []
    for loc in LOCATIONS:
        hits = random.randint(1, 8) + (total_records // 10)
        result.append({**loc, "hits": hits})
    return result


@app.get("/api/stats/soc-log")
def get_soc_log(db: Session = Depends(get_db), limit: int = 20):
    """Returns recent audit log lines for the SOC terminal widget."""
    records = (
        db.query(models.AnomalyRecord)
        .order_by(models.AnomalyRecord.timestamp.desc())
        .limit(limit)
        .all()
    )
    import json as _json
    log_lines = []
    for r in records:
        user = db.query(models.User).filter(models.User.id == r.user_id).first()
        sev = "MEDIUM"
        if r.features_json:
            try: sev = _json.loads(r.features_json).get("severity", "MEDIUM")
            except: pass
        log_lines.append({
            "ts": r.timestamp.strftime("%H:%M:%S"),
            "level": sev,
            "user": user.employee_id if user else "???",
            "msg": r.type
        })
    return log_lines


@app.get("/api/stats/recent-alerts")
def get_recent_alerts(limit: int = 50, db: Session = Depends(get_db)):
    """Returns recent anomaly events for the Live Threat Feed expanded modal."""
    import json as _json
    records = (
        db.query(models.AnomalyRecord)
        .order_by(models.AnomalyRecord.timestamp.desc())
        .limit(limit)
        .all()
    )
    result = []
    for r in records:
        user = db.query(models.User).filter(models.User.id == r.user_id).first()
        sev  = "MEDIUM"
        desc = ""
        if r.features_json:
            try:
                data = _json.loads(r.features_json)
                sev  = data.get("severity", "MEDIUM")
                desc = data.get("description", "")
            except Exception:
                pass
        result.append({
            "id":          r.id,
            "type":        r.type,
            "severity":    sev,
            "description": desc,
            "timestamp":   r.timestamp.isoformat(),
            "user_name":   user.name         if user else "Unknown",
            "employee_id": user.employee_id  if user else "???",
            "department":  user.department   if user else "—",
        })
    return result


@app.get("/health")
def health_check():
    return {"status": "online"}


@app.get("/api/stats/top-risk-users")
def get_top_risk_users(limit: int = 8, db: Session = Depends(get_db)):
    """Returns the highest-risk users ranked by behavioral score."""
    users = (
        db.query(models.User)
        .order_by(models.User.anomaly_score.desc())
        .limit(limit)
        .all()
    )
    result = []
    for u in users:
        anomaly_count = db.query(models.AnomalyRecord).filter(
            models.AnomalyRecord.user_id == u.id
        ).count()
        result.append({
            "id":            u.id,
            "name":          u.name,
            "employee_id":   u.employee_id,
            "department":    u.department,
            "anomaly_score": round(u.anomaly_score, 1),
            "critical_level": u.critical_level,
            "status":        u.status,
            "anomaly_count": anomaly_count,
        })
    return result


@app.get("/api/stats/rule-engine-stats")
def get_rule_engine_stats(db: Session = Depends(get_db)):
    """Returns rule firing frequency grouped by anomaly type, with severity."""
    import json as _json
    records = db.query(models.AnomalyRecord).all()
    rule_data: dict = {}
    severity_map: dict = {}
    for r in records:
        t = r.type
        rule_data[t] = rule_data.get(t, 0) + 1
        if r.features_json and t not in severity_map:
            try:
                severity_map[t] = _json.loads(r.features_json).get("severity", "MEDIUM")
            except Exception:
                severity_map[t] = "MEDIUM"
    sorted_rules = sorted(rule_data.items(), key=lambda x: x[1], reverse=True)[:10]
    return [
        {"rule": name, "count": count, "severity": severity_map.get(name, "MEDIUM")}
        for name, count in sorted_rules
    ]
