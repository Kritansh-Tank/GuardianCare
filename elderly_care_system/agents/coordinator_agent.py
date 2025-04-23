"""
Coordinator Agent for Elderly Care System.
Manages communication between all specialized agents and coordinates their actions.
Serves as a central hub for system-wide decisions and information sharing.
"""
from typing import Dict, Any, List, Optional, Type
import pandas as pd
import datetime

from elderly_care_system.agents.base_agent import Agent
from elderly_care_system.agents.health_monitoring_agent import HealthMonitoringAgent
from elderly_care_system.agents.safety_monitoring_agent import SafetyMonitoringAgent
from elderly_care_system.agents.reminder_agent import ReminderAgent


class CoordinatorAgent(Agent):
    """
    Agent responsible for coordinating all other agents in the system.
    Acts as a central hub for communication and decision-making.
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "Coordinator Agent"):
        """
        Initialize the coordinator agent.
        
        Args:
            agent_id: Optional unique identifier for the agent.
            name: Name of the agent for display purposes.
        """
        super().__init__(agent_id, name)
        
        # Initialize state
        self.state = {
            "agents": {},
            "alerts": [],
            "status_updates": [],
            "emergency_mode": False
        }
        
        # Initialize specialized agents
        self.initialize_agents()
    
    def initialize_agents(self) -> None:
        """Initialize and connect all specialized agents."""
        # Create agents
        self.health_agent = HealthMonitoringAgent()
        self.safety_agent = SafetyMonitoringAgent()
        self.reminder_agent = ReminderAgent()
        
        # Add agents to state
        self.state["agents"] = {
            "health": self.health_agent,
            "safety": self.safety_agent,
            "reminder": self.reminder_agent
        }
        
        # Connect all agents to the coordinator (and vice versa)
        for agent_type, agent in self.state["agents"].items():
            self.connect_to_agent(agent)
            agent.connect_to_agent(self)
        
        # Connect agents to each other for direct communication when needed
        self.health_agent.connect_to_agent(self.safety_agent)
        self.safety_agent.connect_to_agent(self.health_agent)
        self.health_agent.connect_to_agent(self.reminder_agent)
        self.reminder_agent.connect_to_agent(self.health_agent)
        self.safety_agent.connect_to_agent(self.reminder_agent)
        self.reminder_agent.connect_to_agent(self.safety_agent)
    
    def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle received messages from other agents.
        
        Args:
            message: The message to handle.
        """
        message_type = message.get("type", "")
        
        # Log all received messages
        self.log_message(message)
        
        # Handle different message types
        if message_type == "health_alert":
            self.handle_health_alert(message)
            
        elif message_type == "safety_alert":
            self.handle_safety_alert(message)
            
        elif message_type == "reminder":
            self.handle_reminder(message)
            
        elif message_type == "status_update":
            self.handle_status_update(message)
            
        elif message_type == "request_status":
            # Someone is requesting the system status
            if "sender_id" in message:
                self.send_system_status(message["sender_id"])
    
    def log_message(self, message: Dict[str, Any]) -> None:
        """
        Log a received message for record-keeping.
        
        Args:
            message: The message to log.
        """
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add to status updates
        self.state["status_updates"].append(message)
        
        # Keep only the last 1000 status updates
        if len(self.state["status_updates"]) > 1000:
            self.state["status_updates"] = self.state["status_updates"][-1000:]
    
    def handle_health_alert(self, alert: Dict[str, Any]) -> None:
        """
        Handle health alerts from the health monitoring agent.
        
        Args:
            alert: The health alert message.
        """
        # Add to alerts
        self.state["alerts"].append(alert)
        
        # Check severity and decide on emergency mode
        alert_messages = alert.get("alert_messages", [])
        for message in alert_messages:
            if any(keyword in message.lower() for keyword in ["critical", "severe", "emergency"]):
                self.state["emergency_mode"] = True
                break
        
        # Notify external caregivers or healthcare providers (simulated)
        self.notify_external_contacts("health", alert)
    
    def handle_safety_alert(self, alert: Dict[str, Any]) -> None:
        """
        Handle safety alerts from the safety monitoring agent.
        
        Args:
            alert: The safety alert message.
        """
        # Add to alerts
        self.state["alerts"].append(alert)
        
        # Check severity and decide on emergency mode
        alert_messages = alert.get("alert_messages", [])
        for message in alert_messages:
            if any(keyword in message.lower() for keyword in ["critical", "high", "fall detected"]):
                self.state["emergency_mode"] = True
                break
        
        # Notify external caregivers or emergency services (simulated)
        self.notify_external_contacts("safety", alert)
    
    def handle_reminder(self, reminder: Dict[str, Any]) -> None:
        """
        Handle reminders from the reminder agent.
        
        Args:
            reminder: The reminder message.
        """
        # For now, just log the reminder
        # In a real system, this might trigger voice announcements, display notifications, etc.
        reminder_type = reminder.get("reminder_type", "Unknown")
        reminder_msg = reminder.get("message", "")
        
        print(f"Coordinator received {reminder_type} reminder: {reminder_msg}")
    
    def handle_status_update(self, status: Dict[str, Any]) -> None:
        """
        Handle status updates from other agents.
        
        Args:
            status: The status update message.
        """
        # Just log the status for now
        source = status.get("sender_name", "Unknown agent")
        
        print(f"Coordinator received status update from {source}")
    
    def notify_external_contacts(self, alert_type: str, alert: Dict[str, Any]) -> None:
        """
        Notify external contacts about alerts (simulated).
        
        Args:
            alert_type: Type of alert (health, safety, etc.)
            alert: The alert message.
        """
        # In a real system, this would send SMS, make calls, etc.
        # For now, just print a message
        alert_messages = ", ".join(alert.get("alert_messages", ["Unknown alert"]))
        timestamp = alert.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        print(f"[{timestamp}] EXTERNAL NOTIFICATION: {alert_type.upper()} ALERT - {alert_messages}")
    
    def send_system_status(self, recipient_id: str) -> None:
        """
        Send the current system status to a connected agent.
        
        Args:
            recipient_id: ID of the agent to send the status to.
        """
        message = {
            "type": "system_status",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "emergency_mode": self.state["emergency_mode"],
            "recent_alerts": self.state["alerts"][-5:] if self.state["alerts"] else [],
            "connected_agents": list(self.state["agents"].keys())
        }
        self.send_message(recipient_id, message)
    
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data by routing it to the appropriate specialized agent.
        
        Args:
            data: Data to process.
            
        Returns:
            Results from processing the data.
        """
        results = {}
        data_type = data.get("type", "")
        
        if data_type == "health":
            # Send to health monitoring agent
            results["health"] = self.health_agent.process_data(data.get("data", {}))
            
        elif data_type == "safety":
            # Send to safety monitoring agent
            results["safety"] = self.safety_agent.process_data(data.get("data", {}))
            
        elif data_type == "reminder":
            # Send to reminder agent
            results["reminder"] = self.reminder_agent.process_data(data.get("data", {}))
            
        else:
            # Try to determine the type automatically
            if any(key in data for key in ["Heart Rate", "Blood Pressure", "Glucose Levels"]):
                # Looks like health data
                results["health"] = self.health_agent.process_data(data)
                
            elif any(key in data for key in ["Movement Activity", "Fall Detected"]):
                # Looks like safety data
                results["safety"] = self.safety_agent.process_data(data)
                
            elif any(key in data for key in ["Reminder Type", "Scheduled Time"]):
                # Looks like reminder data
                results["reminder"] = self.reminder_agent.process_data(data)
        
        return results
    
    def process_health_data(self, csv_file: str) -> pd.DataFrame:
        """Process health monitoring data from a CSV file."""
        return self.health_agent.process_csv_data(csv_file)
    
    def process_safety_data(self, csv_file: str) -> pd.DataFrame:
        """Process safety monitoring data from a CSV file."""
        return self.safety_agent.process_csv_data(csv_file)
    
    def process_reminder_data(self, csv_file: str) -> pd.DataFrame:
        """Process reminder data from a CSV file."""
        return self.reminder_agent.process_csv_data(csv_file)
    
    def run_system(self) -> None:
        """
        Run the entire system by checking for due reminders and processing data.
        This method should be called periodically.
        """
        # Run the reminder scheduler
        sent_reminders = self.reminder_agent.run_scheduler()
        
        # Log any sent reminders
        for reminder in sent_reminders:
            self.log_message({
                "type": "reminder_sent",
                "reminder": reminder,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }) 