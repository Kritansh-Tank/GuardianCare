# GuardianCare: Elderly Care Multi-Agent AI System

A multi-agent AI system designed to assist elderly individuals by providing real-time monitoring, reminders, and safety alerts, while promoting health management and social engagement.

## Overview

This system uses a multi-agent approach to create a collaborative support system for elderly care, involving:

- **Health Monitoring**: Monitors vital signs such as heart rate, blood pressure, glucose levels, and oxygen saturation.
- **Safety Monitoring**: Detects falls, unusual inactivity, and tracks movement throughout the home.
- **Reminder System**: Provides timely reminders for medications, appointments, exercise, and hydration.
- **Coordination**: Manages communication between agents and provides a centralized decision-making system.
- **Web Interface**: Offers a modern, responsive dashboard for caregivers and elderly users.

## Features

- **Real-time Health Monitoring**: Detects abnormal vital signs and triggers alerts.
- **Fall Detection**: Identifies falls and triggers appropriate responses based on severity.
- **Daily Reminders**: Manages schedules for medications, appointments, and activities.
- **Multi-Agent Cooperation**: Agents share information and coordinate responses to events.
- **Modern Web Dashboard**: Clean, intuitive interface for monitoring and managing care.
- **Real-time Alerts**: Immediate notifications for critical events with visual and audio cues.
- **Mobile-Responsive Design**: Access the interface from any device (desktop, tablet, smartphone).

## System Architecture

The system consists of the following components:

- **Base Agent**: Abstract class defining common functionality for all agents.
- **Health Monitoring Agent**: Processes health data and triggers alerts for abnormal values.
- **Safety Monitoring Agent**: Monitors movement, detects falls, and identifies unusual behavior.
- **Reminder Agent**: Manages and sends reminders for various activities.
- **User Interface Agent**: Displays information to the user and processes their inputs.
- **Coordinator Agent**: Manages communication between agents and coordinates system-wide decisions.
- **Web Application**: Flask-based web interface for monitoring and interacting with the system.

## Requirements

- Python 3.8+
- pandas
- requests
- flask
- flask-socketio
- Threading support

## Usage

### Running the Web Application

To start the web application with default settings:

```bash
python run_guardiancare.py
```

This will:
1. Start the web server on http://127.0.0.1:5000
2. Initialize all agents
3. Provide access to the dashboard interface

For more options:

```bash
python run_guardiancare.py --help
```

Options include:
- `--host`: Specify the host to run on (default: 127.0.0.1)
- `--port`: Specify the port to use (default: 5000)
- `--debug`: Run in debug mode

### Using the Web Interface

The web interface provides:

1. **Dashboard**: Overview of the system with health status, safety status, and active reminders
2. **Health Monitoring**: Detailed view of health metrics with historical data
3. **Safety Monitoring**: Real-time safety status and incident reports
4. **Reminders**: Manage and acknowledge reminders
5. **Settings**: Configure system parameters

### Running the Backend Only

If you want to run just the backend system without the web interface:

```bash
python -m elderly_care_system.system
```

This will start:
1. The coordinator agent and all specialized agents
2. The console interface for basic interaction

### Dataset

The system uses three CSV files for data:

- `health_monitoring.csv`: Contains health measurements like heart rate, blood pressure, etc.
- `safety_monitoring.csv`: Contains safety data like falls, movement activity, etc.
- `daily_reminder.csv`: Contains reminders for medications, appointments, etc.

## License

This project is licensed under the MIT License - see the LICENSE file for details.