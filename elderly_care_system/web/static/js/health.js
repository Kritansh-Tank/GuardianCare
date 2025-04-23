// Health monitoring page JavaScript

// Initialize socket connection
const socket = io();

// DOM Elements - Vital Signs
const heartRateProgress = document.getElementById("heart-rate-progress");
const heartRateValue = document.getElementById("heart-rate-value");
const bloodPressureProgress = document.getElementById(
  "blood-pressure-progress"
);
const bloodPressureValue = document.getElementById("blood-pressure-value");
const temperatureProgress = document.getElementById("temperature-progress");
const temperatureValue = document.getElementById("temperature-value");
const glucoseProgress = document.getElementById("glucose-progress");
const glucoseValue = document.getElementById("glucose-value");
const oxygenProgress = document.getElementById("oxygen-progress");
const oxygenValue = document.getElementById("oxygen-value");
const healthAlertsList = document.getElementById("health-alerts-list");
const systemStatus = document.getElementById("system-status");
const startSystemBtn = document.getElementById("startSystemBtn");
const stopSystemBtn = document.getElementById("stopSystemBtn");
const refreshHealthBtn = document.getElementById("refreshHealthBtn");

// DOM Elements - Analysis Section
const analysisLoading = document.getElementById("analysis-loading");
const analysisContent = document.getElementById("analysis-content");
const totalReadings = document.getElementById("total-readings");
const totalAlerts = document.getElementById("total-alerts");
const alertPercentage = document.getElementById("alert-percentage");
const notifiedCount = document.getElementById("notified-count");
const metricsTableBody = document.getElementById("metrics-table-body");
const refreshAnalysisBtn = document.getElementById("refreshAnalysisBtn");

// Charts
let healthChart;
let alertTypeChart;

// Initialize page
document.addEventListener("DOMContentLoaded", function () {
  initializeHealthChart();
  fetchHealthData(); // This will now load both health data and analysis
  initializeSocketListeners();
  initializeButtons();
});

// Initialize buttons
function initializeButtons() {
  // Add event listeners only if elements exist
  if (startSystemBtn) {
    startSystemBtn.addEventListener("click", startSystem);
  }

  if (stopSystemBtn) {
    stopSystemBtn.addEventListener("click", stopSystem);
  }

  if (refreshHealthBtn) {
    refreshHealthBtn.addEventListener("click", fetchHealthData);
  }

  if (refreshAnalysisBtn) {
    refreshAnalysisBtn.addEventListener("click", fetchHealthData); // Use fetchHealthData instead of fetchAnalysisData
  }
}

// Initialize health chart
function initializeHealthChart() {
  const ctx = document.getElementById("healthChart").getContext("2d");
  healthChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Heart Rate",
          data: [],
          borderColor: "rgba(255, 99, 132, 1)",
          backgroundColor: "rgba(255, 99, 132, 0.2)",
          borderWidth: 1,
          tension: 0.4,
        },
        {
          label: "Systolic BP",
          data: [],
          borderColor: "rgba(54, 162, 235, 1)",
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          borderWidth: 1,
          tension: 0.4,
        },
        {
          label: "Diastolic BP",
          data: [],
          borderColor: "rgba(75, 192, 192, 1)",
          backgroundColor: "rgba(75, 192, 192, 0.2)",
          borderWidth: 1,
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: "Vital Signs Trends",
        },
        tooltip: {
          mode: "index",
          intersect: false,
        },
      },
      scales: {
        y: {
          beginAtZero: false,
        },
      },
    },
  });
}

// Socket listeners
function initializeSocketListeners() {
  // System status
  socket.on("system_status", function (data) {
    updateSystemStatus(data.running, data.emergency_mode);
  });

  // Health updates
  socket.on("health_update", function (data) {
    updateHealthData(data);
  });

  // Alert notifications
  socket.on("alert", function (data) {
    if (data.alert_type === "health") {
      addHealthAlert(data);
    }
  });
}

