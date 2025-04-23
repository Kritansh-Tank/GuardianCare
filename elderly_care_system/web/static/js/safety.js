// Safety monitoring page JavaScript

// Initialize socket connection
const socket = io();

// DOM Elements - Status
const currentLocation = document.getElementById('current-location');
const lastMovement = document.getElementById('last-movement');
const movementStatus = document.getElementById('movement-status');
const doorStatus = document.getElementById('door-status');
const safetyAlertsList = document.getElementById('safety-alerts-list');
const systemStatus = document.getElementById('system-status');
const startSystemBtn = document.getElementById('startSystemBtn');
const stopSystemBtn = document.getElementById('stopSystemBtn');
const refreshSafetyBtn = document.getElementById('refreshSafetyBtn');

// DOM Elements - Activity Heat Map
const bedroomActivity = document.getElementById('bedroom-activity');
const bathroomActivity = document.getElementById('bathroom-activity');
const kitchenActivity = document.getElementById('kitchen-activity');
const livingRoomActivity = document.getElementById('living-room-activity');
const outsideActivity = document.getElementById('outside-activity');

const bedroomTime = document.getElementById('bedroom-time');
const bathroomTime = document.getElementById('bathroom-time');
const kitchenTime = document.getElementById('kitchen-time');
const livingRoomTime = document.getElementById('living-room-time');
const outsideTime = document.getElementById('outside-time');

// DOM Elements - Time Period Buttons
const todayBtn = document.getElementById('todayBtn');
const weekBtn = document.getElementById('weekBtn');
const monthBtn = document.getElementById('monthBtn');

// DOM Elements - Timeline
const timelineContainer = document.querySelector('.timeline');
const timelineItemTemplate = document.getElementById('timeline-item-template');
const emptyTimeline = document.getElementById('empty-timeline');

// Activity data storage
let activityData = {
    today: {
        bedroom: 0,
        bathroom: 0,
        kitchen: 0,
        livingRoom: 0,
        outside: 0
    },
    week: {
        bedroom: 0,
        bathroom: 0,
        kitchen: 0,
        livingRoom: 0,
        outside: 0
    },
    month: {
        bedroom: 0,
        bathroom: 0,
        kitchen: 0,
        livingRoom: 0,
        outside: 0
    }
};

// Timeline events storage
let timelineEvents = [];

// Current time period selection
let currentTimePeriod = 'today';

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    fetchSafetyData();
    initializeSocketListeners();
    initializeButtons();
    
    // Initial system status check
    checkSystemStatus();
});

// Initialize buttons
function initializeButtons() {
    if (startSystemBtn) {
        startSystemBtn.addEventListener('click', startSystem);
    }
    
    if (stopSystemBtn) {
        stopSystemBtn.addEventListener('click', stopSystem);
    }
    
    if (refreshSafetyBtn) {
        refreshSafetyBtn.addEventListener('click', fetchSafetyData);
    }
    
    // Initialize clear alerts button
    const clearAlertsBtn = document.getElementById('clearAlertsBtn');
    if (clearAlertsBtn) {
        clearAlertsBtn.addEventListener('click', clearSafetyAlerts);
    }
    
    // Initialize time period buttons
    if (todayBtn) {
        todayBtn.addEventListener('click', function() {
            setTimePeriod('today');
        });
    }
    
    if (weekBtn) {
        weekBtn.addEventListener('click', function() {
            setTimePeriod('week');
        });
    }
    
    if (monthBtn) {
        monthBtn.addEventListener('click', function() {
            setTimePeriod('month');
        });
    }
}

// Set time period for activity visualization
function setTimePeriod(period) {
    // Update current time period
    currentTimePeriod = period;
    
    // Update button states
    todayBtn.classList.remove('active');
    weekBtn.classList.remove('active');
    monthBtn.classList.remove('active');
    
    switch (period) {
        case 'today':
            todayBtn.classList.add('active');
            break;
        case 'week':
            weekBtn.classList.add('active');
            break;
        case 'month':
            monthBtn.classList.add('active');
            break;
    }
    
    // Update the visualization
    updateActivityVisualization();
}

