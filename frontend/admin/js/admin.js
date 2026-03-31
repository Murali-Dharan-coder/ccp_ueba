const API_BASE_URL = "http://localhost:8000/api";

// Chart instances (stored globally so we can update, not recreate)
let anomalyTrendChart = null;
let riskDistChart = null;
let alertTypeChart = null;
let adminSSE = null;

// ─────────────────────────────────────────────────────────────────────────────
// Authentication
// ─────────────────────────────────────────────────────────────────────────────

async function loginAdmin(pin) {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pin: pin })
        });
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('admin_token', data.access_token);
            return true;
        }
        return false;
    } catch (error) {
        console.error("Login error:", error);
        return false;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Dashboard Init
// ─────────────────────────────────────────────────────────────────────────────

async function initDashboard() {
    await updateStats();
    await initCharts();
    await loadLiveFeed();

    // SSE: receive real-time pushes from backend
    connectAdminSSE();

    // Periodic fallback refresh (every 20 s)
    setInterval(async () => {
        await updateStats();
        refreshChartData();
        await loadLiveFeed();
    }, 20000);
}

// ─────────────────────────────────────────────────────────────────────────────
// Admin SSE Client
// ─────────────────────────────────────────────────────────────────────────────

function connectAdminSSE() {
    if (adminSSE) adminSSE.close();
    adminSSE = new EventSource(`${API_BASE_URL}/events/stream`);

    adminSSE.onmessage = async (evt) => {
        try {
            const msg = JSON.parse(evt.data);
            if (msg.event === "new_anomaly") {
                // Instant update — no page reload needed
                await updateStats();
                refreshChartData();
                prependLiveFeedItem(msg.data);
                flashAlertIndicator();
            }
        } catch (e) { /* heartbeat */ }
    };

    adminSSE.onerror = () => {
        setTimeout(connectAdminSSE, 5000);
    };
}

function flashAlertIndicator() {
    const badge = document.getElementById('liveAlertDot');
    if (!badge) return;
    badge.classList.add('pulse-danger');
    setTimeout(() => badge.classList.remove('pulse-danger'), 2000);
}

// ─────────────────────────────────────────────────────────────────────────────
// Stats
// ─────────────────────────────────────────────────────────────────────────────

async function updateStats() {
    try {
        const resp = await fetch(`${API_BASE_URL}/stats/overview`);
        const stats = await resp.json();

        setText('totalUsers',     stats.total_users);
        setText('criticalAlerts', stats.critical_alerts);
        setText('lockedAccounts', stats.locked_accounts);
        setText('systemHealth',   stats.system_status);
        setText('totalAnomalies', stats.total_anomalies ?? '');
    } catch (e) {
        console.error("Stats update failed:", e);
    }
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el && value !== undefined) el.innerText = value;
}

// ─────────────────────────────────────────────────────────────────────────────
// Charts
// ─────────────────────────────────────────────────────────────────────────────

const CHART_DEFAULTS = {
    color: { grid: 'rgba(255,255,255,0.04)', tick: '#64748b' }
};

async function initCharts() {
    await initTrendChart();
    await initRiskChart();
    await initAlertTypeChart();
}

async function initTrendChart() {
    const canvas = document.getElementById('anomalyChart');
    if (!canvas) return;
    try {
        const resp = await fetch(`${API_BASE_URL}/stats/alerts-trend`);
        const d = await resp.json();

        if (anomalyTrendChart) anomalyTrendChart.destroy();
        anomalyTrendChart = new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: d.labels,
                datasets: [{
                    label: 'Anomalies',
                    data: d.data,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59,130,246,0.08)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#3b82f6',
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15,23,42,0.95)',
                        borderColor: 'rgba(59,130,246,0.3)',
                        borderWidth: 1,
                        titleColor: '#93c5fd',
                        bodyColor: '#cbd5e1'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: CHART_DEFAULTS.color.grid },
                        ticks: { color: CHART_DEFAULTS.color.tick }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: CHART_DEFAULTS.color.tick }
                    }
                }
            }
        });
    } catch (e) { console.error("Trend chart error:", e); }
}

