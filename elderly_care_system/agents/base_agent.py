"""
Base Agent class for the Elderly Care System.
All specialized agents will inherit from this class.
"""
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable


class Agent(ABC):
    """Base Agent class that all other agents will inherit from."""
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "Generic Agent"):
        """
        Initialize the base agent with a unique ID and name.
        
        Args:
            agent_id: Optional unique identifier for the agent. If not provided, a UUID will be generated.
            name: Name of the agent for display purposes.
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name
        self.message_queue = []
        self.connected_agents = {}
        self.state: Dict[str, Any] = {}
        
        # Initialize callback function(s)
        self.display_callback = None  # Used for displaying messages
        self.alert_callback = None  # Used for sending alerts
        self.reminder_callback = None  # Used for sending reminders
        self.status_callback = None  # Used for status updates
    
    def connect_to_agent(self, agent: 'Agent') -> None:
        """
        Connect this agent to another agent for communication.
        
        Args:
            agent: The agent to connect to.
        """
        if agent.agent_id not in self.connected_agents:
            self.connected_agents[agent.agent_id] = agent
    
    def disconnect_from_agent(self, agent_id: str) -> None:
        """
        Disconnect from a connected agent.
        
        Args:
            agent_id: ID of the agent to disconnect from.
        """
        if agent_id in self.connected_agents:
            del self.connected_agents[agent_id]
    
    def send_message(self, recipient_id: str, message: Dict[str, Any]) -> bool:
        """
        Send a message to a connected agent.
        
        Args:
            recipient_id: The ID of the recipient agent.
            message: The message to send.
            
        Returns:
            bool: True if message was sent successfully, False otherwise.
        """
        # Add sender ID and name to the message
        if "sender_id" not in message:
            message["sender_id"] = self.agent_id
        if "sender_name" not in message:
            message["sender_name"] = self.name
        
        # Send the message
        if recipient_id in self.connected_agents:
            self.connected_agents[recipient_id].handle_message(message)
            return True
        else:
            return False
    
    def broadcast_message(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected agents.
        
        Args:
            message: The message to broadcast.
        """
        # Add sender ID and name to the message
        if "sender_id" not in message:
            message["sender_id"] = self.agent_id
        if "sender_name" not in message:
            message["sender_name"] = self.name
        
        # Send the message to all connected agents
        for agent_id, agent in self.connected_agents.items():
            agent.handle_message(message)
    
    def receive_message(self, message: Dict[str, Any]) -> None:
        """
        Receive a message from another agent.
        
        Args:
            message: The received message.
        """
        self.message_queue.append(message)
        self.process_messages()
    
    def process_messages(self) -> None:
        """Process all messages in the queue."""
        while self.message_queue:
            message = self.message_queue.pop(0)
            self.handle_message(message)
    
    @abstractmethod
    def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle a received message. To be implemented by subclasses.
        
        Args:
            message: The message to handle.
        """
        pass
    
    @abstractmethod
    def process_data(self, data: Any) -> Any:
        """
        Process data received by the agent. To be implemented by subclasses.
        
        Args:
            data: The data to process.
            
        Returns:
            Processed data or results.
        """
        pass
    
    def update_state(self, state_updates: Dict[str, Any]) -> None:
        """
        Update the agent's internal state.
        
        Args:
            state_updates: Dictionary of state variables to update.
        """
        self.state.update(state_updates)
    
    def display_message(self, message: str) -> None:
        """
        Display a message to the user.
        If a display callback is set, it will be used.
        
        Args:
            message: Message to display.
        """
        if self.display_callback:
            self.display_callback(message)
        else:
            print(f"[{self.name}] {message}")
    
    def send_alert(self, alert_data: Dict[str, Any]) -> None:
        """
        Send an alert through the alert callback if available.
        
        Args:
            alert_data: Alert data to send.
        """
        if self.alert_callback:
            self.alert_callback(alert_data)
    
    def send_reminder(self, reminder_data: Dict[str, Any]) -> None:
        """
        Send a reminder through the reminder callback if available.
        
        Args:
            reminder_data: Reminder data to send.
        """
        if self.reminder_callback:
            self.reminder_callback(reminder_data)
    
    def send_status_update(self, status_data: Dict[str, Any]) -> None:
        """
        Send a status update through the status callback if available.
        
        Args:
            status_data: Status data to send.
        """
        if self.status_callback:
            self.status_callback(status_data)
    
    def register_callback(self, callback_type: str, callback: Callable) -> None:
        """
        Register a callback function of a specific type.
        
        Args:
            callback_type: Type of callback ('display', 'alert', 'reminder', 'status').
            callback: Callback function to register.
        """
        if callback_type == 'display':
            self.display_callback = callback
        elif callback_type == 'alert':
            self.alert_callback = callback
        elif callback_type == 'reminder':
            self.reminder_callback = callback
        elif callback_type == 'status':
            self.status_callback = callback 