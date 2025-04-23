// Settings page JavaScript

// Initialize socket connection
const socket = io();

// DOM Elements
const systemStatus = document.getElementById('system-status');
const startSystemBtn = document.getElementById('startSystemBtn');
const stopSystemBtn = document.getElementById('stopSystemBtn');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');
const systemSettingsForm = document.getElementById('system-settings-form');
const notificationSettingsForm = document.getElementById('notification-settings-form');
const healthThresholdsForm = document.getElementById('health-thresholds-form');
const dataSourceForm = document.getElementById('data-source-form');

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    initializeSocketListeners();
    initializeButtons();
    initializeForms();
    loadSettings();
});

// Initialize buttons
function initializeButtons() {
    if (startSystemBtn) startSystemBtn.addEventListener('click', startSystem);
    if (stopSystemBtn) stopSystemBtn.addEventListener('click', stopSystem);
    if (saveSettingsBtn) saveSettingsBtn.addEventListener('click', saveAllSettings);
}

// Initialize forms
function initializeForms() {
    // System settings form
    if (systemSettingsForm) {
        systemSettingsForm.addEventListener('submit', function(event) {
            event.preventDefault();
            saveSystemSettings();
        });
    }
    
    // Notification settings form
    if (notificationSettingsForm) {
        notificationSettingsForm.addEventListener('submit', function(event) {
            event.preventDefault();
            saveNotificationSettings();
        });
    }
    
    // Health thresholds form
    if (healthThresholdsForm) {
        healthThresholdsForm.addEventListener('submit', function(event) {
            event.preventDefault();
            saveHealthThresholds();
        });
    }
    
    // Data source form
    if (dataSourceForm) {
        dataSourceForm.addEventListener('submit', function(event) {
            event.preventDefault();
            uploadDataFiles();
        });
    }
    
    // Add listeners for tab features that need special handling
    const remindersTabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    remindersTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            // You could run special logic when tabs are shown
            console.log('Tab activated:', event.target.id);
        });
    });
}

// Socket listeners
function initializeSocketListeners() {
    // System status
    socket.on('system_status', function(data) {
        updateSystemStatus(data.running, data.emergency_mode);
    });
}

// Save all settings at once
function saveAllSettings() {
    // Save all settings categories
    saveSystemSettings();
    saveNotificationSettings();
    saveHealthThresholds();
    
    // Show success message
    showAlert('All settings saved successfully', 'success');
}