// Socket listeners
function initializeSocketListeners() {
    // System status
    socket.on('system_status', function(data) {
        updateSystemStatus(data.running, data.emergency_mode);
    });

    // Safety updates
    socket.on('safety_update', function(data) {
        updateSafetyData(data);
    });

    // Alert notifications
    socket.on('alert', function(data) {
        if (data.alert_type === 'safety') {
            addSafetyAlert(data);
        }
    });
    
    // Connection events
    socket.on('connect', function() {
        console.log('Safety page socket connected to server');
        checkSystemStatus();
    });
    
    socket.on('disconnect', function() {
        console.log('Safety page socket disconnected from server');
        updateSystemStatus(false, false);
    });
}

// Check system status via API
function checkSystemStatus() {
    fetch('/api/system/status')
        .then(response => response.json())
        .then(data => {
            const isRunning = data.status === "System running";
            const isEmergency = data.emergency_mode === true;
            updateSystemStatus(isRunning, isEmergency);
        })
        .catch(error => {
            console.error('Error fetching system status:', error);
            updateSystemStatus(false, false);
        });
}

// Fetch safety data from API
function fetchSafetyData() {
    fetch('/api/safety/data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('Error fetching safety data:', data.error);
                return;
            }
            
            // Process and update with the data
            updateSafetyData(data);
            
            // Generate sample data for visualization if no location data is provided
            if (!data.location_data) {
                generateSampleActivityData();
            } else {
                processLocationData(data.location_data);
            }
        })
        .catch(error => {
            console.error('Error fetching safety data:', error);
            // Generate sample data for demonstration
            generateSampleActivityData();
        });
}

// Generate sample activity data for demonstration
function generateSampleActivityData() {
    // Sample data for today
    activityData.today = {
        bedroom: Math.floor(Math.random() * 6), // 0-5 hours
        bathroom: Math.floor(Math.random() * 2), // 0-1 hours
        kitchen: Math.floor(Math.random() * 3), // 0-2 hours
        livingRoom: Math.floor(Math.random() * 8), // 0-7 hours
        outside: Math.floor(Math.random() * 4) // 0-3 hours
    };
    
    // Sample data for week (roughly 7x today)
    activityData.week = {
        bedroom: activityData.today.bedroom * 7 + Math.floor(Math.random() * 10),
        bathroom: activityData.today.bathroom * 7 + Math.floor(Math.random() * 5),
        kitchen: activityData.today.kitchen * 7 + Math.floor(Math.random() * 8),
        livingRoom: activityData.today.livingRoom * 7 + Math.floor(Math.random() * 15),
        outside: activityData.today.outside * 7 + Math.floor(Math.random() * 10)
    };
    
    // Sample data for month (roughly 30x today)
    activityData.month = {
        bedroom: activityData.today.bedroom * 30 + Math.floor(Math.random() * 25),
        bathroom: activityData.today.bathroom * 30 + Math.floor(Math.random() * 15),
        kitchen: activityData.today.kitchen * 30 + Math.floor(Math.random() * 20),
        livingRoom: activityData.today.livingRoom * 30 + Math.floor(Math.random() * 40),
        outside: activityData.today.outside * 30 + Math.floor(Math.random() * 30)
    };
    
    // Update visualization with this data
    updateActivityVisualization();
    
    // Generate sample timeline events
    generateSampleTimelineEvents();
}

