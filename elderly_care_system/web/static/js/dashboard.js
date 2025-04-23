/**
 * GuardianCare - Dashboard JavaScript
 * Handles all client-side functionality for the elderly care system
 */

// Initialize socket connection
const socket = io();

// System state tracking - delegated to common.js
const getSystemRunning = () => window.guardianCareCommon?.isSystemRunning() || false;
const getEmergencyMode = () => window.guardianCareCommon?.isEmergencyMode() || false;
let dataLoadedCount = 0;

// DOM Elements
const startSystemBtn = document.getElementById('startSystemBtn');
const stopSystemBtn = document.getElementById('stopSystemBtn');
const refreshDashboardBtn = document.getElementById('refreshDashboardBtn');
const clearAlertsBtn = document.getElementById('clearAlertsBtn');
const clearActivitiesBtn = document.getElementById('clearActivitiesBtn');
const systemStatusBtn = document.getElementById('system-status');
const alertsList = document.getElementById('alerts-list');
const activityFeed = document.getElementById('activity-feed');
const healthVitals = document.getElementById('health-vitals');
const safetyStatus = document.getElementById('safety-status');
const activeReminders = document.getElementById('active-reminders');

// Status overview elements
const statusHealthIndicator = document.getElementById('status-health-indicator');
const statusSafetyIndicator = document.getElementById('status-safety-indicator');
const statusRemindersIndicator = document.getElementById('status-reminders-indicator');
const statusSystemIndicator = document.getElementById('status-system-indicator');
const statusHealthValue = document.getElementById('status-health-value');
const statusSafetyValue = document.getElementById('status-safety-value');
const statusRemindersValue = document.getElementById('status-reminders-value');
const statusSystemValue = document.getElementById('status-system-value');

// Loading state references
const healthLoadingState = document.querySelector('#health-status-card .loading-state');
const safetyLoadingState = document.querySelector('#safety-status-card .loading-state');
const remindersLoadingState = document.querySelector('#reminders-card .loading-state');

// Timestamp references
const healthDataTimestamp = document.querySelector('.health-data-timestamp');
const safetyDataTimestamp = document.querySelector('.safety-data-timestamp');
const remindersDataTimestamp = document.querySelector('.reminders-data-timestamp');

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Initial data load
    refreshDashboardData();
    
    // Check system status immediately
    checkSystemStatus();
    
    // Periodic updates - only refresh data if system is running
    setInterval(() => {
        if (getSystemRunning()) {
            refreshDashboardData();
        }
    }, 60000); // Every minute if system is running
    
    // Event listeners - only for dashboard-specific controls
    if (startSystemBtn) startSystemBtn.addEventListener('click', startSystem);
    if (stopSystemBtn) stopSystemBtn.addEventListener('click', stopSystem);
    if (refreshDashboardBtn) {
        refreshDashboardBtn.addEventListener('click', () => {
            refreshDashboardData(true);
            addActivityItem('Dashboard data manually refreshed');
        });
    }
    
    if (clearAlertsBtn) {
        clearAlertsBtn.addEventListener('click', clearAlerts);
    }
    
    if (clearActivitiesBtn) {
        clearActivitiesBtn.addEventListener('click', clearActivities);
    }
});

// Function to check system status
function checkSystemStatus() {
    fetch('/api/system/status')
        .then(response => response.json())
        .then(data => {
            const isRunning = data.status === "System running";
            const isEmergency = data.emergency_mode === true;
            updateSystemStatusDisplay(isRunning, isEmergency);
        })
        .catch(error => {
            console.error('Error fetching system status:', error);
            updateSystemStatusDisplay(false, false);
        });
}

// Update system status display
function updateSystemStatusDisplay(isRunning, isEmergency) {
    if (!systemStatusBtn) return;
    
    const statusIndicator = systemStatusBtn.querySelector('.status-indicator');
    
    if (isEmergency) {
        if (statusIndicator) statusIndicator.className = 'status-indicator emergency';
        systemStatusBtn.innerHTML = '<span class="status-indicator emergency"></span> EMERGENCY';
    } else if (isRunning) {
        if (statusIndicator) statusIndicator.className = 'status-indicator active';
        systemStatusBtn.innerHTML = '<span class="status-indicator active"></span> System Active';
    } else {
        if (statusIndicator) statusIndicator.className = 'status-indicator inactive';
        systemStatusBtn.innerHTML = '<span class="status-indicator inactive"></span> System Inactive';
    }
    
    // Update control buttons
    if (startSystemBtn && stopSystemBtn) {
        startSystemBtn.disabled = isRunning;
        stopSystemBtn.disabled = !isRunning;
    }
}

