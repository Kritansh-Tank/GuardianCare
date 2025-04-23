// Reminders page JavaScript

// Initialize socket connection
const socket = io();

// DOM Elements
const activeRemindersList = document.getElementById('active-reminders-list');
const upcomingRemindersList = document.getElementById('upcoming-reminders-list');
const reminderHistoryList = document.getElementById('reminder-history-list');
const medicationScheduleList = document.getElementById('medication-schedule-list');
const todayRemindersTable = document.getElementById('today-reminders-table');
const upcomingRemindersTable = document.getElementById('upcoming-reminders-table');
const completedRemindersTable = document.getElementById('completed-reminders-table');
const systemStatus = document.getElementById('system-status');
const startSystemBtn = document.getElementById('startSystemBtn');
const stopSystemBtn = document.getElementById('stopSystemBtn');
const refreshRemindersBtn = document.getElementById('refreshRemindersBtn');
const refreshMedicationBtn = document.getElementById('refreshMedicationBtn');

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    fetchReminders();
    fetchMedicationSchedule();
    initializeSocketListeners();
    initializeButtons();
});

// Initialize buttons
function initializeButtons() {
    if (startSystemBtn) startSystemBtn.addEventListener('click', startSystem);
    if (stopSystemBtn) stopSystemBtn.addEventListener('click', stopSystem);
    if (refreshRemindersBtn) refreshRemindersBtn.addEventListener('click', fetchReminders);
    if (refreshMedicationBtn) refreshMedicationBtn.addEventListener('click', fetchMedicationSchedule);
}

// Socket listeners
function initializeSocketListeners() {
    // System status
    socket.on('system_status', function(data) {
        updateSystemStatus(data.running, data.emergency_mode);
    });

    // Reminder updates
    socket.on('reminder', function(data) {
        // New reminder received
        fetchReminders();
        
        // Show notification
        showNotification('New Reminder', data.message);
    });
}

// Fetch reminders from API
function fetchReminders() {
    fetch('/api/reminders')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching reminders:', data.error);
                return;
            }
            updateReminders(data);
        })
        .catch(error => console.error('Error fetching reminders:', error));
}

// Fetch medication schedule (mock for now)
function fetchMedicationSchedule() {
    // This would be a real API call in a production system
    const mockSchedule = [
        {
            time: '08:00',
            medications: [
                { name: 'Lisinopril', dosage: '10mg', instructions: 'Take with water' },
                { name: 'Multivitamin', dosage: '1 tablet', instructions: 'Take with food' }
            ]
        },
        {
            time: '12:00',
            medications: [
                { name: 'Metformin', dosage: '500mg', instructions: 'Take with food' }
            ]
        },
        {
            time: '18:00',
            medications: [
                { name: 'Lisinopril', dosage: '10mg', instructions: 'Take with water' },
                { name: 'Metformin', dosage: '500mg', instructions: 'Take with food' }
            ]
        },
        {
            time: '21:00',
            medications: [
                { name: 'Aspirin', dosage: '81mg', instructions: 'Take with water' }
            ]
        }
    ];
    
    updateMedicationSchedule(mockSchedule);
}

// Update reminders display
function updateReminders(data) {
    // Update active reminders
    updateActiveReminders(data.active_reminders || []);
    
    // Update completed reminders
    updateCompletedReminders(data.completed_reminders || []);
    
    // For upcoming, we can use active reminders or a separate list if available
    updateUpcomingReminders(data.active_reminders || []);
}

