/**
 * common.js - Shared functionality across the elderly care system web interface
 * This file contains common functions for system status, socket connections,
 * and other utilities that are reused across different pages.
 */

// Global variables
let socket = null;
let isSystemRunning = false;
let isEmergencyMode = false;

// DOM Elements
let systemStatusElement = null;
let statusIndicator = null;
let startSystemBtn = null;
let stopSystemBtn = null;

// Page detection
const isDashboardPage = window.location.pathname === '/dashboard' || window.location.pathname === '/';

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Find common UI elements
    systemStatusElement = document.getElementById('system-status');
    statusIndicator = document.querySelector('.status-indicator');
    startSystemBtn = document.getElementById('startSystemBtn');
    stopSystemBtn = document.getElementById('stopSystemBtn');
    
    // Initialize socket
    socket = initSocket();
    
    // Set up system control button listeners
    if (startSystemBtn) {
        startSystemBtn.addEventListener('click', startSystem);
    }
    
    if (stopSystemBtn) {
        stopSystemBtn.addEventListener('click', stopSystem);
    }
    
    // Initial status check
    checkSystemStatus();
});

// Initialize socket connection
function initSocket() {
    if (socket) return socket; // Return existing socket if already initialized
    
    // Create socket connection
    socket = io();
    
    // Set up basic socket event listeners
    socket.on('connect', function() {
        console.log('Connected to server');
        checkSystemStatus(); // Force a system status check on connect
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        isSystemRunning = false;
        isEmergencyMode = false;
        updateSystemStatusIndicator();
    });
    
    // Listen for system status updates
    socket.on('system_status', function(data) {
        console.log('Received system status update:', data);
        isSystemRunning = data.running;
        isEmergencyMode = data.emergency_mode;
        updateSystemStatusIndicator();
        
        // Update control buttons
        updateSystemControlButtons();
    });
    
    // Listen for emergency alerts
    socket.on('emergency_alert', function(data) {
        handleEmergencyAlert(data);
    });
    
    return socket;
}

// Check system status via API
function checkSystemStatus() {
    fetch('/api/system/status')
        .then(response => response.json())
        .then(data => {
            isSystemRunning = data.status === "System running";
            isEmergencyMode = data.emergency_mode === true;
            updateSystemStatusIndicator();
            updateSystemControlButtons();
        })
        .catch(error => {
            console.error('Error fetching system status:', error);
            isSystemRunning = false;
            isEmergencyMode = false;
            updateSystemStatusIndicator();
            updateSystemControlButtons();
        });
}

// Update system status indicator in the UI
function updateSystemStatusIndicator() {
    if (!statusIndicator || !systemStatusElement) return;
    
    if (isEmergencyMode) {
        statusIndicator.className = 'status-indicator emergency';
        systemStatusElement.innerHTML = '<span class="status-indicator emergency"></span> EMERGENCY';
        document.body.classList.add('emergency-mode');
    } else if (isSystemRunning) {
        statusIndicator.className = 'status-indicator active';
        systemStatusElement.innerHTML = '<span class="status-indicator active"></span> System Active';
        document.body.classList.remove('emergency-mode');
    } else {
        statusIndicator.className = 'status-indicator inactive';
        systemStatusElement.innerHTML = '<span class="status-indicator inactive"></span> System Inactive';
        document.body.classList.remove('emergency-mode');
    }
}

// Update system control buttons based on system status
function updateSystemControlButtons() {
    if (!startSystemBtn || !stopSystemBtn) return;
    
    if (isSystemRunning) {
        startSystemBtn.disabled = true;
        stopSystemBtn.disabled = false;
    } else {
        startSystemBtn.disabled = false;
        stopSystemBtn.disabled = true;
    }
}

// Handle emergency alerts
function handleEmergencyAlert(data) {
    // Create and show alert notification
    const alertContainer = document.createElement('div');
    alertContainer.className = 'alert alert-danger alert-dismissible fade show emergency-alert';
    alertContainer.innerHTML = `
        <strong>EMERGENCY ALERT!</strong> ${data.message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to document body
    document.body.appendChild(alertContainer);
    
    // Play alert sound if available
    const alertSound = new Audio('/static/sounds/alert.wav');
    alertSound.play().catch(e => console.log('Could not play alert sound:', e));
    
    // Auto-dismiss after 10 seconds
    setTimeout(() => {
        alertContainer.classList.remove('show');
        setTimeout(() => alertContainer.remove(), 1000);
    }, 10000);
}

// System control functions
function startSystem() {
    fetch('/api/system/start', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "System started successfully") {
            console.log('System started successfully');
            checkSystemStatus(); // Refresh system status
        } else {
            console.error('Error starting system:', data);
            alert('Failed to start system: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error starting system:', error);
    });
}

function stopSystem() {
    fetch('/api/system/stop', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "System stopped successfully") {
            console.log('System stopped successfully');
            checkSystemStatus(); // Refresh system status
        } else {
            console.error('Error stopping system:', data);
            alert('Failed to stop system: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error stopping system:', error);
    });
}

function acknowledgeEmergency() {
    if (socket) {
        socket.emit('control_system', { action: 'acknowledge_emergency' });
    }
}

// Getters for system status
function getSystemRunning() {
    return isSystemRunning;
}

function getEmergencyMode() {
    return isEmergencyMode;
}

// Export public functions and variables for other scripts to use
window.guardianCareCommon = {
    isSystemRunning: getSystemRunning,
    isEmergencyMode: getEmergencyMode,
    startSystem: startSystem,
    stopSystem: stopSystem,
    acknowledgeEmergency: acknowledgeEmergency,
    updateSystemStatus: updateSystemStatusIndicator,
    checkSystemStatus: checkSystemStatus
}; 