// Refresh all dashboard data
function refreshDashboardData(showLoadingState = false) {
    // Reset data loaded counter
    dataLoadedCount = 0;
    
    // Show loading states if requested
    if (showLoadingState) {
        showLoadingStates();
    }
    
    // Update all data sections
    updateHealthData();
    updateSafetyData();
    updateReminders();
}

// Show loading states
function showLoadingStates() {
    if (healthLoadingState) {
        healthLoadingState.classList.remove('d-none');
        healthVitals.classList.add('d-none');
        healthDataTimestamp.classList.add('d-none');
    }
    
    if (safetyLoadingState) {
        safetyLoadingState.classList.remove('d-none');
        safetyStatus.classList.add('d-none');
        safetyDataTimestamp.classList.add('d-none');
    }
    
    if (remindersLoadingState) {
        remindersLoadingState.classList.remove('d-none');
        activeReminders.classList.add('d-none');
        remindersDataTimestamp.classList.add('d-none');
    }
}

// Check if all data sections are loaded
function checkDataLoaded() {
    dataLoadedCount++;
    // When all 3 sections are loaded, update overview
    if (dataLoadedCount >= 3) {
        updateStatusOverview();
    }
}

// Update the status overview section
function updateStatusOverview() {
    // Set health status
    const healthData = healthVitals.querySelectorAll('.health-metric').length;
    if (healthData > 0) {
        statusHealthValue.textContent = `${healthData} metrics available`;
        statusHealthIndicator.innerHTML = '<i class="bi bi-heart-pulse text-primary"></i>';
    } else {
        statusHealthValue.textContent = 'No data';
        statusHealthIndicator.innerHTML = '<i class="bi bi-heart-pulse text-muted"></i>';
    }
    
    // Set safety status
    const safetyData = safetyStatus.querySelectorAll('.safety-status-item').length;
    if (safetyData > 0) {
        statusSafetyValue.textContent = `${safetyData} checks active`;
        statusSafetyIndicator.innerHTML = '<i class="bi bi-shield-check text-success"></i>';
    } else {
        statusSafetyValue.textContent = 'No data';
        statusSafetyIndicator.innerHTML = '<i class="bi bi-shield-check text-muted"></i>';
    }
    
    // Set reminders status
    const reminderData = activeReminders.querySelectorAll('.reminder-item').length;
    if (reminderData > 0) {
        statusRemindersValue.textContent = `${reminderData} active`;
        statusRemindersIndicator.innerHTML = '<i class="bi bi-bell text-warning"></i>';
    } else {
        statusRemindersValue.textContent = 'None active';
        statusRemindersIndicator.innerHTML = '<i class="bi bi-bell text-muted"></i>';
    }
    
    // Set system status
    if (getSystemRunning()) {
        statusSystemValue.textContent = getEmergencyMode() ? 'Emergency Mode' : 'Active';
        statusSystemIndicator.innerHTML = getEmergencyMode() ? 
            '<i class="bi bi-cpu text-danger"></i>' : 
            '<i class="bi bi-cpu text-info"></i>';
    } else {
        statusSystemValue.textContent = 'Inactive';
        statusSystemIndicator.innerHTML = '<i class="bi bi-cpu text-muted"></i>';
    }
}

// Clear alerts
function clearAlerts() {
    alertsList.innerHTML = '<div class="list-group-item text-center text-muted">No alerts to display</div>';
    addActivityItem('Alerts cleared');
}

// Clear activities
function clearActivities() {
    activityFeed.innerHTML = '<div class="list-group-item text-center text-muted">No activities to display</div>';
}

// Socket event listeners for dashboard-specific events
socket.on('connect', () => {
    console.log('Dashboard socket connected to server');
    addActivityItem('Connected to server');
    checkSystemStatus();
});

socket.on('disconnect', () => {
    console.log('Dashboard socket disconnected from server');
    addActivityItem('Disconnected from server', 'warning');
    updateSystemStatusDisplay(false, false);
});