async function initRiskChart() {
    const canvas = document.getElementById('riskChart');
    if (!canvas) return;
    try {
        const resp = await fetch(`${API_BASE_URL}/stats/risk-distribution`);
        const d = await resp.json();

        if (riskDistChart) riskDistChart.destroy();
        riskDistChart = new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: d.labels,
                datasets: [{
                    data: d.data,
                    backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'],
                    borderColor: 'rgba(15,23,42,0.8)',
                    borderWidth: 3,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '68%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#94a3b8',
                            padding: 14,
                            usePointStyle: true,
                            pointStyleWidth: 10
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15,23,42,0.95)',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8'
                    }
                }
            }
        });
    } catch (e) { console.error("Risk chart error:", e); }
}

async function initAlertTypeChart() {
    const canvas = document.getElementById('alertTypeChart');
    if (!canvas) return;
    try {
        const resp = await fetch(`${API_BASE_URL}/stats/alerts-by-type`);
        const d = await resp.json();

        if (alertTypeChart) alertTypeChart.destroy();
        alertTypeChart = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: d.labels,
                datasets: [{
                    label: 'Count',
                    data: d.data,
                    backgroundColor: [
                        'rgba(239,68,68,0.7)','rgba(245,158,11,0.7)','rgba(59,130,246,0.7)',
                        'rgba(16,185,129,0.7)','rgba(139,92,246,0.7)','rgba(236,72,153,0.7)',
                        'rgba(20,184,166,0.7)','rgba(251,146,60,0.7)'
                    ],
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: CHART_DEFAULTS.color.grid },
                        ticks: { color: CHART_DEFAULTS.color.tick }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#cbd5e1', font: { size: 11 } }
                    }
                }
            }
        });
    } catch (e) { console.error("Alert type chart error:", e); }
}

async function refreshChartData() {
    // Update existing chart data without full destroy/recreate
    try {
        const trendResp = await fetch(`${API_BASE_URL}/stats/alerts-trend`);
        const trendData = await trendResp.json();
        if (anomalyTrendChart) {
            anomalyTrendChart.data.labels = trendData.labels;
            anomalyTrendChart.data.datasets[0].data = trendData.data;
            anomalyTrendChart.update('active');
        }

        const riskResp = await fetch(`${API_BASE_URL}/stats/risk-distribution`);
        const riskData = await riskResp.json();
        if (riskDistChart) {
            riskDistChart.data.datasets[0].data = riskData.data;
            riskDistChart.update('active');
        }

        const typeResp = await fetch(`${API_BASE_URL}/stats/alerts-by-type`);
        const typeData = await typeResp.json();
        if (alertTypeChart) {
            alertTypeChart.data.labels = typeData.labels;
            alertTypeChart.data.datasets[0].data = typeData.data;
            alertTypeChart.update('active');
        }
    } catch (e) { console.error("Chart refresh error:", e); }
}

// ─────────────────────────────────────────────────────────────────────────────
// Live Threat Feed
// ─────────────────────────────────────────────────────────────────────────────

async function loadLiveFeed() {
    const container = document.getElementById('liveFeedList');
    if (!container) return;
    try {
        const resp = await fetch(`${API_BASE_URL}/stats/recent-alerts?limit=8`);
        const items = await resp.json();
        container.innerHTML = '';
        items.forEach(item => container.appendChild(buildFeedItem(item)));
    } catch (e) { console.error("Live feed error:", e); }
}

function prependLiveFeedItem(data) {
    const container = document.getElementById('liveFeedList');
    if (!container) return;
    const item = buildFeedItem({
        user_name: data.user_name,
        employee_id: data.employee_id,
        type: data.type,
        severity: data.severity,
        description: data.description,
        timestamp: data.timestamp
    });
    item.style.animation = 'slideInFeed 0.4s ease-out';
    container.insertBefore(item, container.firstChild);
    // Keep max 8 items
    while (container.children.length > 8) container.removeChild(container.lastChild);
}