// Load settings from localStorage
function loadSettings() {
    // System settings - check if elements exist before setting values
    const dataRefreshInterval = localStorage.getItem('dataRefreshInterval') || 60;
    const enableNotifications = localStorage.getItem('enableNotifications') !== 'false';
    const emergencyContact = localStorage.getItem('emergencyContact') || '';
    
    setElementValueSafely('dataRefreshInterval', dataRefreshInterval);
    setElementCheckedSafely('enableNotifications', enableNotifications);
    setElementValueSafely('emergencyContact', emergencyContact);
    
    // Additional system settings
    setElementCheckedSafely('enableSystemSwitch', localStorage.getItem('enableSystemSwitch') !== 'false');
    setElementValueSafely('systemLanguage', localStorage.getItem('systemLanguage') || 'en');
    setElementValueSafely('voiceType', localStorage.getItem('voiceType') || 'female');
    setElementValueSafely('voiceVolume', localStorage.getItem('voiceVolume') || 75);
    setElementValueSafely('caregiverContact', localStorage.getItem('caregiverContact') || '');
    
    // Health monitoring settings
    setElementCheckedSafely('enableHealthMonitoring', localStorage.getItem('enableHealthMonitoring') !== 'false');
    setElementValueSafely('heartRateMin', localStorage.getItem('heartRateMin') || 60);
    setElementValueSafely('heartRateMax', localStorage.getItem('heartRateMax') || 100);
    setElementValueSafely('systolicMin', localStorage.getItem('systolicMin') || 90);
    setElementValueSafely('diastolicMin', localStorage.getItem('diastolicMin') || 60);
    setElementValueSafely('systolicMax', localStorage.getItem('systolicMax') || 140);
    setElementValueSafely('diastolicMax', localStorage.getItem('diastolicMax') || 90);
    setElementValueSafely('temperatureMin', localStorage.getItem('temperatureMin') || 36.0);
    setElementValueSafely('temperatureMax', localStorage.getItem('temperatureMax') || 37.5);
    setElementValueSafely('glucoseMin', localStorage.getItem('glucoseMin') || 70);
    setElementValueSafely('glucoseMax', localStorage.getItem('glucoseMax') || 180);
    setElementValueSafely('oxygenMin', localStorage.getItem('oxygenMin') || 95);
    
    // Safety monitoring settings
    setElementCheckedSafely('enableSafetyMonitoring', localStorage.getItem('enableSafetyMonitoring') !== 'false');
    setElementCheckedSafely('enableFallDetection', localStorage.getItem('enableFallDetection') !== 'false');
    setElementCheckedSafely('enableLocationTracking', localStorage.getItem('enableLocationTracking') !== 'false');
    setElementCheckedSafely('enableDoorMonitoring', localStorage.getItem('enableDoorMonitoring') !== 'false');
    setElementValueSafely('inactivityThreshold', localStorage.getItem('inactivityThreshold') || 4);
    
    // Reminders settings
    setElementCheckedSafely('enableReminders', localStorage.getItem('enableReminders') !== 'false');
    setElementValueSafely('reminderLeadTime', localStorage.getItem('reminderLeadTime') || 15);
    setElementValueSafely('reminderRepeatInterval', localStorage.getItem('reminderRepeatInterval') || 5);
    setElementValueSafely('reminderMaxRepeats', localStorage.getItem('reminderMaxRepeats') || 3);
    setElementCheckedSafely('notifyCaregiverAfterMaxRepeats', localStorage.getItem('notifyCaregiverAfterMaxRepeats') !== 'false');
    
    // Notification settings
    setElementCheckedSafely('enableNotifications', localStorage.getItem('enableNotifications') !== 'false');
    setElementCheckedSafely('enableVoiceNotifications', localStorage.getItem('enableVoiceNotifications') !== 'false');
    setElementCheckedSafely('enableTextNotifications', localStorage.getItem('enableTextNotifications') !== 'false');
    setElementCheckedSafely('enableEmailNotifications', localStorage.getItem('enableEmailNotifications') === 'true');
    setElementValueSafely('healthNotificationPriority', localStorage.getItem('healthNotificationPriority') || 'high');
    setElementValueSafely('safetyNotificationPriority', localStorage.getItem('safetyNotificationPriority') || 'high');
    setElementValueSafely('reminderNotificationPriority', localStorage.getItem('reminderNotificationPriority') || 'medium');
    setElementValueSafely('quietHoursStart', localStorage.getItem('quietHoursStart') || '22:00');
    setElementValueSafely('quietHoursEnd', localStorage.getItem('quietHoursEnd') || '07:00');
}

// Helper function to safely set element values
function setElementValueSafely(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.value = value;
    }
}

// Helper function to safely set element checked state
function setElementCheckedSafely(elementId, checked) {
    const element = document.getElementById(elementId);
    if (element) {
        element.checked = checked;
    }
}

// Save system settings
function saveSystemSettings() {
    // Get system settings values safely
    const enableSystemSwitch = getElementCheckedSafely('enableSystemSwitch', true);
    const systemLanguage = getElementValueSafely('systemLanguage', 'en');
    const voiceType = getElementValueSafely('voiceType', 'female');
    const voiceVolume = getElementValueSafely('voiceVolume', 75);
    const emergencyContact = getElementValueSafely('emergencyContact', '');
    const caregiverContact = getElementValueSafely('caregiverContact', '');
    
    // Save to localStorage
    localStorage.setItem('enableSystemSwitch', enableSystemSwitch);
    localStorage.setItem('systemLanguage', systemLanguage);
    localStorage.setItem('voiceType', voiceType);
    localStorage.setItem('voiceVolume', voiceVolume);
    localStorage.setItem('emergencyContact', emergencyContact);
    localStorage.setItem('caregiverContact', caregiverContact);
    
    // Show success message
    showAlert('System settings saved successfully', 'success');
    
    // If notifications are enabled, request permission
    if (enableSystemSwitch && ("Notification" in window)) {
        Notification.requestPermission();
    }
}