socket.on('system_status', (data) => {
    console.log('System status update received:', data);
    updateSystemStatusDisplay(data.running, data.emergency_mode);
});

socket.on('update', (data) => {
    console.log('Received update:', data);
    addActivityItem(data.message);
});

socket.on('health_update', (data) => {
    console.log('Health update:', data);
    updateHealthDisplay(data);
    addActivityItem(`Health update received: ${getUpdateSummary(data)}`);
});

socket.on('safety_update', (data) => {
    console.log('Safety update:', data);
    updateSafetyDisplay(data);
    addActivityItem(`Safety update received: ${getUpdateSummary(data)}`);
});

socket.on('reminder', (data) => {
    console.log('Reminder:', data);
    addReminder(data);
    addActivityItem(`Reminder: ${data.message}`);
});

socket.on('alert', (data) => {
    console.log('Alert:', data);
    addAlert(data);
    playAlertSound(data.alert_type);
});

// System control functions
function startSystem() {
    fetch('/api/system/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Start system response:', data);
        addActivityItem(`System start command: ${data.status}`);
        
        // Refresh data after starting system
        refreshDashboardData(true);
    })
    .catch(error => {
        console.error('Error starting system:', error);
        addActivityItem('Error starting system', 'error');
    });
}

function stopSystem() {
    fetch('/api/system/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Stop system response:', data);
        addActivityItem(`System stop command: ${data.status}`);
    })
    .catch(error => {
        console.error('Error stopping system:', error);
        addActivityItem('Error stopping system', 'error');
    });
}

// Data update functions
function updateHealthData() {
    fetch('/api/health/data')
    .then(response => response.json())
    .then(data => {
        updateHealthDisplay(data);
    })
    .catch(error => {
        console.error('Error fetching health data:', error);
        if (healthLoadingState) {
            healthLoadingState.classList.add('d-none');
            healthVitals.classList.remove('d-none');
            healthVitals.innerHTML = '<p class="text-danger">Error loading health data. <button class="btn btn-sm btn-outline-primary" onclick="updateHealthData()">Try Again</button></p>';
        }
        checkDataLoaded();
    });
}

function updateSafetyData() {
    fetch('/api/safety/data')
    .then(response => response.json())
    .then(data => {
        updateSafetyDisplay(data);
    })
    .catch(error => {
        console.error('Error fetching safety data:', error);
        if (safetyLoadingState) {
            safetyLoadingState.classList.add('d-none');
            safetyStatus.classList.remove('d-none');
            safetyStatus.innerHTML = '<p class="text-danger">Error loading safety data. <button class="btn btn-sm btn-outline-success" onclick="updateSafetyData()">Try Again</button></p>';
        }
        checkDataLoaded();
    });
}

function updateReminders() {
    fetch('/api/reminders')
    .then(response => response.json())
    .then(data => {
        updateRemindersDisplay(data);
    })
    .catch(error => {
        console.error('Error fetching reminders:', error);
        if (remindersLoadingState) {
            remindersLoadingState.classList.add('d-none');
            activeReminders.classList.remove('d-none');
            activeReminders.innerHTML = '<li class="list-group-item text-danger">Error loading reminders. <button class="btn btn-sm btn-outline-warning" onclick="updateReminders()">Try Again</button></li>';
        }
        checkDataLoaded();
    });
}

// Display update functions
function updateHealthDisplay(data) {
    // Update timestamp
    if (healthDataTimestamp) {
        const timestamp = new Date().toLocaleTimeString();
        healthDataTimestamp.querySelector('span').textContent = timestamp;
        healthDataTimestamp.classList.remove('d-none');
    }
    
    // Hide loading state and show content
    if (healthLoadingState) {
        healthLoadingState.classList.add('d-none');
        healthVitals.classList.remove('d-none');
    }
    
    if (!data.latest_readings) {
        healthVitals.innerHTML = '<p class="text-muted">No health data available</p>';
        checkDataLoaded();
        return;
    }
    
    const readings = data.latest_readings;
    let html = '';
    
    if ('heart_rate' in readings) {
        html += createHealthMetric('heart', 'Heart Rate', `${readings.heart_rate} bpm`);
    }
    
    if ('systolic_bp' in readings && 'diastolic_bp' in readings) {
        html += createHealthMetric('activity', 'Blood Pressure', `${readings.systolic_bp}/${readings.diastolic_bp} mmHg`);
    }
    
    if ('glucose' in readings) {
        html += createHealthMetric('droplet-half', 'Glucose', `${readings.glucose} mg/dL`);
    }
    
    if ('oxygen_saturation' in readings) {
        html += createHealthMetric('lungs', 'Oxygen Saturation', `${readings.oxygen_saturation}%`);
    }
    
    if ('temperature' in readings) {
        html += createHealthMetric('thermometer', 'Temperature', `${readings.temperature}°C`);
    }
    
    healthVitals.innerHTML = html || '<p class="text-muted">No health data available</p>';
    checkDataLoaded();
}