// Fetch health data from API
function fetchHealthData() {
  // Show loading indicator for analysis section
  if (analysisLoading) {
    analysisLoading.classList.remove("d-none");
    if (analysisContent) {
      analysisContent.classList.add("d-none");
    }
  }

  fetch("/api/health/data")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      // Check content type to make sure it's JSON
      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error(
          `Expected JSON but got ${contentType || "unknown content type"}`
        );
      }

      return response.json();
    })
    .then((data) => {
      if (data.error) {
        console.error("Error fetching health data:", data.error);

        // Display error message in the analysis section
        if (analysisLoading && analysisContent) {
          analysisLoading.classList.add("d-none");
          analysisContent.classList.remove("d-none");
          analysisContent.innerHTML = `
                        <div class="alert alert-danger">
                            <h4 class="alert-heading">Error Loading Data</h4>
                            <p>${data.error}</p>
                            <hr>
                            <p class="mb-0">Try refreshing the page or starting the system if it's not running.</p>
                        </div>
                    `;
        }
        return;
      }

      // Update vital signs with latest readings
      updateHealthData(data);

      // Update analysis section with analysis data
      if (data.analysis) {
        updateAnalysisData(data.analysis);
      }

      // Hide loading indicator
      if (analysisLoading && analysisContent) {
        analysisLoading.classList.add("d-none");
        analysisContent.classList.remove("d-none");
      }
    })
    .catch((error) => {
      console.error("Error fetching health data:", error);

      // Display error message in the analysis section
      if (analysisLoading && analysisContent) {
        analysisLoading.classList.add("d-none");
        analysisContent.classList.remove("d-none");
        analysisContent.innerHTML = `
                    <div class="alert alert-danger">
                        <h4 class="alert-heading">Error Loading Data</h4>
                        <p>${error.message}</p>
                        <hr>
                        <p class="mb-0">Try refreshing the page or starting the system if it's not running.</p>
                        <button id="startSystemFromError" class="btn btn-primary mt-3">Start System</button>
                    </div>
                `;

        // Add event listener to the start system button
        const startSystemFromError = document.getElementById(
          "startSystemFromError"
        );
        if (startSystemFromError) {
          startSystemFromError.addEventListener("click", () => {
            startSystem();
            setTimeout(fetchHealthData, 2000);
          });
        }
      }
    });
}

// Update health data display
function updateHealthData(data) {
  const latestReadings = data.latest_readings || {};

  // Update vital signs progress bars
  if ("heartrate" in latestReadings) {
    const heartRate = latestReadings.heartrate;
    const percentage = Math.min(100, (heartRate / 200) * 100);
    updateProgressBar(
      heartRateProgress,
      heartRateValue,
      heartRate + " BPM",
      percentage
    );
  }

  if ("systolic_bp" in latestReadings && "diastolic_bp" in latestReadings) {
    const systolic = latestReadings.systolic_bp;
    const diastolic = latestReadings.diastolic_bp;
    const percentage = Math.min(100, (systolic / 200) * 100);
    updateProgressBar(
      bloodPressureProgress,
      bloodPressureValue,
      systolic + "/" + diastolic + " mmHg",
      percentage
    );
  }

  if ("temperature" in latestReadings) {
    const temp = latestReadings.temperature;
    const percentage = Math.min(100, ((temp - 35) / 5) * 100);
    updateProgressBar(
      temperatureProgress,
      temperatureValue,
      temp + "°C",
      percentage
    );
  }

  if ("blood_glucose" in latestReadings) {
    const glucose = latestReadings.blood_glucose;
    const percentage = Math.min(100, (glucose / 300) * 100);
    updateProgressBar(
      glucoseProgress,
      glucoseValue,
      glucose + " mg/dL",
      percentage
    );
  }

  if ("oxygen_level" in latestReadings) {
    const oxygen = latestReadings.oxygen_level;
    const percentage = oxygen;
    updateProgressBar(oxygenProgress, oxygenValue, oxygen + "%", percentage);
  }

  // Update alerts
  if (data.alerts && data.alerts.length > 0) {
    updateHealthAlerts(data.alerts);
  }

  // Update chart
  updateHealthChart(latestReadings);
}