function buildFeedItem(item) {
    const div = document.createElement('div');
    const sevColor = item.severity === 'CRITICAL' ? '#ef4444' : (item.severity === 'HIGH' ? '#f59e0b' : '#3b82f6');
    div.style.cssText = 'display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.04);';
    div.innerHTML = `
        <div style="width:8px;height:8px;border-radius:50%;background:${sevColor};flex-shrink:0;box-shadow:0 0 6px ${sevColor};"></div>
        <div style="flex:1;min-width:0;">
            <div style="font-size:0.78rem;font-weight:600;color:#f1f5f9;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${item.type}</div>
            <div style="font-size:0.7rem;color:#64748b;">${item.user_name || '—'} · ${new Date(item.timestamp).toLocaleTimeString()}</div>
        </div>
        <span style="font-size:0.65rem;font-weight:700;padding:2px 7px;border-radius:10px;background:${sevColor}20;color:${sevColor};border:1px solid ${sevColor}40;flex-shrink:0;">${item.severity}</span>
    `;
    return div;
}

// ─────────────────────────────────────────────────────────────────────────────
// Alerts Page
// ─────────────────────────────────────────────────────────────────────────────

let allUsers = [];

async function loadAllAlerts() {
    const tbody = document.getElementById('alertsBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-center text-secondary py-5"><div class="shimmer" style="height:20px;width:100%"></div></td></tr>';

    try {
        const [usersResp, recentResp] = await Promise.all([
            fetch(`${API_BASE_URL}/admin/users`),
            fetch(`${API_BASE_URL}/stats/recent-alerts?limit=100`)
        ]);
        const users = await usersResp.json();
        const alerts = await recentResp.json();

        if (tbody) tbody.innerHTML = '';
        if (alerts.length === 0) {
            if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-5">No behavioral anomalies identified in current feed.</td></tr>';
            return;
        }

        alerts.forEach(alert => {
            const tr = document.createElement('tr');
            const sev = alert.severity || 'MEDIUM';
            const sevClass = sev === 'CRITICAL' ? 'sev-critical' : (sev === 'HIGH' ? 'sev-high' : 'sev-elevated');
            tr.className = 'user-row border-bottom border-white border-opacity-5';

            tr.innerHTML = `
                <td style="padding:14px 20px;">
                    <div class="d-flex align-items-center">
                        <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(alert.user_name)}&background=1e293b&color=3b82f6" class="rounded-circle me-3" width="32">
                        <div>
                            <div class="fw-bold text-white small">${alert.user_name}</div>
                            <div class="x-small" style="color:#94a3b8;">${alert.employee_id}</div>
                        </div>
                    </div>
                </td>
                <td class="small" style="color:#cbd5e1;">${new Date(alert.timestamp).toLocaleString()}</td>
                <td><span class="threat-chip">${alert.type}</span></td>
                <td><span class="sev-badge ${sevClass}">${sev}</span></td>
                <td class="small text-white">${alert.description}</td>
            `;
            tbody.appendChild(tr);
        });

        // Auto-refresh alerts page via SSE too
        if (!adminSSE) connectAdminSSE();

    } catch (e) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Network error: failed to downlink alert data.</td></tr>';
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Risk Analysis
// ─────────────────────────────────────────────────────────────────────────────

async function loadRiskAnalysis() {
    const tbody = document.getElementById('riskBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-center text-secondary py-5">Loading workforce analytics...</td></tr>';

    try {
        const resp = await fetch(`${API_BASE_URL}/admin/users`);
        if (!resp.ok) throw new Error("API call failed");
        allUsers = await resp.json();
        renderUserTable(allUsers);
        if (!adminSSE) connectAdminSSE();
    } catch (e) {
        if (tbody) tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Transmission Error: ${e.message}</td></tr>`;
    }
}

function renderUserTable(usersToRender) {
    const tbody = document.getElementById('riskBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    usersToRender.sort((a, b) => b.anomaly_score - a.anomaly_score);

    usersToRender.forEach(user => {
        const tr = document.createElement('tr');
        tr.className = 'user-row border-bottom border-white border-opacity-5';
        const scoreColor = getScoreColor(user.anomaly_score);

        tr.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=1e293b&color=3b82f6" class="rounded-circle me-3" width="35">
                    <div>
                        <div class="fw-bold text-white">${user.name}</div>
                        <div class="text-secondary x-small">${user.employee_id} | ${user.email}</div>
                    </div>
                </div>
            </td>
            <td><span class="text-white small">${user.department}</span></td>
            <td>
                <div class="d-flex align-items-center">
                    <div class="progress flex-grow-1 me-3" style="height:6px;background:rgba(255,255,255,0.05)">
                        <div class="progress-bar bg-${scoreColor}" style="width:${user.anomaly_score}%"></div>
                    </div>
                    <span class="fw-bold text-white small">${Math.round(user.anomaly_score)}</span>
                </div>
            </td>
            <td>
                <span style="display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;font-size:0.7rem;font-weight:700;letter-spacing:0.05em;
                    background:${user.status === 'Locked' ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)'};
                    color:${user.status === 'Locked' ? '#fca5a5' : '#6ee7b7'};
                    border:1px solid ${user.status === 'Locked' ? 'rgba(239,68,68,0.3)' : 'rgba(16,185,129,0.3)'};">
                    <span style="width:6px;height:6px;border-radius:50%;display:inline-block;background:${user.status === 'Locked' ? '#ef4444' : '#10b981'};"></span>
                    ${user.status.toUpperCase()}
                </span>
            </td>
            <td>
                <div class="d-flex gap-1">
                    <button type="button" style="background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.25);color:#93c5fd;border-radius:8px;padding:5px 9px;cursor:pointer;" title="Intelligence Report" onclick="viewUserReport(${user.id})">
                        <i class="fas fa-file-pdf" style="font-size:0.85rem;"></i>
                    </button>
                    <button type="button" style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);color:#a5b4fc;border-radius:8px;padding:5px 9px;cursor:pointer;" title="Edit Profile" onclick="openEditModal(${user.id}, '${user.name.replace(/'/g, "\\'")}')">
                        <i class="fas fa-user-edit" style="font-size:0.85rem;"></i>
                    </button>
                    ${user.status === 'Active'
                        ? `<button type="button" style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);color:#fca5a5;border-radius:8px;padding:5px 9px;cursor:pointer;" title="Lock Account" onclick="toggleUserLock(${user.id}, 'lock')"><i class="fas fa-lock" style="font-size:0.85rem;"></i></button>`
                        : `<button type="button" style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);color:#6ee7b7;border-radius:8px;padding:5px 9px;cursor:pointer;" title="Unlock Account" onclick="toggleUserLock(${user.id}, 'unlock')"><i class="fas fa-lock-open" style="font-size:0.85rem;"></i></button>`
                    }
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });

    if (usersToRender.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-secondary py-5">No subjects currently registered.</td></tr>';
    }
}