function updateSafetyDisplay(data) {
    // Update timestamp
    if (safetyDataTimestamp) {
        const timestamp = new Date().toLocaleTimeString();
        safetyDataTimestamp.querySelector('span').textContent = timestamp;
        safetyDataTimestamp.classList.remove('d-none');
    }
    
    // Hide loading state and show content
    if (safetyLoadingState) {
        safetyLoadingState.classList.add('d-none');
        safetyStatus.classList.remove('d-none');
    }
    
    if (!data.latest_readings) {
        safetyStatus.innerHTML = '<p class="text-muted">No safety data available</p>';
        checkDataLoaded();
        return;
    }
    
    const readings = data.latest_readings;
    let html = '';
    
    if ('movement_activity' in readings) {
        const status = readings.movement_activity === 'Active' ? 'ok' : 'warning';
        html += createSafetyStatusItem(status, 'Movement', readings.movement_activity);
    }
    
    if ('fall_detected' in readings) {
        const status = readings.fall_detected ? 'danger' : 'ok';
        html += createSafetyStatusItem(status, 'Fall Detection', readings.fall_detected ? 'Fall Detected!' : 'No Falls');
    }
    
    if ('location' in readings) {
        html += createSafetyStatusItem('ok', 'Location', readings.location);
    }
    
    if ('door_status' in readings) {
        const status = readings.door_status === 'Closed' ? 'ok' : 'warning';
        html += createSafetyStatusItem(status, 'Door Status', readings.door_status);
    }
    
    safetyStatus.innerHTML = html || '<p class="text-muted">No safety data available</p>';
    checkDataLoaded();
}

function updateRemindersDisplay(data) {
    // Update timestamp
    if (remindersDataTimestamp) {
        const timestamp = new Date().toLocaleTimeString();
        remindersDataTimestamp.querySelector('span').textContent = timestamp;
        remindersDataTimestamp.classList.remove('d-none');
    }
    
    // Hide loading state and show content
    if (remindersLoadingState) {
        remindersLoadingState.classList.add('d-none');
        activeReminders.classList.remove('d-none');
    }
    
    if (!data.active_reminders || data.active_reminders.length === 0) {
        activeReminders.innerHTML = '<li class="list-group-item text-center text-muted">No active reminders</li>';
        checkDataLoaded();
        return;
    }
    
    let html = '';
    for (const reminder of data.active_reminders) {
        html += createReminderItem(reminder);
    }
    
    activeReminders.innerHTML = html;
    
    // Add event listeners to the acknowledge buttons
    document.querySelectorAll('.acknowledge-btn').forEach(button => {
        button.addEventListener('click', function() {
            const reminderId = this.getAttribute('data-id');
            acknowledgeReminder(reminderId);
        });
    });
    
    checkDataLoaded();
}

