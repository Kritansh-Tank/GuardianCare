"""
User Interface Agent for Elderly Care System.
Handles the display of information to the elderly user and processes their inputs.
Provides a text-based interface in this implementation but could be extended to voice or GUI.
"""
from typing import Dict, Any, List, Optional, Callable
import datetime
import time

from elderly_care_system.agents.base_agent import Agent


class UserInterfaceAgent(Agent):
    """
    Agent responsible for handling user interface interactions.
    Displays information to the user and processes their inputs.
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "User Interface Agent"):
        """
        Initialize the user interface agent.
        
        Args:
            agent_id: Optional unique identifier for the agent.
            name: Name of the agent for display purposes.
        """
        super().__init__(agent_id, name)
        
        # Initialize state
        self.state = {
            "display_queue": [],
            "user_inputs": [],
            "active_reminders": [],
            "active_alerts": [],
            "acknowledged_reminders": [],
            "screen_content": ""
        }
        
        # Define display handlers
        self.display_handlers = {
            "health_alert": self.display_health_alert,
            "safety_alert": self.display_safety_alert,
            "reminder": self.display_reminder,
            "ai_response": self.display_ai_response,
            "system_status": self.display_system_status
        }
    
    def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle received messages from other agents.
        
        Args:
            message: The message to handle.
        """
        message_type = message.get("type", "")
        
        # Add to display queue
        self.state["display_queue"].append(message)
        
        # Process the display queue
        self.process_display_queue()
        
        # Handle specific message types
        if message_type == "health_alert":
            self.add_active_alert(message)
            
        elif message_type == "safety_alert":
            self.add_active_alert(message)
            
        elif message_type == "reminder":
            self.add_active_reminder(message)
            
        elif message_type == "acknowledge_reminder":
            self.acknowledge_reminder(message.get("reminder_id"))
    
    def process_display_queue(self) -> None:
        """Process messages in the display queue and display them to the user."""
        while self.state["display_queue"]:
            message = self.state["display_queue"].pop(0)
            message_type = message.get("type", "")
            
            # Call the appropriate display handler
            if message_type in self.display_handlers:
                self.display_handlers[message_type](message)
            else:
                # Default display for unknown message types
                content = f"\n--- Message from {message.get('sender_name', 'Unknown')} ---\n"
                content += f"Type: {message_type}\n"
                content += f"Content: {message}\n"
                self.display_content(content)
    
    def display_content(self, content: str) -> None:
        """
        Display content to the user.
        
        Args:
            content: Content to display.
        """
        # In a real system, this would display on a screen, speak aloud, etc.
        # For this implementation, we'll just print to the console
        print(content)
        
        # Update the screen content
        self.state["screen_content"] = content
    
    def display_health_alert(self, alert: Dict[str, Any]) -> None:
        """
        Display a health alert to the user.
        
        Args:
            alert: Health alert message.
        """
        # Extract alert messages
        alert_messages = alert.get("alert_messages", [])
        timestamp = alert.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Build the display content
        content = "\n╔════════════════ HEALTH ALERT ════════════════╗\n"
        content += f"║ Time: {timestamp}\n"
        content += "║\n"
        
        for message in alert_messages:
            content += f"║ {message}\n"
        
        content += "║\n"
        content += "║ Please acknowledge this alert or contact help if needed.\n"
        content += "╚══════════════════════════════════════════════╝\n"
        
        # Display the content
        self.display_content(content)
    
    def display_safety_alert(self, alert: Dict[str, Any]) -> None:
        """
        Display a safety alert to the user.
        
        Args:
            alert: Safety alert message.
        """
        # Extract alert messages
        alert_messages = alert.get("alert_messages", [])
        timestamp = alert.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Build the display content
        content = "\n╔════════════════ SAFETY ALERT ════════════════╗\n"
        content += f"║ Time: {timestamp}\n"
        content += "║\n"
        
        for message in alert_messages:
            content += f"║ {message}\n"
        
        content += "║\n"
        content += "║ Please acknowledge this alert or contact help if needed.\n"
        content += "╚══════════════════════════════════════════════╝\n"
        
        # Display the content
        self.display_content(content)
    
    def display_reminder(self, reminder: Dict[str, Any]) -> None:
        """
        Display a reminder to the user.
        
        Args:
            reminder: Reminder message.
        """
        # Extract reminder details
        reminder_type = reminder.get("reminder_type", "General")
        reminder_message = reminder.get("message", "")
        reminder_id = reminder.get("reminder_id", "")
        timestamp = reminder.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Build the display content
        content = f"\n╔════════════════ {reminder_type.upper()} REMINDER ════════════════╗\n"
        content += f"║ Time: {timestamp}\n"
        content += "║\n"
        content += f"║ {reminder_message}\n"
        content += "║\n"
        content += f"║ To acknowledge this reminder, say \"acknowledge reminder {reminder_id}\"\n"
        content += "╚═════════════════════════════════════════════════════╝\n"
        
        # Display the content
        self.display_content(content)
    
    def display_ai_response(self, message: Dict[str, Any]) -> None:
        """
        Display an AI response to the user.
        
        Args:
            message: AI response message.
        """
        # Extract response details
        response = message.get("response", "")
        context = message.get("context", "")
        timestamp = message.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Build the display content
        content = "\n╔════════════════ MESSAGE FROM CARE COMPANION ════════════════╗\n"
        content += f"║ Time: {timestamp}\n"
        content += "║\n"
        
        # Split response into lines and add them to content
        for line in response.split('\n'):
            wrapped_lines = [line[i:i+60] for i in range(0, len(line), 60)]
            for wrapped in wrapped_lines:
                content += f"║ {wrapped}\n"
        
        content += "╚═══════════════════════════════════════════════════════════╝\n"
        
        # Display the content
        self.display_content(content)
    
    def display_system_status(self, status: Dict[str, Any]) -> None:
        """
        Display system status to the user.
        
        Args:
            status: System status message.
        """
        # Extract status details
        emergency_mode = status.get("emergency_mode", False)
        recent_alerts = status.get("recent_alerts", [])
        connected_agents = status.get("connected_agents", [])
        timestamp = status.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Build the display content
        content = "\n╔════════════════ SYSTEM STATUS ════════════════╗\n"
        content += f"║ Time: {timestamp}\n"
        content += "║\n"
        content += f"║ Emergency Mode: {'ACTIVE' if emergency_mode else 'Inactive'}\n"
        content += "║\n"
        content += f"║ Connected Agents: {', '.join(connected_agents)}\n"
        content += "║\n"
        
        if recent_alerts:
            content += "║ Recent Alerts:\n"
            for alert in recent_alerts:
                alert_type = alert.get("type", "Unknown")
                alert_time = alert.get("timestamp", "Unknown time")
                content += f"║ - {alert_type} at {alert_time}\n"
        
        content += "╚══════════════════════════════════════════════╝\n"
        
        # Display the content
        self.display_content(content)
    
    def add_active_alert(self, alert: Dict[str, Any]) -> None:
        """
        Add an alert to the list of active alerts.
        
        Args:
            alert: Alert message.
        """
        self.state["active_alerts"].append(alert)
        
        # Keep only the most recent 10 alerts
        if len(self.state["active_alerts"]) > 10:
            self.state["active_alerts"] = self.state["active_alerts"][-10:]
    
    def add_active_reminder(self, reminder: Dict[str, Any]) -> None:
        """
        Add a reminder to the list of active reminders.
        
        Args:
            reminder: Reminder message.
        """
        self.state["active_reminders"].append(reminder)
        
        # Keep only the most recent 10 reminders
        if len(self.state["active_reminders"]) > 10:
            self.state["active_reminders"] = self.state["active_reminders"][-10:]
    
    def acknowledge_reminder(self, reminder_id: str) -> None:
        """
        Acknowledge a reminder.
        
        Args:
            reminder_id: ID of the reminder to acknowledge.
        """
        # Find the reminder in active reminders
        for i, reminder in enumerate(self.state["active_reminders"]):
            if reminder.get("reminder_id") == reminder_id:
                # Move from active to acknowledged
                self.state["acknowledged_reminders"].append(reminder)
                self.state["active_reminders"].pop(i)
                
                # Notify the reminder agent
                self.broadcast_message({
                    "type": "acknowledge_reminder",
                    "reminder_id": reminder_id,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # Display acknowledgment to user
                self.display_content(f"\nReminder {reminder_id} acknowledged. Thank you!\n")
                
                break
    
    def get_user_input(self, prompt: str = "") -> str:
        """
        Get input from the user.
        
        Args:
            prompt: Prompt to display to the user.
            
        Returns:
            User input.
        """
        # Display the prompt
        if prompt:
            self.display_content(prompt)
        
        # Get user input
        user_input = input("> ")
        
        # Add to list of user inputs
        self.state["user_inputs"].append({
            "input": user_input,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return user_input
    
    def process_user_input(self, user_input: str) -> None:
        """
        Process input from the user.
        
        Args:
            user_input: Input from the user.
        """
        # Check for commands
        if user_input.lower().startswith("acknowledge reminder"):
            # Extract the reminder ID
            parts = user_input.split()
            if len(parts) >= 3:
                reminder_id = parts[2]
                self.acknowledge_reminder(reminder_id)
        
        else:
            # Send as a user message to the AI comms agent
            self.broadcast_message({
                "type": "user_message",
                "content": user_input,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    def run_ui_loop(self, stop_event: Optional[Callable[[], bool]] = None) -> None:
        """
        Run the UI loop to continuously process user input.
        
        Args:
            stop_event: Optional callable that returns True when the loop should stop.
        """
        # Display welcome message
        self.display_content("\n╔════════════════ WELCOME TO ELDERLY CARE SYSTEM ════════════════╗\n"
                             "║                                                                 ║\n"
                             "║ This system helps monitor your health and safety, and provides  ║\n"
                             "║ reminders for medications, appointments, and activities.        ║\n"
                             "║                                                                 ║\n"
                             "║ You can type messages anytime to communicate with the system.   ║\n"
                             "║                                                                 ║\n"
                             "║ Type 'help' for assistance, or 'exit' to quit.                  ║\n"
                             "╚═════════════════════════════════════════════════════════════════╝\n")
        
        # Run the loop
        while True:
            # Check if we should stop
            if stop_event and stop_event():
                break
            
            # Get and process user input
            user_input = self.get_user_input()
            
            # Check for exit command
            if user_input.lower() == "exit":
                self.display_content("\nThank you for using the Elderly Care System. Goodbye!\n")
                break
            
            # Process the input
            self.process_user_input(user_input)
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.1)
    
    def process_data(self, data: Any) -> Any:
        """
        Process data received by the agent.
        
        Args:
            data: The data to process.
            
        Returns:
            Processed data or results.
        """
        # This agent doesn't do any standalone data processing; it handles UI
        pass