// Process real location data if provided by the API
function processLocationData(locationData) {
    // Reset activity data
    activityData = {
        today: { bedroom: 0, bathroom: 0, kitchen: 0, livingRoom: 0, outside: 0 },
        week: { bedroom: 0, bathroom: 0, kitchen: 0, livingRoom: 0, outside: 0 },
        month: { bedroom: 0, bathroom: 0, kitchen: 0, livingRoom: 0, outside: 0 }
    };
    
    // Process each location entry
    locationData.forEach(entry => {
        const location = entry.location.toLowerCase().replace(' ', '');
        const duration = entry.duration || 1; // Duration in hours
        const date = new Date(entry.timestamp);
        const now = new Date();
        
        // Check if entry is from today
        if (isToday(date)) {
            activityData.today[location] += duration;
        }
        
        // Check if entry is from this week
        if (isThisWeek(date)) {
            activityData.week[location] += duration;
        }
        
        // Check if entry is from this month
        if (isThisMonth(date)) {
            activityData.month[location] += duration;
        }
    });
    
    // Update visualization
    updateActivityVisualization();
}

// Generate sample timeline events
function generateSampleTimelineEvents() {
    // Clear existing events
    timelineEvents = [];
    
    // Create a few sample events for today
    const now = new Date();
    
    // Morning routine
    timelineEvents.push({
        time: new Date(now.setHours(8, 15, 0, 0)),
        title: 'Movement Detected',
        description: 'Morning activity in Bedroom',
        type: 'movement'
    });
    
    // Breakfast
    timelineEvents.push({
        time: new Date(now.setHours(9, 0, 0, 0)),
        title: 'Location Change',
        description: 'Moved to Kitchen, likely breakfast time',
        type: 'location'
    });
    
    // Living room
    timelineEvents.push({
        time: new Date(now.setHours(11, 30, 0, 0)),
        title: 'Sustained Activity',
        description: 'Active movement in Living Room',
        type: 'activity'
    });
    
    // Lunch
    timelineEvents.push({
        time: new Date(now.setHours(13, 0, 0, 0)),
        title: 'Location Change',
        description: 'Moved to Kitchen, likely lunch time',
        type: 'location'
    });
    
    // Outside
    timelineEvents.push({
        time: new Date(now.setHours(15, 45, 0, 0)),
        title: 'Door Opened',
        description: 'Front door opened, likely went outside',
        type: 'door'
    });
    
    // Back home
    timelineEvents.push({
        time: new Date(now.setHours(17, 30, 0, 0)),
        title: 'Door Opened',
        description: 'Front door opened, returned home',
        type: 'door'
    });
    
    // Update timeline visualization
    updateTimelineVisualization();
}

// Update safety data display
function updateSafetyData(data) {
    const latestReadings = data.latest_readings || {};
    
    // Update current location if available
    if ('location' in latestReadings && currentLocation) {
        currentLocation.textContent = latestReadings.location || 'Unknown';
    }
    
    // Update last movement time if available
    if ('last_movement_time' in latestReadings && lastMovement) {
        if (latestReadings.last_movement_time) {
            const movementTime = new Date(latestReadings.last_movement_time);
            lastMovement.textContent = movementTime.toLocaleTimeString();
        } else {
            lastMovement.textContent = 'Unknown';
        }
    }
    
    // Update movement status
    if ('movement_status' in latestReadings && movementStatus) {
        const status = latestReadings.movement_status || 'Unknown';
        let badgeClass = 'bg-secondary';
        
        // Set appropriate badge color based on status
        switch(status.toLowerCase()) {
            case 'active':
                badgeClass = 'bg-success';
                break;
            case 'moderate':
                badgeClass = 'bg-info';
                break;
            case 'low':
                badgeClass = 'bg-warning';
                break;
            case 'no movement':
                badgeClass = 'bg-danger';
                break;
        }
        
        movementStatus.innerHTML = `<span class="badge ${badgeClass}">${status}</span>`;
    }
    
    // Update door status
    if ('door_status' in latestReadings && doorStatus) {
        const status = latestReadings.door_status || 'Unknown';
        let badgeClass = 'bg-secondary';
        
        // Set appropriate badge color based on status
        switch(status.toLowerCase()) {
            case 'closed':
                badgeClass = 'bg-success';
                break;
            case 'open':
                badgeClass = 'bg-danger';
                break;
            case 'ajar':
                badgeClass = 'bg-warning';
                break;
        }
        
        doorStatus.innerHTML = `<span class="badge ${badgeClass}">${status}</span>`;
    }
    
    // Update alerts if available
    if (data.alerts && data.alerts.length > 0) {
        updateSafetyAlerts(data.alerts);
    }
    
    // Add an entry to the timeline if there's relevant activity
    if (latestReadings.timestamp && (latestReadings.movement_status || latestReadings.location)) {
        // Create a timeline event
        const event = {
            time: new Date(latestReadings.timestamp),
            title: latestReadings.movement_status ? 'Movement Update' : 'Location Update',
            description: latestReadings.movement_status 
                ? `Movement status: ${latestReadings.movement_status}` 
                : `Location changed to: ${latestReadings.location}`,
            type: latestReadings.movement_status ? 'movement' : 'location'
        };
        
        // Add to timeline events
        timelineEvents.push(event);
        
        // Update the timeline
        updateTimelineVisualization();
    }
}