// Save notification settings
function saveNotificationSettings() {
    // Get notification settings values safely
    const enableNotifications = getElementCheckedSafely('enableNotifications', true);
    const enableVoiceNotifications = getElementCheckedSafely('enableVoiceNotifications', true);
    const enableTextNotifications = getElementCheckedSafely('enableTextNotifications', true);
    const enableEmailNotifications = getElementCheckedSafely('enableEmailNotifications', false);
    const healthNotificationPriority = getElementValueSafely('healthNotificationPriority', 'high');
    const safetyNotificationPriority = getElementValueSafely('safetyNotificationPriority', 'high');
    const reminderNotificationPriority = getElementValueSafely('reminderNotificationPriority', 'medium');
    const quietHoursStart = getElementValueSafely('quietHoursStart', '22:00');
    const quietHoursEnd = getElementValueSafely('quietHoursEnd', '07:00');
    
    // Save to localStorage
    localStorage.setItem('enableNotifications', enableNotifications);
    localStorage.setItem('enableVoiceNotifications', enableVoiceNotifications);
    localStorage.setItem('enableTextNotifications', enableTextNotifications);
    localStorage.setItem('enableEmailNotifications', enableEmailNotifications);
    localStorage.setItem('healthNotificationPriority', healthNotificationPriority);
    localStorage.setItem('safetyNotificationPriority', safetyNotificationPriority);
    localStorage.setItem('reminderNotificationPriority', reminderNotificationPriority);
    localStorage.setItem('quietHoursStart', quietHoursStart);
    localStorage.setItem('quietHoursEnd', quietHoursEnd);
    
    // Show success message
    showAlert('Notification settings saved successfully', 'success');
}

// Helper function to safely get element checked state
function getElementCheckedSafely(elementId, defaultValue) {
    const element = document.getElementById(elementId);
    return element ? element.checked : defaultValue;
}

// Helper function to safely get element value
function getElementValueSafely(elementId, defaultValue) {
    const element = document.getElementById(elementId);
    return element ? element.value : defaultValue;
}

// Save health thresholds
function saveHealthThresholds() {
    // Get health settings values safely
    const enableHealthMonitoring = getElementCheckedSafely('enableHealthMonitoring', true);
    const heartRateMin = getElementValueSafely('heartRateMin', 60);
    const heartRateMax = getElementValueSafely('heartRateMax', 100);
    const systolicMin = getElementValueSafely('systolicMin', 90);
    const diastolicMin = getElementValueSafely('diastolicMin', 60);
    const systolicMax = getElementValueSafely('systolicMax', 140);
    const diastolicMax = getElementValueSafely('diastolicMax', 90);
    const temperatureMin = getElementValueSafely('temperatureMin', 36.0);
    const temperatureMax = getElementValueSafely('temperatureMax', 37.5);
    const glucoseMin = getElementValueSafely('glucoseMin', 70);
    const glucoseMax = getElementValueSafely('glucoseMax', 180);
    const oxygenMin = getElementValueSafely('oxygenMin', 95);
    
    // Save to localStorage
    localStorage.setItem('enableHealthMonitoring', enableHealthMonitoring);
    localStorage.setItem('heartRateMin', heartRateMin);
    localStorage.setItem('heartRateMax', heartRateMax);
    localStorage.setItem('systolicMin', systolicMin);
    localStorage.setItem('diastolicMin', diastolicMin);
    localStorage.setItem('systolicMax', systolicMax);
    localStorage.setItem('diastolicMax', diastolicMax);
    localStorage.setItem('temperatureMin', temperatureMin);
    localStorage.setItem('temperatureMax', temperatureMax);
    localStorage.setItem('glucoseMin', glucoseMin);
    localStorage.setItem('glucoseMax', glucoseMax);
    localStorage.setItem('oxygenMin', oxygenMin);
    
    // Also update thresholds in the system via API
    updateHealthThresholds({
        heartrate_min: parseInt(heartRateMin),
        heartrate_max: parseInt(heartRateMax),
        blood_pressure_systolic_min: parseInt(systolicMin),
        blood_pressure_diastolic_min: parseInt(diastolicMin),
        blood_pressure_systolic_max: parseInt(systolicMax),
        blood_pressure_diastolic_max: parseInt(diastolicMax),
        temperature_min: parseFloat(temperatureMin),
        temperature_max: parseFloat(temperatureMax),
        blood_glucose_min: parseInt(glucoseMin),
        blood_glucose_max: parseInt(glucoseMax),
        oxygen_level_min: parseInt(oxygenMin)
    });
    
    // Show success message
    showAlert('Health thresholds saved successfully', 'success');
}