// Update active reminders list
function updateActiveReminders(reminders) {
    // Check if we should update the table or the list view
    if (todayRemindersTable) {
        updateTodayRemindersTable(reminders);
        return;
    }
    
    if (!activeRemindersList) {
        console.warn('Active reminders list element not found');
        return;
    }
    
    if (reminders.length === 0) {
        activeRemindersList.innerHTML = '<div class="list-group-item text-center text-muted">No active reminders</div>';
        return;
    }
    
    activeRemindersList.innerHTML = '';
    reminders.forEach(reminder => {
        const reminderItem = document.createElement('div');
        reminderItem.className = 'list-group-item';
        
        // Format time
        const time = new Date(reminder.sent_at || reminder.scheduled_time).toLocaleTimeString();
        
        // Choose icon based on type
        let icon = 'bi-bell';
        let bgClass = 'bg-warning';
        
        if (reminder.type === 'Medication') {
            icon = 'bi-capsule';
            bgClass = 'bg-primary';
        } else if (reminder.type === 'Appointment') {
            icon = 'bi-calendar-event';
            bgClass = 'bg-info';
        } else if (reminder.type === 'Exercise') {
            icon = 'bi-activity';
            bgClass = 'bg-success';
        } else if (reminder.type === 'Hydration') {
            icon = 'bi-cup-straw';
            bgClass = 'bg-info';
        }
        
        reminderItem.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <span class="reminder-icon d-inline-block rounded-circle ${bgClass} text-white p-2">
                        <i class="bi ${icon} fs-5"></i>
                    </span>
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">${reminder.type} Reminder</h5>
                        <small>${time}</small>
                    </div>
                    <p class="mb-1">${reminder.message}</p>
                </div>
                <div class="ms-3">
                    <button class="btn btn-sm btn-success acknowledge-btn" data-id="${reminder.id}">
                        <i class="bi bi-check-lg"></i>
                    </button>
                </div>
            </div>
        `;
        
        activeRemindersList.appendChild(reminderItem);
        
        // Add event listener for acknowledge button
        const acknowledgeBtn = reminderItem.querySelector('.acknowledge-btn');
        if (acknowledgeBtn) {
            acknowledgeBtn.addEventListener('click', function() {
                acknowledgeReminder(reminder.id);
            });
        }
    });
}

// Update today's reminders table
function updateTodayRemindersTable(reminders) {
    if (!todayRemindersTable) {
        console.warn('Today reminders table element not found');
        return;
    }
    
    if (reminders.length === 0) {
        todayRemindersTable.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No active reminders</td></tr>';
        return;
    }
    
    todayRemindersTable.innerHTML = '';
    reminders.forEach(reminder => {
        const time = new Date(reminder.sent_at || reminder.scheduled_time).toLocaleTimeString();
        const date = new Date(reminder.sent_at || reminder.scheduled_time).toLocaleDateString();
        
        let priorityClass = 'text-warning';
        let priorityText = 'Medium';
        if (reminder.priority === 'high') {
            priorityClass = 'text-danger';
            priorityText = 'High';
        } else if (reminder.priority === 'low') {
            priorityClass = 'text-info';
            priorityText = 'Low';
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${time}</td>
            <td>${reminder.type || 'General'}</td>
            <td>${reminder.message}</td>
            <td class="${priorityClass}">${priorityText}</td>
            <td><span class="badge bg-warning">Active</span></td>
            <td>
                <button class="btn btn-sm btn-success acknowledge-btn" data-id="${reminder.id}">
                    <i class="bi bi-check-lg"></i> Acknowledge
                </button>
            </td>
        `;
        
        todayRemindersTable.appendChild(row);
        
        // Add event listener for acknowledge button
        const acknowledgeBtn = row.querySelector('.acknowledge-btn');
        if (acknowledgeBtn) {
            acknowledgeBtn.addEventListener('click', function() {
                acknowledgeReminder(reminder.id);
            });
        }
    });
}