function filterUsers() {
    const searchTerm = document.getElementById('userSearch').value.toLowerCase();
    const deptFilter = document.getElementById('deptFilter').value;
    const sortType = document.getElementById('riskSort').value;

    let filtered = allUsers.filter(u => {
        const matchSearch = u.name.toLowerCase().includes(searchTerm) || u.employee_id.toLowerCase().includes(searchTerm);
        const matchDept = deptFilter === "" || u.department === deptFilter;
        return matchSearch && matchDept;
    });

    if (sortType === 'desc') filtered.sort((a, b) => b.anomaly_score - a.anomaly_score);
    else if (sortType === 'asc') filtered.sort((a, b) => a.anomaly_score - b.anomaly_score);
    else if (sortType === 'name') filtered.sort((a, b) => a.name.localeCompare(b.name));

    renderUserTable(filtered);
}

function getScoreColor(score) {
    if (score > 80) return 'danger';
    if (score > 60) return 'warning';
    if (score > 40) return 'info';
    return 'success';
}

// ─────────────────────────────────────────────────────────────────────────────
// User Management Actions
// ─────────────────────────────────────────────────────────────────────────────

async function toggleUserLock(userId, action) {
    if (action === 'lock') {
        document.getElementById('lockUserId').value = userId;
        document.getElementById('lockReasonInput').value = '';
        let modalEl = document.getElementById('lockUserModal');
        let modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
        modal.show();
        return;
    }

    const confirmMsg = "Protocol Restoration: Reactivate this subject's credentials?";
    if (!confirm(confirmMsg)) return;

    try {
        const resp = await fetch(`${API_BASE_URL}/admin/unlock/${userId}`, { method: 'POST' });
        if (resp.ok) {
            showActionToast("Access Restored", `Security protocol updated for Subject #${userId}.`, "success");
            loadRiskAnalysis();
            updateStats();
        } else {
            showActionToast("Protocol Failed", "Authorization server rejected the request.", "warning");
        }
    } catch (e) {
        showActionToast("Connection Interrupted", "Neural link to backend failed.", "danger");
    }
}

