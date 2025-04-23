#!/usr/bin/env python
"""
GuardianCare - Elderly Care Multi-Agent AI System
Launch script for the web application with integrated functionality
"""
from elderly_care_system.system import ElderlyCareSystem
import os
import json
import threading
import argparse
from typing import Dict, Any, List
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import pandas as pd

# Define app name and version directly
__app_name__ = "GuardianCare"
__version__ = "1.0.0"

# Import directly from system instead of from elderly_care_system package
# You will need to adjust this import path according to your project structure
import sys
sys.path.append(".")  # Add current directory to path

# Initialize Flask application
app = Flask(__name__,
            template_folder='elderly_care_system/web/templates',
            static_folder='elderly_care_system/web/static',
            static_url_path='/static')  # Explicitly set the static URL path
app.config['SECRET_KEY'] = 'guardian-care-secret-key'
# Allow any origin for Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Debug mode for logging
app.config['DEBUG'] = True

# Global system instance
system = None
system_thread = None


class WebUIAgent:
    """Adapter class to connect the web UI with the elderly care system."""

    @staticmethod
    def send_system_message(message: str) -> None:
        """Send a message to all connected clients."""
        data = {
            'type': 'system_message',
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        socketio.emit('update', data)

    @staticmethod
    def send_health_update(data: Dict[str, Any]) -> None:
        """Send health data update to all connected clients."""
        socketio.emit('health_update', data)

    @staticmethod
    def send_safety_update(data: Dict[str, Any]) -> None:
        """Send safety data update to all connected clients."""
        socketio.emit('safety_update', data)

    @staticmethod
    def send_reminder(data: Dict[str, Any]) -> None:
        """Send reminder to all connected clients."""
        socketio.emit('reminder', data)

    @staticmethod
    def send_alert(alert_type: str, data: Dict[str, Any]) -> None:
        """Send alert to all connected clients."""
        data['alert_type'] = alert_type
        socketio.emit('alert', data)


def start_system():
    """Initialize and start the elderly care system."""
    global system, system_thread

    if system is not None:
        return {"status": "System already running"}

    try:
        # Create the system
        system = ElderlyCareSystem()

        # Connect web UI agent callbacks
        system.ui.display_callback = WebUIAgent.send_system_message
        system.health_agent.alert_callback = lambda data: WebUIAgent.send_alert(
            'health', data)
        system.safety_agent.alert_callback = lambda data: WebUIAgent.send_alert(
            'safety', data)
        system.reminder_agent.reminder_callback = WebUIAgent.send_reminder

        # Initialize health data from CSV
        try:
            # Get the current directory
            current_dir = os.getcwd()

            # Construct absolute paths for dataset files
            dataset_dir = os.path.join(
                current_dir, "Dataset", "[Usecase 4] AI for Elderly Care and Support")
            health_csv = os.path.join(dataset_dir, "health_monitoring.csv")
            safety_csv = os.path.join(dataset_dir, "safety_monitoring.csv")
            reminder_csv = os.path.join(dataset_dir, "daily_reminder.csv")

            print(f"Looking for data files in: {dataset_dir}")

            # Process health data
            if os.path.exists(health_csv):
                print(f"Preloading health data from: {health_csv}")
                # Read the CSV data
                df = pd.read_csv(health_csv)

                # Print the first few rows for debugging
                print(f"Health CSV data loaded with {len(df)} rows")
                print(f"Column names: {df.columns.tolist()}")

                # Initialize agent with data
                system.health_agent.initialize_with_data(df)

                # Process rows to get initial readings
                for i in range(min(5, len(df))):
                    data = system.health_agent.row_to_dict(df.iloc[i])
                    result = system.health_agent.process_health_data(data)

                    # Store this as the latest reading
                    system.health_agent.state["latest_readings"] = data

                    # Debug info
                    print(
                        f"Processed health row {i}, found metrics: {list(data.keys())}")
            else:
                print(f"WARNING: Health data file not found at: {health_csv}")

                # Create some dummy data for testing if the CSV load fails
                print("Creating dummy health data for testing")
                dummy_data = {
                    "heartrate": 75,
                    "systolic_bp": 120,
                    "diastolic_bp": 80,
                    "temperature": 36.5,
                    "blood_glucose": 100,
                    "oxygen_level": 98,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                system.health_agent.state["latest_readings"] = dummy_data
                system.health_agent.process_health_data(dummy_data)

            # Process safety data
            if os.path.exists(safety_csv):
                print(f"Preloading safety data from: {safety_csv}")
                # Read the CSV data
                safety_df = pd.read_csv(safety_csv)

                print(f"Safety CSV data loaded with {len(safety_df)} rows")
                print(f"Column names: {safety_df.columns.tolist()}")

                # Initialize agent with data
                system.safety_agent.initialize_with_data(safety_df)

                # Process rows to get initial readings
                for i in range(min(5, len(safety_df))):
                    data = system.safety_agent.row_to_dict(safety_df.iloc[i])
                    result = system.safety_agent.process_safety_data(data)

                    # Store this as the latest reading
                    system.safety_agent.state["latest_readings"] = data

                    # Debug info
                    print(
                        f"Processed safety row {i}, found metrics: {list(data.keys())}")
            else:
                print(f"WARNING: Safety data file not found at: {safety_csv}")

                # Create dummy safety data
                dummy_safety = {
                    "movement_detected": True,
                    "fall_detected": False,
                    "door_status": "closed",
                    "location": "living_room",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                system.safety_agent.state["latest_readings"] = dummy_safety
                system.safety_agent.process_safety_data(dummy_safety)

            # Process reminder data
            if os.path.exists(reminder_csv):
                print(f"Preloading reminder data from: {reminder_csv}")
                # Read the CSV data
                reminder_df = pd.read_csv(reminder_csv)

                print(f"Reminder CSV data loaded with {len(reminder_df)} rows")
                print(f"Column names: {reminder_df.columns.tolist()}")

                # Initialize agent with data
                system.reminder_agent.initialize_with_data(reminder_df)

                # Process rows to get initial reminders
                for i in range(min(5, len(reminder_df))):
                    data = system.reminder_agent.row_to_dict(
                        reminder_df.iloc[i])
                    result = system.reminder_agent.process_reminder(data)

                    # Debug info
                    print(f"Processed reminder row {i}, found data: {data}")
            else:
                print(
                    f"WARNING: Reminder data file not found at: {reminder_csv}")

                # Create dummy reminder data
                dummy_reminder = {
                    "reminder_type": "medication",
                    "description": "Take heart medication",
                    "time": "08:00",
                    "priority": "high",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                }
                system.reminder_agent.add_reminder(dummy_reminder)

        except Exception as e:
            import traceback
            print(f"Error preloading data: {str(e)}")
            print(traceback.format_exc())

        # Start the system in a separate thread
        system_thread = threading.Thread(target=system.start)
        system_thread.daemon = True
        system_thread.start()

        return {"status": "System started successfully"}
    except Exception as e:
        import traceback
        return {
            "status": "Error starting system",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def stop_system():
    """Stop the elderly care system."""
    global system

    if system is None:
        return {"status": "System not running"}

    try:
        system.stop()
        system = None
        return {"status": "System stopped successfully"}
    except Exception as e:
        return {"status": "Error stopping system", "error": str(e)}


@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html', app_name=__app_name__, version=__version__)


@app.route('/health')
def health_page():
    """Render the health monitoring page with integrated analysis."""
    return render_template('health.html', app_name=__app_name__)


@app.route('/safety')
def safety_page():
    """Render the safety monitoring page."""
    return render_template('safety.html', app_name=__app_name__)


@app.route('/reminders')
def reminders_page():
    """Render the reminders page."""
    return render_template('reminders.html', app_name=__app_name__)


@app.route('/settings')
def settings_page():
    """Render the settings page."""
    return render_template('settings.html', app_name=__app_name__)


@app.route('/api/system/start', methods=['POST'])
def api_start_system():
    """API endpoint to start the system."""
    result = start_system()
    return jsonify(result)


@app.route('/api/system/stop', methods=['POST'])
def api_stop_system():
    """API endpoint to stop the system."""
    result = stop_system()
    return jsonify(result)


@app.route('/api/system/status', methods=['GET'])
def api_system_status():
    """API endpoint to get system status."""
    global system

    if system is None:
        return jsonify({"status": "System not running"})

    return jsonify({
        "status": "System running",
        "emergency_mode": system.coordinator.state.get("emergency_mode", False),
        "connected_agents": list(system.coordinator.state.get("agents", {}).keys())
    })


@app.route('/api/health/data', methods=['GET'])
def api_health_data():
    """API endpoint to get the latest health data."""
    global system

    if system is None or system.health_agent is None:
        return jsonify({"error": "System not running"})

    try:
        # If there's no data yet, try loading some from the CSV
        if not system.health_agent.state.get("latest_readings"):
            # Get the path to the CSV file
            dataset_dir = "Dataset/[Usecase 4] AI for Elderly Care and Support"
            health_csv = os.path.join(dataset_dir, "health_monitoring.csv")

            if os.path.exists(health_csv):
                print(f"Loading initial health data from CSV: {health_csv}")
                # Process a few rows to get initial data
                df = pd.read_csv(health_csv)
                for i in range(min(5, len(df))):
                    data = system.health_agent.row_to_dict(df.iloc[i])
                    system.health_agent.process_health_data(data)
                    system.health_agent.state["latest_readings"] = data

        # Generate analysis data to include with the response
        health_analysis = {}
        try:
            dataset_dir = "Dataset/[Usecase 4] AI for Elderly Care and Support"
            health_csv = os.path.join(dataset_dir, "health_monitoring.csv")

            if os.path.exists(health_csv):
                health_analysis = system.health_agent.analyze_csv_data(
                    health_csv)
        except Exception as e:
            print(f"Error generating health analysis: {str(e)}")
            health_analysis = {"error": str(e)}

        return jsonify({
            "latest_readings": system.health_agent.state.get("latest_readings", {}),
            # Last 5 alerts
            "alerts": system.health_agent.state.get("alerts", [])[-5:],
            "analysis": health_analysis  # Include analysis data
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        return jsonify({
            "error": f"Error fetching health data: {str(e)}",
            "traceback": error_traceback
        })


@app.route('/api/safety/data', methods=['GET'])
def api_safety_data():
    """API endpoint to get the latest safety data."""
    global system

    if system is None or system.safety_agent is None:
        return jsonify({"error": "System not running"})

    try:
        # If there's no data yet, try loading some from the CSV
        if not system.safety_agent.state.get("latest_readings"):
            # Get the path to the CSV file
            dataset_dir = "Dataset/[Usecase 4] AI for Elderly Care and Support"
            safety_csv = os.path.join(dataset_dir, "safety_monitoring.csv")

            if os.path.exists(safety_csv):
                print(f"Loading initial safety data from CSV: {safety_csv}")
                # Process a few rows to get initial data
                df = pd.read_csv(safety_csv)
                for i in range(min(5, len(df))):
                    data = system.safety_agent.row_to_dict(df.iloc[i])
                    system.safety_agent.process_safety_data(data)
                    system.safety_agent.state["latest_readings"] = data

        return jsonify({
            "latest_readings": system.safety_agent.state.get("latest_readings", {}),
            # Last 5 alerts
            "alerts": system.safety_agent.state.get("alerts", [])[-5:],
            "status": {
                "current_location": system.safety_agent.state.get("current_location", "unknown"),
                "last_movement": system.safety_agent.state.get("last_movement_time", "unknown"),
                "door_status": system.safety_agent.state.get("door_status", "unknown"),
            }
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        return jsonify({
            "error": f"Error fetching safety data: {str(e)}",
            "traceback": error_traceback
        })


@app.route('/api/reminders', methods=['GET'])
def api_reminders():
    """API endpoint to get active reminders."""
    global system

    if system is None or system.reminder_agent is None:
        return jsonify({"error": "System not running"})

    try:
        # If there are no reminders yet, try loading some from the CSV
        if not system.reminder_agent.state.get("active_reminders"):
            # Get the path to the CSV file
            dataset_dir = "Dataset/[Usecase 4] AI for Elderly Care and Support"
            reminder_csv = os.path.join(dataset_dir, "daily_reminder.csv")

            if os.path.exists(reminder_csv):
                print(
                    f"Loading initial reminder data from CSV: {reminder_csv}")
                # Process a few rows to get initial data
                df = pd.read_csv(reminder_csv)
                for i in range(min(10, len(df))):
                    data = system.reminder_agent.row_to_dict(df.iloc[i])
                    system.reminder_agent.process_reminder(data)

        return jsonify({
            "active_reminders": system.reminder_agent.state.get("active_reminders", []),
            # Last 10 completed
            "completed_reminders": system.reminder_agent.state.get("completed_reminders", [])[-10:],
            # Next 5 upcoming
            "upcoming_reminders": system.reminder_agent.state.get("upcoming_reminders", [])[:5]
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        return jsonify({
            "error": f"Error fetching reminders: {str(e)}",
            "traceback": error_traceback
        })


@app.route('/api/acknowledge-reminder', methods=['POST'])
def api_acknowledge_reminder():
    """API endpoint to acknowledge a reminder."""
    global system

    if system is None or system.reminder_agent is None:
        return jsonify({"error": "System not running"})

    data = request.json
    reminder_id = data.get('reminder_id')

    if not reminder_id:
        return jsonify({"error": "Missing reminder_id"})

    # Find and mark the reminder as acknowledged
    result = system.reminder_agent.acknowledge_reminder(reminder_id)

    return jsonify(result)


@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """API endpoint to get system settings."""
    global system

    if system is None:
        return jsonify({"error": "System not running"})

    try:
        # Get settings from various agents
        health_settings = system.health_agent.get_settings() if system.health_agent else {}
        safety_settings = system.safety_agent.get_settings() if system.safety_agent else {}
        reminder_settings = system.reminder_agent.get_settings() if system.reminder_agent else {}

        return jsonify({
            "health": health_settings,
            "safety": safety_settings,
            "reminder": reminder_settings,
            "system": {
                "notifications_enabled": True,
                "emergency_contacts": system.coordinator.state.get("emergency_contacts", []),
                "caregiver_contact": system.coordinator.state.get("caregiver_contact", "")
            }
        })
    except Exception as e:
        return jsonify({"error": f"Error fetching settings: {str(e)}"})


@app.route('/api/settings', methods=['POST'])
def api_update_settings():
    """API endpoint to update system settings."""
    global system

    if system is None:
        return jsonify({"error": "System not running"})

    data = request.json
    try:
        # Update settings in various agents
        if "health" in data and system.health_agent:
            system.health_agent.update_settings(data["health"])

        if "safety" in data and system.safety_agent:
            system.safety_agent.update_settings(data["safety"])

        if "reminder" in data and system.reminder_agent:
            system.reminder_agent.update_settings(data["reminder"])

        if "system" in data:
            if "emergency_contacts" in data["system"]:
                system.coordinator.state["emergency_contacts"] = data["system"]["emergency_contacts"]

            if "caregiver_contact" in data["system"]:
                system.coordinator.state["caregiver_contact"] = data["system"]["caregiver_contact"]

        return jsonify({"status": "Settings updated successfully"})
    except Exception as e:
        return jsonify({"error": f"Error updating settings: {str(e)}"})


@socketio.on('connect')
def socket_connect():
    """Handle client connection to Socket.IO."""
    socketio.emit('system_status', {
        "running": system is not None,
        "emergency_mode": system.coordinator.state.get("emergency_mode", False) if system else False
    })


@socketio.on('disconnect')
def socket_disconnect():
    """Handle client disconnection from Socket.IO."""
    pass


def run_app(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask application."""
    socketio.run(app, host=host, port=port, debug=debug)


def main():
    """Main entry point for the GuardianCare application."""
    parser = argparse.ArgumentParser(
        description=f"{__app_name__} v{__version__} - Elderly Care Multi-Agent AI System")

    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='Host to run the server on (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port to run the server on (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                        help='Run in debug mode')

    args = parser.parse_args()

    # Set app debug mode based on command line argument
    app.config['DEBUG'] = args.debug

    print(f"Starting {__app_name__} v{__version__}...")
    print(f"Server will be available at http://{args.host}:{args.port}")
    print(f"Debug mode: {args.debug}")

    # Log all registered routes for debugging
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule} -> {rule.endpoint}")

    # Start system on application launch
    start_system()

    # Run the Flask application
    run_app(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
