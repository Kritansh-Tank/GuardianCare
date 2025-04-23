"""
Web Application for GuardianCare Elderly Care System.
Provides a web-based interface for interacting with the multi-agent system.
"""
import json
import threading
import os
from typing import Dict, Any, List
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

from elderly_care_system import __app_name__, __version__
from elderly_care_system.system import ElderlyCareSystem


# Initialize Flask application
app = Flask(__name__, template_folder='web/templates',
            static_folder='web/static')
app.config['SECRET_KEY'] = 'guardian-care-secret-key'
socketio = SocketIO(app)

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

        # Start the system in a separate thread
        system_thread = threading.Thread(target=system.start)
        system_thread.daemon = True
        system_thread.start()

        return {"status": "System started successfully"}
    except Exception as e:
        return {"status": "Error starting system", "error": str(e)}


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


@app.route('/health/analysis')
def health_analysis_page():
    """Render the detailed health analysis page."""
    return render_template('health_analysis.html', app_name=__app_name__)


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

    # Emit system status update to all clients
    if result.get("status") == "System started successfully":
        socketio.emit('system_status', {
            "running": True,
            "emergency_mode": system.coordinator.state.get("emergency_mode", False) if system else False
        })

    return jsonify(result)


@app.route('/api/system/stop', methods=['POST'])
def api_stop_system():
    """API endpoint to stop the system."""
    result = stop_system()

    # Emit system status update to all clients
    if result.get("status") == "System stopped successfully":
        socketio.emit('system_status', {
            "running": False,
            "emergency_mode": False
        })

    return jsonify(result)


@app.route('/api/system/status', methods=['GET'])
def api_system_status():
    """API endpoint to get system status."""
    global system

    if system is None:
        return jsonify({"status": "System not running", "emergency_mode": False})

    is_emergency = system.coordinator.state.get("emergency_mode", False)

    return jsonify({
        "status": "System running",
        "emergency_mode": is_emergency,
        "connected_agents": list(system.coordinator.state.get("agents", {}).keys())
    })


@app.route('/api/health/data', methods=['GET'])
def api_health_data():
    """API endpoint to get the latest health data."""
    global system

    if system is None or system.health_agent is None:
        return jsonify({"error": "System not running"})

    return jsonify({
        "latest_readings": system.health_agent.state.get("latest_readings", {}),
        # Last 5 alerts
        "alerts": system.health_agent.state.get("alerts", [])[-5:]
    })


@app.route('/api/health/analysis', methods=['GET'])
def api_health_analysis():
    """API endpoint to get detailed health monitoring analysis."""
    global system

    if system is None or system.health_agent is None:
        return jsonify({"error": "System not running"})

    try:
        # Get the path to the CSV file
        dataset_dir = "Dataset/[Usecase 4] AI for Elderly Care and Support"
        health_csv = os.path.join(dataset_dir, "health_monitoring.csv")

        # Generate analysis using the health monitoring agent
        analysis = system.health_agent.analyze_csv_data(health_csv)

        return jsonify(analysis)
    except Exception as e:
        return jsonify({"error": f"Error generating health analysis: {str(e)}"})


@app.route('/api/safety/data', methods=['GET'])
def api_safety_data():
    """API endpoint to get the latest safety data."""
    global system

    if system is None or system.safety_agent is None:
        return jsonify({"error": "System not running"})

    return jsonify({
        "latest_readings": system.safety_agent.state.get("latest_readings", {}),
        # Last 5 alerts
        "alerts": system.safety_agent.state.get("alerts", [])[-5:]
    })


@app.route('/api/reminders', methods=['GET'])
def api_reminders():
    """API endpoint to get active reminders."""
    global system

    if system is None or system.reminder_agent is None:
        return jsonify({"error": "System not running"})

    return jsonify({
        "active_reminders": system.reminder_agent.state.get("active_reminders", []),
        # Last 10 completed
        "completed_reminders": system.reminder_agent.state.get("completed_reminders", [])[-10:]
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


@socketio.on('connect')
def socket_connect():
    """Handle client connection to Socket.IO."""
    global system

    # Send current system status to the newly connected client
    socketio.emit('system_status', {
        "running": system is not None,
        "emergency_mode": system.coordinator.state.get("emergency_mode", False) if system else False
    }, room=request.sid)  # Send only to the connecting client


@socketio.on('disconnect')
def socket_disconnect():
    """Handle client disconnection from Socket.IO."""
    pass


def run_app(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask application."""
    socketio.run(app, host=host, port=port, debug=debug)


if __name__ == '__main__':
    # Start system on application launch
    start_system()

    # Run the Flask application
    run_app(debug=True)