// Update activity visualization based on the current time period
function updateActivityVisualization() {
    const data = activityData[currentTimePeriod];
    
    // Calculate the maximum value for scaling
    const maxValue = Math.max(
        data.bedroom || 0,
        data.bathroom || 0, 
        data.kitchen || 0, 
        data.livingRoom || 0, 
        data.outside || 0,
        1 // Minimum value to avoid division by zero
    );
    
    // Update activity indicators
    if (bedroomActivity) {
        const percentage = (data.bedroom / maxValue) * 100;
        bedroomActivity.querySelector('.activity-level').style.height = `${percentage}%`;
        bedroomTime.textContent = formatHours(data.bedroom);
    }
    
    if (bathroomActivity) {
        const percentage = (data.bathroom / maxValue) * 100;
        bathroomActivity.querySelector('.activity-level').style.height = `${percentage}%`;
        bathroomTime.textContent = formatHours(data.bathroom);
    }
    
    if (kitchenActivity) {
        const percentage = (data.kitchen / maxValue) * 100;
        kitchenActivity.querySelector('.activity-level').style.height = `${percentage}%`;
        kitchenTime.textContent = formatHours(data.kitchen);
    }
    
    if (livingRoomActivity) {
        const percentage = (data.livingRoom / maxValue) * 100;
        livingRoomActivity.querySelector('.activity-level').style.height = `${percentage}%`;
        livingRoomTime.textContent = formatHours(data.livingRoom);
    }
    
    if (outsideActivity) {
        const percentage = (data.outside / maxValue) * 100;
        outsideActivity.querySelector('.activity-level').style.height = `${percentage}%`;
        outsideTime.textContent = formatHours(data.outside);
    }
}

// Update timeline visualization with current events
function updateTimelineVisualization() {
    if (!timelineContainer || !timelineItemTemplate) return;
    
    // Clear existing timeline items (except template)
    const existingItems = timelineContainer.querySelectorAll('.timeline-item:not(#timeline-item-template)');
    existingItems.forEach(item => item.remove());
    
    // Hide or show the empty timeline message
    if (timelineEvents.length === 0) {
        if (emptyTimeline) emptyTimeline.style.display = 'block';
        return;
    } else {
        if (emptyTimeline) emptyTimeline.style.display = 'none';
    }
    
    // Sort events by time (newest first)
    const sortedEvents = [...timelineEvents].sort((a, b) => b.time - a.time);
    
    // Add events to the timeline
    sortedEvents.forEach(event => {
        // Clone the template
        const timelineItem = timelineItemTemplate.cloneNode(true);
        timelineItem.removeAttribute('id');
        timelineItem.style.display = '';
        
        // Set the content
        const title = timelineItem.querySelector('.timeline-title');
        const description = timelineItem.querySelector('p');
        const marker = timelineItem.querySelector('.timeline-marker');
        
        if (title) title.textContent = `${formatTime(event.time)} - ${event.title}`;
        if (description) description.textContent = event.description;
        
        // Style based on event type
        if (marker) {
            switch (event.type) {
                case 'movement':
                    marker.style.backgroundColor = '#fd7e14'; // Orange
                    break;
                case 'location':
                    marker.style.backgroundColor = '#0dcaf0'; // Cyan
                    break;
                case 'activity':
                    marker.style.backgroundColor = '#198754'; // Green
                    break;
                case 'door':
                    marker.style.backgroundColor = '#dc3545'; // Red
                    break;
                default:
                    marker.style.backgroundColor = '#0d6efd'; // Blue
            }
        }
        
        // Add to timeline
        timelineContainer.appendChild(timelineItem);
    });
}

