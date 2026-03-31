
const API_BASE_URL = "http://localhost:8000/api";
let currentUserId = null;
let riskChart = null;
let sseSource = null;

// UEBA actions mapped from Java rule classes
const UEBA_ACTIONS = [
    "suspicious_login",
    "off_hours_login",
    "insecure_network",
    "data_exfiltration",
    "impossible_travel",
    "admin_panel_abuse",
    "lateral_movement",
    "unauthorized_software",
    "log_tampering",
    "privilege_escalation",
    "brute_force_login",
    "post_resignation"
];

// Map simulation buttons to the closest Java-rule action
const BUTTON_ACTION_MAP = {
    "suspicious_login":  "suspicious_login",
    "data_exfiltration": "data_exfiltration",
    "impossible_travel": "impossible_travel",
    "system_tampering":  "log_tampering",
    "admin_panel_abuse": "admin_panel_abuse",
    "off_hours_login":   "off_hours_login"
};

// ─────────────────────────────────────────────────────────────────────────────
// Auth
// ─────────────────────────────────────────────────────────────────────────────

async function loginEmployee(idOrEmail, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ employee_id_or_email: idOrEmail, password: password })
        });
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('employee_token', data.access_token);
            currentUserId = data.user_id;
            return { success: true };
        }
        if (response.status === 403) {
            const data = await response.json();
            return { success: false, locked: true, reason: data.detail.reason, user_id: data.detail.user_id };
        }
        return { success: false };
    } catch (error) {
        console.error("Login error:", error);
        return { success: false };
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Dashboard Init
// ─────────────────────────────────────────────────────────────────────────────

async function initEmployeeDashboard() {
    if (!currentUserId) return;

    initRiskGauge();
    await updateProfile();
    await loadMyAnomalies();
    populateActivityLog();
    setSessionContext();

    // SSE: get pushed updates when backend generates anomalies for this user
    connectSSE();
}

// ─────────────────────────────────────────────────────────────────────────────
// SSE Client
// ─────────────────────────────────────────────────────────────────────────────

function connectSSE() {
    if (sseSource) sseSource.close();
    sseSource = new EventSource(`${API_BASE_URL}/events/stream`);

    sseSource.onmessage = (evt) => {
        try {
            const msg = JSON.parse(evt.data);
            if (msg.event === "new_anomaly" && msg.data && msg.data.user_id === currentUserId) {
                // Our user got a new anomaly — refresh synchronously
                appendAnomaly(msg.data);
                updateProfile();
            }
        } catch (e) { /* heartbeat / parse error */ }
    };

    sseSource.onerror = () => {
        // Reconnect after 5 s
        setTimeout(connectSSE, 5000);
    };
}

// ─────────────────────────────────────────────────────────────────────────────
// Risk Gauge (Chart.js doughnut)
// ─────────────────────────────────────────────────────────────────────────────

function initRiskGauge() {
    const ctx = document.getElementById('riskGauge').getContext('2d');
    riskChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [0, 100],
                backgroundColor: ['#3b82f6', 'rgba(255,255,255,0.05)'],
                borderWidth: 0,
                circumference: 270,
                rotation: 225,
                cutout: '80%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } }
        }
    });
}