// Update upcoming reminders list
function updateUpcomingReminders(reminders) {
    // Check if we should update the table or the list view
    if (upcomingRemindersTable) {
        updateUpcomingRemindersTable(reminders);
        return;
    }
    
    if (!upcomingRemindersList) {
        console.warn('Upcoming reminders list element not found');
        return;
    }
    
    // For demo purposes, we'll create some upcoming reminders
    // In a real app, this would come from the API
    const upcomingReminders = [
        {
            id: 'upcoming-1',
            type: 'Medication',
            scheduled_time: new Date(new Date().getTime() + 60*60*1000).toISOString(),
            message: 'Take your evening medication'
        },
        {
            id: 'upcoming-2',
            type: 'Hydration',
            scheduled_time: new Date(new Date().getTime() + 90*60*1000).toISOString(),
            message: 'Remember to drink water'
        },
        {
            id: 'upcoming-3',
            type: 'Exercise',
            scheduled_time: new Date(new Date().getTime() + 120*60*1000).toISOString(),
            message: 'Time for your evening walk'
        }
    ];
    
    if (upcomingReminders.length === 0) {
        upcomingRemindersList.innerHTML = '<div class="list-group-item text-center text-muted">No upcoming reminders</div>';
        return;
    }
    
    upcomingRemindersList.innerHTML = '';
    upcomingReminders.forEach(reminder => {
        const reminderItem = document.createElement('div');
        reminderItem.className = 'list-group-item';
        
        // Format time
        const time = new Date(reminder.scheduled_time).toLocaleTimeString();
        
        // Choose icon based on type
        let icon = 'bi-bell';
        let textClass = 'text-warning';
        
        if (reminder.type === 'Medication') {
            icon = 'bi-capsule';
            textClass = 'text-primary';
        } else if (reminder.type === 'Appointment') {
            icon = 'bi-calendar-event';
            textClass = 'text-info';
        } else if (reminder.type === 'Exercise') {
            icon = 'bi-activity';
            textClass = 'text-success';
        } else if (reminder.type === 'Hydration') {
            icon = 'bi-cup-straw';
            textClass = 'text-info';
        }
        
        reminderItem.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1 ${textClass}">
                    <i class="bi ${icon} me-2"></i>
                    ${reminder.type}
                </h6>
                <small>${time}</small>
            </div>
            <p class="mb-0 small">${reminder.message}</p>
        `;
        
        upcomingRemindersList.appendChild(reminderItem);
    });
}

// Update upcoming reminders table
function updateUpcomingRemindersTable(reminders) {
    if (!upcomingRemindersTable) {
        console.warn('Upcoming reminders table element not found');
        return;
    }
    
    // For demo purposes, we'll create some upcoming reminders
    // In a real app, this would come from the API
    const upcomingReminders = [
        {
            id: 'upcoming-1',
            type: 'Medication',
            scheduled_time: new Date(new Date().getTime() + 60*60*1000).toISOString(),
            message: 'Take your evening medication',
            priority: 'high'
        },
        {
            id: 'upcoming-2',
            type: 'Hydration',
            scheduled_time: new Date(new Date().getTime() + 90*60*1000).toISOString(),
            message: 'Remember to drink water',
            priority: 'low'
        },
        {
            id: 'upcoming-3',
            type: 'Exercise',
            scheduled_time: new Date(new Date().getTime() + 120*60*1000).toISOString(),
            message: 'Time for your evening walk',
            priority: 'medium'
        }
    ];
    
    if (upcomingReminders.length === 0) {
        upcomingRemindersTable.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No upcoming reminders</td></tr>';
        return;
    }
    
    upcomingRemindersTable.innerHTML = '';
    upcomingReminders.forEach(reminder => {
        const time = new Date(reminder.scheduled_time).toLocaleTimeString();
        const date = new Date(reminder.scheduled_time).toLocaleDateString();
        
        let priorityClass = 'text-warning';
        let priorityText = 'Medium';
        if (reminder.priority === 'high') {
            priorityClass = 'text-danger';
            priorityText = 'High';
        } else if (reminder.priority === 'low') {
            priorityClass = 'text-info';
            priorityText = 'Low';
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${date}</td>
            <td>${time}</td>
            <td>${reminder.type || 'General'}</td>
            <td>${reminder.message}</td>
            <td class="${priorityClass}">${priorityText}</td>
        `;
        
        upcomingRemindersTable.appendChild(row);
    });
}

// Update completed reminders list (history)
function updateCompletedReminders(reminders) {
    // Check if we should update the table or the list view
    if (completedRemindersTable) {
        updateCompletedRemindersTable(reminders);
        return;
    }
    
    if (!reminderHistoryList) {
        console.warn('Reminder history list element not found');
        return;
    }
    
    if (reminders.length === 0) {
        reminderHistoryList.innerHTML = '<div class="list-group-item text-center text-muted">No reminder history</div>';
        return;
    }
    
    reminderHistoryList.innerHTML = '';
    reminders.forEach(reminder => {
        const reminderItem = document.createElement('div');
        reminderItem.className = 'list-group-item';
        
        // Format timestamp
        const timestamp = new Date(reminder.sent_at).toLocaleString();
        
        // Choose icon based on type
        let icon = 'bi-bell';
        
        if (reminder.type === 'Medication') {
            icon = 'bi-capsule';
        } else if (reminder.type === 'Appointment') {
            icon = 'bi-calendar-event';
        } else if (reminder.type === 'Exercise') {
            icon = 'bi-activity';
        } else if (reminder.type === 'Hydration') {
            icon = 'bi-cup-straw';
        }
        
        reminderItem.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1 text-muted">
                    <i class="bi ${icon} me-2"></i>
                    ${reminder.type}
                </h6>
                <small>${timestamp}</small>
            </div>
            <p class="mb-0 small text-muted">${reminder.message}</p>
        `;
        
        reminderHistoryList.appendChild(reminderItem);
    });
}

// Update completed reminders table
function updateCompletedRemindersTable(reminders) {
    if (!completedRemindersTable) {
        console.warn('Completed reminders table element not found');
        return;
    }
    
    // For demo purposes, we'll create some completed reminders
    // In a real app, this would come from the API
    const completedReminders = [
        {
            id: 'completed-1',
            type: 'Medication',
            sent_at: new Date(new Date().getTime() - 3*60*60*1000).toISOString(),
            completed_at: new Date(new Date().getTime() - 3*60*60*1000 + 5*60*1000).toISOString(),
            message: 'Take your morning medication'
        },
        {
            id: 'completed-2',
            type: 'Hydration',
            sent_at: new Date(new Date().getTime() - 2*60*60*1000).toISOString(),
            completed_at: new Date(new Date().getTime() - 2*60*60*1000 + 2*60*1000).toISOString(),
            message: 'Remember to drink water'
        }
    ];
    
    if (completedReminders.length === 0) {
        completedRemindersTable.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No completed reminders</td></tr>';
        return;
    }
    
    completedRemindersTable.innerHTML = '';
    completedReminders.forEach(reminder => {
        const sentTime = new Date(reminder.sent_at).toLocaleTimeString();
        const sentDate = new Date(reminder.sent_at).toLocaleDateString();
        const completedTime = new Date(reminder.completed_at).toLocaleTimeString();
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${sentDate}</td>
            <td>${sentTime}</td>
            <td>${reminder.type || 'General'}</td>
            <td>${reminder.message}</td>
            <td>${completedTime}</td>
        `;
        
        completedRemindersTable.appendChild(row);
    });
}