// Update safety alerts
function updateSafetyAlerts(alerts) {
    if (!safetyAlertsList) return;
    
    if (alerts.length === 0) {
        safetyAlertsList.innerHTML = '<div class="list-group-item text-center text-muted">No safety alerts to display</div>';
        return;
    }
    
    // Clear existing alerts
    safetyAlertsList.innerHTML = '';
    
    // Add alerts in reverse order (newest first)
    alerts.slice().reverse().forEach(alert => {
        addSafetyAlert(alert);
    });
}

// Update the addSafetyAlert function to add animation effect for new alerts
function addSafetyAlert(alert) {
    if (!safetyAlertsList) return;
    
    // If there's a placeholder, remove it
    const placeholder = safetyAlertsList.querySelector('.text-center.text-muted');
    if (placeholder) {
        safetyAlertsList.removeChild(placeholder);
    }
    
    // Create alert element
    const alertElement = document.createElement('div');
    alertElement.className = 'list-group-item list-group-item-action';
    
    // Determine severity class and icon
    let severityClass = 'list-group-item-warning';
    let icon = 'exclamation-triangle';
    let severity = alert.severity || 'medium';
    
    if (alert.alert_type === 'door') {
        icon = 'door-open';
    } else if (alert.alert_type === 'movement') {
        icon = 'person-walking';
    } else if (alert.alert_type === 'fall') {
        icon = 'person-falling';
        severity = 'high';
    } else if (alert.alert_type === 'location') {
        icon = 'geo-alt';
    } else if (alert.alert_type === 'inactivity') {
        icon = 'hourglass-split';
    }
    
    // Set color based on severity
    switch(severity.toLowerCase()) {
        case 'high':
            severityClass = 'list-group-item-danger';
            break;
        case 'medium':
            severityClass = 'list-group-item-warning';
            break;
        case 'low':
            severityClass = 'list-group-item-info';
            break;
    }
    
    // Apply the severity class
    alertElement.className += ` ${severityClass}`;
    
    // Add 'new-alert' class for animation if it's a high severity alert
    if (severity.toLowerCase() === 'high') {
        alertElement.classList.add('new-alert');
        
        // Remove the animation class after 10 seconds
        setTimeout(() => {
            alertElement.classList.remove('new-alert');
        }, 10000);
    }
    
    // Format timestamp
    let timestamp = new Date();
    if (alert.timestamp) {
        timestamp = new Date(alert.timestamp);
    }
    const formattedTime = timestamp.toLocaleTimeString();
    const formattedDate = timestamp.toLocaleDateString();
    
    // Format location if available
    const locationInfo = alert.location ? `<span class="badge bg-secondary me-1"><i class="bi bi-geo-alt me-1"></i>${alert.location}</span>` : '';
    
    // Format status if available
    const statusInfo = alert.status ? `<span class="badge ${
        alert.status.toLowerCase() === 'active' ? 'bg-success' : 
        alert.status.toLowerCase() === 'resolved' ? 'bg-secondary' : 'bg-warning'
    } me-1">${alert.status}</span>` : '';
    
    // Set content
    alertElement.innerHTML = `
        <div class="d-flex w-100 justify-content-between">
            <h5 class="mb-1"><i class="bi bi-${icon} me-2"></i> ${alert.message || 'Safety Alert'}</h5>
            <small>${formattedTime}</small>
        </div>
        <p class="mb-1">${alert.details || 'No additional details available.'}</p>
        <div class="mt-2">
            ${locationInfo}
            ${statusInfo}
            <span class="badge bg-dark me-1"><i class="bi bi-calendar me-1"></i>${formattedDate}</span>
            ${alert.duration ? `<span class="badge bg-primary"><i class="bi bi-stopwatch me-1"></i>${alert.duration}</span>` : ''}
        </div>
        ${alert.action ? `<div class="mt-2 small text-muted"><i class="bi bi-info-circle me-1"></i> ${alert.action}</div>` : ''}
    `;
    
    // Add to list
    safetyAlertsList.prepend(alertElement);
    
    // Limit to 10 alerts
    while (safetyAlertsList.children.length > 10) {
        safetyAlertsList.removeChild(safetyAlertsList.lastChild);
    }
    
    // If this is a new high-severity alert, trigger notification
    if (severity.toLowerCase() === 'high' && alertElement.classList.contains('list-group-item-danger')) {
        showSafetyNotification(alert);
    }
}