// Update health thresholds via API
function updateHealthThresholds(thresholds) {
    // This would be a real API call in a production system
    console.log('Updating health thresholds:', thresholds);
    
    // For each threshold, make an API call
    Object.entries(thresholds).forEach(([metric, value]) => {
        // Mock API call - would be real in production
        console.log(`Setting ${metric} to ${value}`);
    });
}

// Upload data files
function uploadDataFiles() {
    const healthDataFile = document.getElementById('healthDataFile')?.files[0];
    const safetyDataFile = document.getElementById('safetyDataFile')?.files[0];
    const reminderDataFile = document.getElementById('reminderDataFile')?.files[0];
    const medicationDataFile = document.getElementById('medicationDataFile')?.files[0];
    
    // Check if any files were selected
    if (!healthDataFile && !safetyDataFile && !reminderDataFile && !medicationDataFile) {
        showAlert('Please select at least one file to upload', 'warning');
        return;
    }
    
    // Create FormData object
    const formData = new FormData();
    if (healthDataFile) formData.append('health_data', healthDataFile);
    if (safetyDataFile) formData.append('safety_data', safetyDataFile);
    if (reminderDataFile) formData.append('reminder_data', reminderDataFile);
    if (medicationDataFile) formData.append('medication_data', medicationDataFile);
    
    // Show uploading message
    showAlert('Uploading files...', 'info');
    
    // In a real app, this would be an actual API call
    setTimeout(() => {
        // Simulate successful upload
        showAlert('Files uploaded successfully', 'success');
        
        // Clear file inputs
        if (document.getElementById('healthDataFile')) document.getElementById('healthDataFile').value = '';
        if (document.getElementById('safetyDataFile')) document.getElementById('safetyDataFile').value = '';
        if (document.getElementById('reminderDataFile')) document.getElementById('reminderDataFile').value = '';
        if (document.getElementById('medicationDataFile')) document.getElementById('medicationDataFile').value = '';
    }, 1500);
}

// Show an alert message
function showAlert(message, type = 'info') {
    // Create alert element
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show fixed-top w-50 mx-auto mt-3`;
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to document
    document.body.appendChild(alertElement);
    
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        alertElement.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(alertElement);
        }, 300);
    }, 3000);
}

// Update system status indicator
function updateSystemStatus(isRunning, isEmergency = false) {
    if (!systemStatus) {
        console.warn('System status element not found');
        return;
    }
    
    const statusIndicator = systemStatus.querySelector('.status-indicator');
    if (!statusIndicator) {
        console.warn('Status indicator element not found');
        return;
    }
    
    if (isEmergency) {
        systemStatus.classList.remove('btn-outline-secondary', 'btn-outline-success');
        systemStatus.classList.add('btn-outline-danger');
        statusIndicator.className = 'status-indicator emergency';
        systemStatus.innerHTML = '<span class="status-indicator emergency"></span> EMERGENCY';
    } else if (isRunning) {
        systemStatus.classList.remove('btn-outline-secondary', 'btn-outline-danger');
        systemStatus.classList.add('btn-outline-success');
        statusIndicator.className = 'status-indicator active';
        systemStatus.innerHTML = '<span class="status-indicator active"></span> System Active';
    } else {
        systemStatus.classList.remove('btn-outline-success', 'btn-outline-danger');
        systemStatus.classList.add('btn-outline-secondary');
        statusIndicator.className = 'status-indicator inactive';
        systemStatus.innerHTML = '<span class="status-indicator inactive"></span> System Inactive';
    }
}

// Start the system
function startSystem() {
    fetch('/api/system/start', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('System start response:', data);
        if (data.status === 'System started successfully') {
            updateSystemStatus(true);
            showAlert('System started successfully', 'success');
        } else {
            showAlert('Error starting system: ' + data.status, 'danger');
        }
    })
    .catch(error => {
        console.error('Error starting system:', error);
        showAlert('Error starting system', 'danger');
    });
}

// Stop the system
function stopSystem() {
    fetch('/api/system/stop', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('System stop response:', data);
        if (data.status === 'System stopped successfully') {
            updateSystemStatus(false);
            showAlert('System stopped successfully', 'success');
        } else {
            showAlert('Error stopping system: ' + data.status, 'danger');
        }
    })
    .catch(error => {
        console.error('Error stopping system:', error);
        showAlert('Error stopping system', 'danger');
    });
} 