// Alert and activity feed functions
function addAlert(data) {
    const alertItem = document.createElement('div');
    alertItem.className = `list-group-item alert-item ${data.alert_type || ''}`;
    
    const timestamp = new Date(data.timestamp).toLocaleTimeString();
    
    let alertContent = '';
    if (Array.isArray(data.alert_messages)) {
        alertContent = data.alert_messages.join('<br>');
    } else {
        alertContent = data.message || 'Unknown alert';
    }
    
    alertItem.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <strong>${data.alert_type || 'System'} Alert</strong>
            <span class="alert-time">${timestamp}</span>
        </div>
        <p class="mb-0">${alertContent}</p>
    `;
    
    // Add the pulse effect for emergency alerts
    if (data.alert_type === 'safety' || getEmergencyMode()) {
        alertItem.classList.add('alert-pulse');
    }
    
    // Remove "no alerts" message if present
    const noAlerts = alertsList.querySelector('.text-muted');
    if (noAlerts) {
        alertsList.removeChild(noAlerts);
    }
    
    // Add to the list
    alertsList.prepend(alertItem);
    
    // Limit the number of alerts shown
    if (alertsList.children.length > 10) {
        alertsList.removeChild(alertsList.lastChild);
    }
}

function addActivityItem(message, type = 'info') {
    const activityItem = document.createElement('div');
    activityItem.className = `list-group-item activity-item ${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    activityItem.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <span>${message}</span>
            <span class="alert-time">${timestamp}</span>
        </div>
    `;
    
    // Remove "no activities" message if present
    const noActivities = activityFeed.querySelector('.text-muted');
    if (noActivities) {
        activityFeed.removeChild(noActivities);
    }
    
    // Add to the list
    activityFeed.prepend(activityItem);
    
    // Limit the number of activities shown
    if (activityFeed.children.length > 10) {
        activityFeed.removeChild(activityFeed.lastChild);
    }
}

function addReminder(data) {
    // Create reminder notification
    const reminder = {
        id: data.id || Date.now().toString(),
        type: data.reminder_type || 'General',
        message: data.message,
        time: data.timestamp || new Date().toISOString()
    };
    
    // Add to active reminders
    updateReminders();
    
    // Show as alert
    addAlert({
        alert_type: 'reminder',
        timestamp: reminder.time,
        alert_messages: [`${reminder.type}: ${reminder.message}`]
    });
}

function acknowledgeReminder(reminderId) {
    fetch('/api/acknowledge-reminder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ reminder_id: reminderId })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Reminder acknowledged:', data);
        addActivityItem(`Reminder ${reminderId} acknowledged`);
        updateReminders();
    })
    .catch(error => {
        console.error('Error acknowledging reminder:', error);
    });
}

// Helper functions
function createHealthMetric(icon, label, value) {
    return `
        <div class="health-metric">
            <div class="health-metric-icon">
                <i class="bi bi-${icon}"></i>
            </div>
            <div>
                <div class="health-metric-value">${value}</div>
                <div class="health-metric-label">${label}</div>
            </div>
        </div>
    `;
}

function createSafetyStatusItem(status, label, value) {
    return `
        <div class="safety-status-item">
            <span class="safety-status-icon ${status}">
                <i class="bi bi-${status === 'ok' ? 'check' : status === 'warning' ? 'exclamation' : 'x'}-circle"></i>
            </span>
            <strong>${label}:</strong> ${value}
        </div>
    `;
}

function createReminderItem(reminder) {
    const time = new Date(reminder.time).toLocaleTimeString();
    
    return `
        <li class="list-group-item reminder-item">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <div><strong>${reminder.type}</strong></div>
                    <div>${reminder.message}</div>
                    <div class="reminder-time">Scheduled: ${time}</div>
                </div>
                <div class="reminder-actions">
                    <button class="btn btn-sm btn-outline-success acknowledge-btn" data-id="${reminder.id}">
                        Acknowledge
                    </button>
                </div>
            </div>
        </li>
    `;
}

function getUpdateSummary(data) {
    if (!data || !data.latest_readings) return 'No data';
    
    const readings = data.latest_readings;
    const keys = Object.keys(readings);
    
    if (keys.length === 0) return 'No readings';
    
    // Return first reading as summary
    const key = keys[0];
    return `${key}: ${readings[key]}`;
}

function playAlertSound(alertType) {
    // In a real implementation, this would play different sounds based on alert type
    console.log(`Playing ${alertType} alert sound`);
    
    // Use the Web Audio API for a simple beep sound
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Different frequency based on alert type
        switch (alertType) {
            case 'health':
                oscillator.frequency.value = 440; // A4
                break;
            case 'safety':
                oscillator.frequency.value = 880; // A5
                break;
            case 'reminder':
                oscillator.frequency.value = 330; // E4
                break;
            default:
                oscillator.frequency.value = 220; // A3
        }
        
        gainNode.gain.value = 0.1;
        oscillator.start();
        
        // Stop after 0.5 seconds
        setTimeout(() => {
            oscillator.stop();
        }, 500);
    } catch (error) {
        console.error('Error playing alert sound:', error);
    }
}