// Add notification functionality for safety alerts
function showSafetyNotification(alert) {
    // Check if notifications are supported
    if (!("Notification" in window)) {
        console.warn("This browser does not support desktop notifications");
        return;
    }
    
    // Check if permission is already granted
    if (Notification.permission === "granted") {
        createNotification(alert);
    }
    // Otherwise, request permission
    else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(function (permission) {
            if (permission === "granted") {
                createNotification(alert);
            }
        });
    }
}

// Create and show a notification
function createNotification(alert) {
    const title = alert.message || "Safety Alert";
    const options = {
        body: alert.details || "A safety concern has been detected.",
        icon: "/static/img/alert-icon.png", // You may need to add this icon
        tag: "safety-alert",
        requireInteraction: true
    };
    
    const notification = new Notification(title, options);
    
    notification.onclick = function() {
        window.focus();
        notification.close();
    };
}

// Generate sample alerts for demonstration
function generateSampleSafetyAlerts() {
    // Clear any existing alerts
    if (safetyAlertsList) {
        safetyAlertsList.innerHTML = '';
    }
    
    // Current time to base alert times on
    const now = new Date();
    
    // Sample alerts with different types and severities
    const sampleAlerts = [
        {
            message: "Fall Detected",
            details: "Possible fall detected in the bathroom with high impact force.",
            alert_type: "fall",
            severity: "high",
            timestamp: new Date(now.getTime() - 15 * 60000), // 15 minutes ago
            location: "Bathroom",
            status: "Active",
            action: "Emergency contacts notified. Awaiting confirmation of wellbeing."
        },
        {
            message: "Extended Inactivity",
            details: "No movement detected for over 4 hours during daytime.",
            alert_type: "inactivity",
            severity: "medium",
            timestamp: new Date(now.getTime() - 240 * 60000), // 4 hours ago
            location: "Living Room",
            status: "Resolved",
            duration: "4h 12m",
            action: "Movement detected at 3:45 PM. Alert automatically resolved."
        },
        {
            message: "Door Left Open",
            details: "Front door has been left open for an extended period.",
            alert_type: "door",
            severity: "medium",
            timestamp: new Date(now.getTime() - 45 * 60000), // 45 minutes ago
            location: "Front Entry",
            status: "Active",
            duration: "45m",
            action: "Please close the door or verify if someone is currently entering/exiting."
        },
        {
            message: "Unusual Activity Pattern",
            details: "Activity pattern deviates significantly from normal routine.",
            alert_type: "movement",
            severity: "low",
            timestamp: new Date(now.getTime() - 120 * 60000), // 2 hours ago
            location: "Bedroom",
            status: "Monitoring",
            action: "System will continue monitoring. Alert will auto-resolve after normal activity patterns resume."
        },
        {
            message: "Prolonged Bathroom Visit",
            details: "Unusual duration spent in bathroom.",
            alert_type: "location",
            severity: "medium",
            timestamp: new Date(now.getTime() - 90 * 60000), // 90 minutes ago
            location: "Bathroom",
            status: "Resolved",
            duration: "32m",
            action: "Duration exceeded typical bathroom visits. Normal movement detected afterward."
        }
    ];
    
    // Add each sample alert
    sampleAlerts.forEach(alert => {
        addSafetyAlert(alert);
    });
}