// Update progress bar
function updateProgressBar(progressBar, valueElement, text, percentage) {
  progressBar.style.width = percentage + "%";
  progressBar.setAttribute("aria-valuenow", percentage);

  // Set color based on percentage
  if (percentage > 80) {
    progressBar.className = "progress-bar bg-danger";
  } else if (percentage > 60) {
    progressBar.className = "progress-bar bg-warning";
  } else {
    progressBar.className = "progress-bar bg-success";
  }

  valueElement.textContent = text;
}

// Update health alerts
function updateHealthAlerts(alerts) {
  if (alerts.length === 0) {
    healthAlertsList.innerHTML =
      '<div class="list-group-item text-center text-muted">No health alerts to display</div>';
    return;
  }

  healthAlertsList.innerHTML = "";
  alerts.forEach((alert) => {
    addHealthAlert(alert);
  });
}

// Add health alert to the list
function addHealthAlert(alert) {
  const alertItem = document.createElement("div");
  alertItem.className = "list-group-item";

  let severityClass = "text-warning";
  if (alert.severity === "high") {
    severityClass = "text-danger";
  } else if (alert.severity === "low") {
    severityClass = "text-info";
  }

  const timestamp = new Date(alert.timestamp).toLocaleString();

  alertItem.innerHTML = `
        <div class="d-flex w-100 justify-content-between">
            <h5 class="mb-1 ${severityClass}">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                ${
                  alert.metric
                    ? alert.metric.replace("_", " ").toUpperCase()
                    : "Health Alert"
                }
            </h5>
            <small>${timestamp}</small>
        </div>
        <p class="mb-1">${alert.message}</p>
        <small class="text-muted">
            ${alert.value ? "Value: " + alert.value : ""}
            ${alert.threshold ? ", Threshold: " + alert.threshold : ""}
        </small>
    `;

  // Add to the top of the list
  if (healthAlertsList.firstChild) {
    healthAlertsList.insertBefore(alertItem, healthAlertsList.firstChild);
  } else {
    healthAlertsList.appendChild(alertItem);
  }

  // Limit number of displayed alerts
  if (healthAlertsList.children.length > 10) {
    healthAlertsList.removeChild(healthAlertsList.lastChild);
  }
}

// Update health chart
function updateHealthChart(latestReadings) {
  const now = new Date().toLocaleTimeString();

  // Add new data point to the chart
  if (healthChart.data.labels.length >= 10) {
    // Remove oldest data point if we have 10 already
    healthChart.data.labels.shift();
    healthChart.data.datasets.forEach((dataset) => {
      dataset.data.shift();
    });
  }

  // Add the current time
  healthChart.data.labels.push(now);

  // Add heart rate data
  if ("heartrate" in latestReadings) {
    healthChart.data.datasets[0].data.push(latestReadings.heartrate);
  } else {
    healthChart.data.datasets[0].data.push(null);
  }

  // Add blood pressure data
  if ("systolic_bp" in latestReadings) {
    healthChart.data.datasets[1].data.push(latestReadings.systolic_bp);
  } else {
    healthChart.data.datasets[1].data.push(null);
  }

  if ("diastolic_bp" in latestReadings) {
    healthChart.data.datasets[2].data.push(latestReadings.diastolic_bp);
  } else {
    healthChart.data.datasets[2].data.push(null);
  }

  // Update the chart
  healthChart.update();
}

// Update system status display
function updateSystemStatus(isRunning, isEmergency = false) {
  if (isEmergency) {
    systemStatus.classList.remove(
      "btn-outline-secondary",
      "btn-outline-success"
    );
    systemStatus.classList.add("btn-outline-danger");
    systemStatus.querySelector(".status-indicator").className =
      "status-indicator emergency";
    systemStatus.innerHTML =
      '<span class="status-indicator emergency"></span> EMERGENCY';
  } else if (isRunning) {
    systemStatus.classList.remove(
      "btn-outline-secondary",
      "btn-outline-danger"
    );
    systemStatus.classList.add("btn-outline-success");
    systemStatus.querySelector(".status-indicator").className =
      "status-indicator active";
    systemStatus.innerHTML =
      '<span class="status-indicator active"></span> System Active';
  } else {
    systemStatus.classList.remove("btn-outline-success", "btn-outline-danger");
    systemStatus.classList.add("btn-outline-secondary");
    systemStatus.querySelector(".status-indicator").className =
      "status-indicator inactive";
    systemStatus.innerHTML =
      '<span class="status-indicator inactive"></span> System Inactive';
  }
}