async function submitLockUser() {
    const userId = document.getElementById('lockUserId').value;
    const reason = document.getElementById('lockReasonInput').value || "Administrative lock: Unusual behavioral activity detected.";
    
    try {
        const resp = await fetch(`${API_BASE_URL}/admin/lock/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason })
        });
        if (resp.ok) {
            const modalEl = document.getElementById('lockUserModal');
            bootstrap.Modal.getInstance(modalEl).hide();
            showActionToast("Access Restricted", `Security protocol updated for Subject #${userId}.`, "danger");
            loadRiskAnalysis();
            updateStats();
        } else {
            showActionToast("Protocol Failed", "Authorization server rejected the request.", "warning");
        }
    } catch (e) {
        showActionToast("Connection Interrupted", "Neural link to backend failed.", "danger");
    }
}

function viewUserReport(userId) {
    window.open(`${API_BASE_URL}/report/${userId}`, '_blank');
}

function openEditModal(userId, currentName) {
    document.getElementById('editUserId').value = userId;
    document.getElementById('editNameInput').value = currentName;
    let modalEl = document.getElementById('editUserModal');
    let modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    modal.show();
}

async function submitEditUser() {
    const userId = document.getElementById('editUserId').value;
    const newName = document.getElementById('editNameInput').value;
    if (!newName) return;
    try {
        const resp = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: newName })
        });
        if (resp.ok) {
            bootstrap.Modal.getInstance(document.getElementById('editUserModal')).hide();
            loadRiskAnalysis();
        } else { alert("Update failed"); }
    } catch (e) { alert("Connection error"); }
}

async function submitAddUser() {
    const data = {
        employee_id: document.getElementById('addEmpId').value,
        name: document.getElementById('addName').value,
        email: document.getElementById('addEmail').value,
        department: document.getElementById('addDept').value,
        password: document.getElementById('addPass').value
    };
    if (!data.employee_id || !data.name || !data.email) { alert("Please fill in all required fields."); return; }
    try {
        const resp = await fetch(`${API_BASE_URL}/admin/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (resp.ok) {
            bootstrap.Modal.getInstance(document.getElementById('addUserModal')).hide();
            document.getElementById('addUserForm').reset();
            loadRiskAnalysis();
            updateStats();
        } else {
            const err = await resp.json();
            alert(`Error: ${err.detail || 'Failed to add user'}`);
        }
    } catch (e) { alert("Connection error"); }
}

// ─────────────────────────────────────────────────────────────────────────────
// Toast Notification
// ─────────────────────────────────────────────────────────────────────────────

function showActionToast(title, message, type = 'primary') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = 'cyber-card p-3 mb-2';
    toast.style.cssText = `min-width:300px;background:rgba(15,23,42,0.95);border-left:4px solid ${type === 'danger' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};box-shadow:0 10px 30px rgba(0,0,0,0.5);`;
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="me-3"><i class="fas ${type === 'danger' ? 'fa-shield-alt' : type === 'success' ? 'fa-user-check' : 'fa-info-circle'} text-${type}" style="font-size:1.5rem;"></i></div>
            <div>
                <div class="fw-bold text-white small" style="letter-spacing:1px;">${title.toUpperCase()}</div>
                <div class="text-secondary x-small">${message}</div>
            </div>
        </div>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.transition = 'all 0.5s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

function getSeverity(type) {
    if (!type) return 'ELEVATED';
    if (type.includes('Brute') || type.includes('Tamper') || type.includes('Exfil') || type.includes('Privilege')) return 'CRITICAL';
    if (type.includes('Travel') || type.includes('Sensitive') || type.includes('Lateral') || type.includes('Resign')) return 'HIGH';
    return 'ELEVATED';
}