// Modify fetchSafetyData to include sample alerts when no real data is available
const originalFetchSafetyData = fetchSafetyData;
fetchSafetyData = function() {
    originalFetchSafetyData();
    
    // After a short delay, generate sample alerts if there are none
    setTimeout(() => {
        if (safetyAlertsList && safetyAlertsList.children.length <= 1 && 
            safetyAlertsList.textContent.includes('No safety alerts')) {
            generateSampleSafetyAlerts();
        }
    }, 1000);
}

// Function to update system status display
function updateSystemStatus(isRunning, isEmergency = false) {
    if (!systemStatus) return;
    
    const statusIndicator = systemStatus.querySelector('.status-indicator');
    
    if (isEmergency) {
        systemStatus.classList.remove('btn-outline-secondary', 'btn-outline-success');
        systemStatus.classList.add('btn-outline-danger');
        if (statusIndicator) {
            statusIndicator.className = 'status-indicator emergency';
        }
        systemStatus.innerHTML = '<span class="status-indicator emergency"></span> EMERGENCY';
    } else if (isRunning) {
        systemStatus.classList.remove('btn-outline-secondary', 'btn-outline-danger');
        systemStatus.classList.add('btn-outline-success');
        if (statusIndicator) {
            statusIndicator.className = 'status-indicator active';
        }
        systemStatus.innerHTML = '<span class="status-indicator active"></span> System Active';
    } else {
        systemStatus.classList.remove('btn-outline-success', 'btn-outline-danger');
        systemStatus.classList.add('btn-outline-secondary');
        if (statusIndicator) {
            statusIndicator.className = 'status-indicator inactive';
        }
        systemStatus.innerHTML = '<span class="status-indicator inactive"></span> System Inactive';
    }
    
    // Update button states
    if (startSystemBtn && stopSystemBtn) {
        startSystemBtn.disabled = isRunning;
        stopSystemBtn.disabled = !isRunning;
    }
}

// Start the system
function startSystem() {
    fetch('/api/system/start', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateSystemStatus(true);
            // Show success message
            alert('System started successfully.');
            // Fetch new data
            setTimeout(fetchSafetyData, 2000);
        } else {
            alert('Error starting system: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error starting system:', error);
        alert('Error starting system. Check console for details.');
    });
}

// Stop the system
function stopSystem() {
    fetch('/api/system/stop', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateSystemStatus(false);
            // Show success message
            alert('System stopped successfully.');
        } else {
            alert('Error stopping system: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error stopping system:', error);
        alert('Error stopping system. Check console for details.');
    });
}

// Helper function: Format hours for display
function formatHours(hours) {
    if (hours === 0) return '0 hrs';
    if (hours < 1) {
        const minutes = Math.round(hours * 60);
        return `${minutes} mins`;
    }
    return `${hours.toFixed(1)} hrs`;
}

// Helper function: Format time for timeline
function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Helper function: Check if a date is today
function isToday(date) {
    const today = new Date();
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
}

// Helper function: Check if a date is in this week
function isThisWeek(date) {
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - now.getDay()); // Start of week (Sunday)
    startOfWeek.setHours(0, 0, 0, 0);
    
    return date >= startOfWeek;
}

// Helper function: Check if a date is in this month
function isThisMonth(date) {
    const now = new Date();
    return date.getMonth() === now.getMonth() &&
           date.getFullYear() === now.getFullYear();
}

// Function to clear all safety alerts
function clearSafetyAlerts() {
    if (safetyAlertsList) {
        safetyAlertsList.innerHTML = '<div class="list-group-item text-center text-muted">No safety alerts to display</div>';
    }
} 