// Update medication schedule list
function updateMedicationSchedule(schedule) {
    if (!medicationScheduleList) {
        console.warn('Medication schedule list element not found');
        return;
    }
    
    if (!schedule || schedule.length === 0) {
        medicationScheduleList.innerHTML = '<div class="list-group-item text-center text-muted">No medication schedule</div>';
        return;
    }
    
    medicationScheduleList.innerHTML = '';
    
    // Sort by time
    schedule.sort((a, b) => {
        return a.time.localeCompare(b.time);
    });
    
    schedule.forEach(timeSlot => {
        const scheduleItem = document.createElement('div');
        scheduleItem.className = 'list-group-item';
        
        const now = new Date();
        const [hours, minutes] = timeSlot.time.split(':');
        const slotTime = new Date();
        slotTime.setHours(parseInt(hours), parseInt(minutes), 0);
        
        const isPast = slotTime < now;
        const isNow = Math.abs(slotTime - now) < 30 * 60 * 1000; // Within 30 minutes
        
        let timeClass = 'text-primary';
        if (isPast) {
            timeClass = 'text-muted';
        } else if (isNow) {
            timeClass = 'text-success fw-bold';
        }
        
        scheduleItem.innerHTML = `
            <div class="d-flex w-100 justify-content-between mb-2">
                <h5 class="mb-1 ${timeClass}">
                    <i class="bi bi-clock me-2"></i>
                    ${timeSlot.time}
                </h5>
                <small>${isPast ? 'Past' : isNow ? 'Current' : 'Upcoming'}</small>
            </div>
        `;
        
        const medicationsList = document.createElement('ul');
        medicationsList.className = 'list-unstyled mb-0';
        
        timeSlot.medications.forEach(med => {
            const medItem = document.createElement('li');
            medItem.className = 'd-flex align-items-center mb-1';
            medItem.innerHTML = `
                <i class="bi bi-capsule me-2 text-primary"></i>
                <div>
                    <strong>${med.name}</strong> (${med.dosage})
                    <small class="d-block text-muted">${med.instructions}</small>
                </div>
            `;
            medicationsList.appendChild(medItem);
        });
        
        scheduleItem.appendChild(medicationsList);
        medicationScheduleList.appendChild(scheduleItem);
    });
}

// Acknowledge a reminder
function acknowledgeReminder(reminderId) {
    fetch('/api/acknowledge-reminder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            reminder_id: reminderId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Refresh reminders list
            fetchReminders();
        } else {
            console.error('Error acknowledging reminder:', data.message);
        }
    })
    .catch(error => console.error('Error acknowledging reminder:', error));
}

// Show browser notification
function showNotification(title, message) {
    // Check if notifications are supported
    if (!("Notification" in window)) {
        return;
    }
    
    // Check permission
    if (Notification.permission === "granted") {
        new Notification(title, { body: message });
    } else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(permission => {
            if (permission === "granted") {
                new Notification(title, { body: message });
            }
        });
    }
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
        }
    })
    .catch(error => console.error('Error starting system:', error));
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
        }
    })
    .catch(error => console.error('Error stopping system:', error));
} 