// Start system
function startSystem() {
  fetch("/api/system/start", {
    method: "POST",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        console.error("Error starting system:", data.error);
        alert("Error starting system: " + data.error);
        return;
      }
      console.log("System started:", data);
      updateSystemStatus(true);
      setTimeout(fetchHealthData, 2000); // Refresh data after system starts
    })
    .catch((error) => console.error("Error starting system:", error));
}

// Stop system
function stopSystem() {
  fetch("/api/system/stop", {
    method: "POST",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        console.error("Error stopping system:", data.error);
        alert("Error stopping system: " + data.error);
        return;
      }
      console.log("System stopped:", data);
      updateSystemStatus(false);
    })
    .catch((error) => console.error("Error stopping system:", error));
}

// ANALYSIS FUNCTIONALITY

// We'll keep the existing fetchAnalysisData but update it to just call fetchHealthData
function fetchAnalysisData() {
  fetchHealthData();
}

// Update analysis data display
function updateAnalysisData(data) {
  // Ensure we have all the elements before updating
  if (!totalReadings || !totalAlerts || !alertPercentage || !notifiedCount) {
    console.error("Missing DOM elements for analysis data");
    return;
  }

  // Update summary statistics
  totalReadings.textContent = data.total_readings || 0;
  totalAlerts.textContent = data.alert_counts?.total || 0;
  alertPercentage.textContent = (data.alert_percentage || 0).toFixed(1) + "%";
  notifiedCount.textContent = data.notified_count || 0;

  // Update metrics table
  if (metricsTableBody && data.metric_stats) {
    updateMetricsTable(data.metric_stats);
  }

  // Update alert type chart
  if (data.alert_counts) {
    updateAlertTypeChart(data.alert_counts);
  }
}

// Update metrics table
function updateMetricsTable(metricStats) {
  metricsTableBody.innerHTML = "";

  for (const [metric, stats] of Object.entries(metricStats)) {
    const row = document.createElement("tr");

    // Format metric name
    const metricName = metric
      .replace("_", " ")
      .replace(/\b\w/g, (l) => l.toUpperCase());

    // Create table cells
    row.innerHTML = `
            <td>${metricName}</td>
            <td>${stats.total_readings}</td>
            <td>${stats.threshold_exceeded}</td>
            <td>${stats.percentage.toFixed(1)}%</td>
        `;

    // Add color based on percentage
    if (stats.percentage > 50) {
      row.classList.add("table-danger");
    } else if (stats.percentage > 25) {
      row.classList.add("table-warning");
    } else if (stats.percentage > 0) {
      row.classList.add("table-info");
    }

    metricsTableBody.appendChild(row);
  }
}

// Update alert type chart
function updateAlertTypeChart(alertCounts) {
  // Check if chart element exists
  const chartElement = document.getElementById("alertTypeChart");
  if (!chartElement) {
    console.error("Alert type chart element not found");
    return;
  }

  // Prepare chart data
  const labels = [];
  const data = [];
  const backgroundColor = [
    "rgba(255, 99, 132, 0.7)",
    "rgba(54, 162, 235, 0.7)",
    "rgba(255, 206, 86, 0.7)",
    "rgba(75, 192, 192, 0.7)",
    "rgba(153, 102, 255, 0.7)",
  ];

  // Add each alert type (except 'total')
  for (const [type, count] of Object.entries(alertCounts)) {
    if (type !== "total") {
      labels.push(
        type.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())
      );
      data.push(count);
    }
  }

  // Destroy existing chart if it exists
  if (alertTypeChart) {
    alertTypeChart.destroy();
  }

  // Create new chart
  const ctx = chartElement.getContext("2d");
  alertTypeChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Alerts by Type",
          data: data,
          backgroundColor: backgroundColor,
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "right",
        },
        title: {
          display: true,
          text: "Alert Distribution by Type",
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const label = context.label || "";
              const value = context.raw;
              const percentage = ((value / alertCounts.total) * 100).toFixed(1);
              return `${label}: ${value} (${percentage}%)`;
            },
          },
        },
      },
    },
  });
}