function updateRiskGauge(score) {
    if (!riskChart) return;
    const color = getScoreColorHex(score);
    riskChart.data.datasets[0].data = [score, 100 - score];
    riskChart.data.datasets[0].backgroundColor[0] = color;
    riskChart.update('none');

    const sv = document.getElementById('scoreValue');
    if (sv) { sv.innerText = Math.round(score); sv.style.color = color; }

    const badge = document.getElementById('riskBadge');
    if (badge) {
        badge.innerText = getRiskLevel(score);
        badge.className = `badge-portal status-${getRiskLevel(score).toLowerCase()}`;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Profile
// ─────────────────────────────────────────────────────────────────────────────

async function updateProfile() {
    try {
        const resp = await fetch(`${API_BASE_URL}/admin/users`);
        const users = await resp.json();
        const me = users.find(u => u.id === currentUserId);
        if (me) {
            const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
            setTxt('userDisplayName', me.name);
            setTxt('userDept', me.department);
            setTxt('userEmpId', me.employee_id);
            setTxt('userDeptDetail', me.department);
            setTxt('welcomeMsg', `Welcome, ${me.name.split(' ')[0]}`);

            const av = document.getElementById('userAvatar');
            if (av) av.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(me.name)}&background=3b82f6&color=fff`;

            updateRiskGauge(me.anomaly_score);
        }
    } catch (e) { console.error("Profile update error:", e); }
}

// ─────────────────────────────────────────────────────────────────────────────
// Anomaly List
// ─────────────────────────────────────────────────────────────────────────────

async function loadMyAnomalies() {
    const list = document.getElementById('anomalyList');
    if (!list) return;
    try {
        const resp = await fetch(`${API_BASE_URL}/anomalies/${currentUserId}`);
        const data = await resp.json();

        list.innerHTML = '';
        if (data.anomalies.length === 0) {
            list.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">No behavioral anomalies detected.</td></tr>';
        } else {
            data.anomalies.forEach(anom => {
                list.appendChild(buildAnomalyRow(anom));
            });
        }
        updateRiskGauge(data.score || 0);

        // Mirror to the "Security Alerts" tab as well
        const alertList = document.getElementById('anomalyListAlerts');
        if (alertList) alertList.innerHTML = list.innerHTML;

    } catch (e) {
        console.error("Failed to load anomalies:", e);
    }
}

function buildAnomalyRow(anom) {
    const tr = document.createElement('tr');
    const sev = anom.severity || getSeverityFromType(anom.type);
    const sevClass = sev === 'CRITICAL' ? 'emp-sev-high' : (sev === 'HIGH' ? 'emp-sev-high' : 'emp-sev-medium');
    tr.innerHTML = `
        <td><span class="fw-bold text-white">${anom.type}</span></td>
        <td><span class="emp-sev-pill ${sevClass}">${sev}</span></td>
        <td class="small text-secondary">${new Date(anom.timestamp).toLocaleString()}</td>
        <td class="small text-white">${anom.description}</td>
    `;
    return tr;
}

/** Prepend a single anomaly instantly (called from SSE push) */
function appendAnomaly(anomData) {
    const list = document.getElementById('anomalyList');
    if (!list) return;

    // Remove "no anomalies" placeholder if present
    const placeholder = list.querySelector('td[colspan]');
    if (placeholder) list.innerHTML = '';

    const row = buildAnomalyRow({
        type: anomData.type,
        severity: anomData.severity,
        description: anomData.description,
        timestamp: anomData.timestamp
    });

    // Flash animation
    row.style.animation = 'pulse 0.6s ease-out';
    list.insertBefore(row, list.firstChild);

    // Badge counter
    updateAlertBadge();

    // Mirror to alerts tab
    const alertList = document.getElementById('anomalyListAlerts');
    if (alertList) alertList.innerHTML = list.innerHTML;

    // Show toast notification
    showNotification(`⚠ ${anomData.severity} — ${anomData.type}`, 'danger');
}

function updateAlertBadge() {
    const badge = document.getElementById('alertCountBadge');
    if (badge) {
        const current = parseInt(badge.innerText) || 0;
        badge.innerText = current + 1;
        badge.classList.remove('d-none');
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Simulate Action (employee button → POST to backend)
// ─────────────────────────────────────────────────────────────────────────────

async function simulateAction(type) {
    const action = BUTTON_ACTION_MAP[type] || type;
    await postSimulateAction(action, true);
}

async function postSimulateAction(action, showToast = true) {
    if (!currentUserId) return;
    try {
        const resp = await fetch(`${API_BASE_URL}/simulate/${currentUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        if (resp.ok) {
            const result = await resp.json();
            if (result.anomaly) {
                appendAnomaly(result.anomaly);
                updateRiskGauge(result.anomaly.score);
            }
            if (showToast) {
                showNotification(`⚠ Event triggered: ${action.replaceAll('_', ' ').toUpperCase()}`, 'warning');
            }
        }
    } catch (e) {
        console.error("Simulation failed:", e);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Activity Log — dynamic from anomaly data
// ─────────────────────────────────────────────────────────────────────────────

function populateActivityLog() {
    const feed = document.getElementById('activityFeed');
    if (!feed) return;

    const activityTypes = [
        { icon: 'login',    fa: 'fa-sign-in-alt',    label: 'Login — Corporate VPN',              detail: () => `IP: ${randomIP()}` },
        { icon: 'download', fa: 'fa-file-download',  label: 'File Download — Q4_Report.xlsx',     detail: () => `${(Math.random()*10+0.5).toFixed(1)} MB · SharePoint` },
        { icon: 'system',   fa: 'fa-cog',            label: 'System Config Access — Registry',    detail: () => 'Local machine' },
        { icon: 'login',    fa: 'fa-network-wired',  label: 'VPN Session Established',            detail: () => `Tunnel: ${randomIP()}` },
        { icon: 'download', fa: 'fa-envelope',       label: 'External Email Sent',                detail: () => `To: ${randomEmail()} · DLP scanned` },
        { icon: 'system',   fa: 'fa-database',       label: 'Database Query — HR Records',        detail: () => `${Math.floor(Math.random()*200+50)} rows retrieved` },
        { icon: 'alert',    fa: 'fa-eye',            label: 'Admin Panel Viewed',                 detail: () => `/admin_panel · Access #${Math.floor(Math.random()*6+1)}` },
        { icon: 'download', fa: 'fa-cloud-upload-alt', label: 'Cloud Sync — OneDrive',           detail: () => `${Math.floor(Math.random()*50+5)} files uploaded` },
    ];

    feed.innerHTML = '';
    const now = new Date();
    const shuffled = [...activityTypes].sort(() => Math.random() - 0.5).slice(0, 7);
    shuffled.forEach((act, i) => {
        const t = new Date(now.getTime() - i * 47 * 60000);
        const item = document.createElement('div');
        item.className = 'activity-item';
        item.style.borderBottom = i < shuffled.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none';
        item.innerHTML = `
            <div class="activity-icon ${act.icon}"><i class="fas ${act.fa}"></i></div>
            <div>
                <div class="fw-bold text-white small">${act.label}</div>
                <div class="x-small" style="color:#94a3b8;">${formatTime(t)} &nbsp;·&nbsp; ${act.detail()}</div>
            </div>
        `;
        feed.appendChild(item);
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Session Context — randomized per session
// ─────────────────────────────────────────────────────────────────────────────

const LOCATIONS = ["New York, USA", "London, UK", "Singapore", "Toronto, Canada", "Berlin, Germany", "Sydney, Australia", "Mumbai, India"];
const DEVICES   = ["Windows 11", "macOS Ventura", "Ubuntu 22.04", "Chrome OS"];

function setSessionContext() {
    const locEl  = document.getElementById('userLocation');
    const devEl  = document.getElementById('userDevice');
    const ipEl   = document.getElementById('userIP');
    if (locEl) locEl.innerText = LOCATIONS[Math.floor(Math.random() * LOCATIONS.length)];
    if (devEl) devEl.innerText = DEVICES[Math.floor(Math.random() * DEVICES.length)];
    if (ipEl)  ipEl.innerText  = randomIP();
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function getScoreColorHex(score) {
    if (score > 80) return '#ef4444';
    if (score > 60) return '#f59e0b';
    if (score > 40) return '#3b82f6';
    return '#10b981';
}

function getRiskLevel(score) {
    if (score > 80) return 'Critical';
    if (score > 60) return 'High';
    if (score > 40) return 'Medium';
    return 'Low';
}

function getSeverityFromType(type) {
    if (!type) return 'MEDIUM';
    if (type.includes('Brute') || type.includes('Tamper') || type.includes('Exfil') || type.includes('Privilege')) return 'CRITICAL';
    if (type.includes('Travel') || type.includes('Sensitive') || type.includes('Lateral') || type.includes('Resign')) return 'HIGH';
    return 'MEDIUM';
}

function randomIP() {
    return `${192 + Math.floor(Math.random() * 2)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 100)}.${Math.floor(Math.random() * 254) + 1}`;
}

function randomEmail() {
    const domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'];
    const names = ['user', 'contact', 'info', 'admin', 'hr'];
    return `${names[Math.floor(Math.random() * names.length)]}@${domains[Math.floor(Math.random() * domains.length)]}`;
}

function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function showNotification(msg, type = 'primary') {
    const colors = { danger: '#ef4444', warning: '#f59e0b', primary: '#3b82f6', success: '#10b981' };
    const color = colors[type] || colors.primary;
    const toast = document.createElement('div');
    toast.style.cssText = `
        position:fixed; bottom:20px; right:20px; z-index:9999;
        background:#0f172a; color:#fff; padding:14px 18px;
        border-radius:12px; border-left:4px solid ${color};
        box-shadow:0 10px 25px rgba(0,0,0,0.5); font-size:0.85rem;
        min-width:280px; animation: slideInRight 0.3s ease-out;
    `;
    toast.innerHTML = `<i class="fas fa-satellite-dish me-2" style="color:${color};"></i>${msg}`;
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateY(10px)'; toast.style.transition = 'all 0.4s'; setTimeout(() => toast.remove(), 400); }, 4500);
}

function logout() {
    localStorage.removeItem('employee_token');
    if (sseSource) sseSource.close();
    window.location.reload();
}
