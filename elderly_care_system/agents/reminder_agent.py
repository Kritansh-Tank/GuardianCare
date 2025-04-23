"""
Reminder Agent for Elderly Care System.
Manages and sends reminders for medications, appointments, exercise, and hydration.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import datetime
import uuid
import random

from elderly_care_system.agents.base_agent import Agent


class ReminderAgent(Agent):
    """
    Agent responsible for managing and sending reminders for medications,
    appointments, exercise, and other activities.
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "Reminder Agent"):
        """
        Initialize the reminder agent.
        
        Args:
            agent_id: Optional unique identifier for the agent.
            name: Name of the agent for display purposes.
        """
        super().__init__(agent_id, name)
        
        # Initialize state
        self.state = {
            "active_reminders": [],
            "completed_reminders": [],
            "scheduled_reminders": [],
            "upcoming_reminders": []
        }
        
        # Store the full dataset
        self.data = None
        self.current_data_index = 0
        
        # Initialize reminder callback
        self.reminder_callback = None
    
    def initialize_with_data(self, data: pd.DataFrame) -> None:
        """
        Initialize the agent with data from a CSV file.
        
        Args:
            data: DataFrame containing reminder data.
        """
        self.data = data
        
        if self.data is not None and not self.data.empty:
            # Process the data to extract scheduled reminders
            self.extract_scheduled_reminders()
            
            # Find upcoming reminders for today
            self.update_upcoming_reminders()
            
            # Set the next data point to process
            self.current_data_index = 0
    
    def row_to_dict(self, row: pd.Series) -> Dict[str, Any]:
        """
        Convert a DataFrame row to a dictionary for processing.
        
        Args:
            row: A row from the reminder DataFrame.
            
        Returns:
            Dictionary with the extracted data.
        """
        data = {}
        
        # Extract the data we need
        if "Device-ID/User-ID" in row:
            data["device_id"] = row["Device-ID/User-ID"]
        
        if "Timestamp" in row:
            data["timestamp"] = row["Timestamp"]
        
        if "Reminder Type" in row:
            data["reminder_type"] = row["Reminder Type"]
        
        if "Scheduled Time" in row:
            data["time"] = row["Scheduled Time"]
        
        if "Reminder Sent (Yes/No)" in row:
            data["sent"] = row["Reminder Sent (Yes/No)"] == "Yes"
        
        if "Acknowledged (Yes/No)" in row:
            data["acknowledged"] = row["Acknowledged (Yes/No)"] == "Yes"
            
        if "Description" in row:
            data["description"] = row["Description"]
        else:
            data["description"] = self.generate_reminder_message(data.get("reminder_type", "General"))
            
        if "Priority" in row:
            data["priority"] = row["Priority"]
        else:
            data["priority"] = "medium"
            
        if "Date" in row:
            data["date"] = row["Date"]
        else:
            data["date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        
        return data
    
    def extract_scheduled_reminders(self) -> None:
        """
        Extract all scheduled reminders from the dataset.
        """
        if self.data is None or self.data.empty:
            return
        
        scheduled_reminders = []
        
        for _, row in self.data.iterrows():
            data = self.row_to_dict(row)
            
            if "reminder_type" in data and "time" in data:
                # Create a reminder object
                reminder = {
                    "id": str(uuid.uuid4()),
                    "device_id": data.get("device_id", "Unknown"),
                    "type": data.get("reminder_type", "General"),
                    "scheduled_time": data.get("time", "00:00"),
                    "message": data.get("description", self.generate_reminder_message(data.get("reminder_type", "General"))),
                    "sent": data.get("sent", False),
                    "acknowledged": data.get("acknowledged", False),
                    "created_at": data.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "priority": data.get("priority", "medium"),
                    "date": data.get("date", datetime.datetime.now().strftime("%Y-%m-%d"))
                }
                scheduled_reminders.append(reminder)
        
        self.state["scheduled_reminders"] = scheduled_reminders
    
    def update_upcoming_reminders(self) -> None:
        """
        Update the list of upcoming reminders based on the current time.
        """
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        upcoming = []
        for reminder in self.state["scheduled_reminders"]:
            # For simulation purposes, we'll pretend all reminders are for today if they don't have a date
            reminder_date = reminder.get("date", today)
            scheduled_time = reminder["scheduled_time"]
            
            # Handle different time formats
            if ":" in scheduled_time and len(scheduled_time) <= 8:
                # It's just a time like "08:00" or "08:00:00"
                scheduled_datetime = datetime.datetime.strptime(f"{reminder_date} {scheduled_time}", "%Y-%m-%d %H:%M:%S" if ":" in scheduled_time else "%Y-%m-%d %H:%M")
            else:
                # It's a full datetime
                try:
                    scheduled_datetime = datetime.datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    # Use current date with the time if parsing fails
                    try:
                        time_only = datetime.datetime.strptime(scheduled_time, "%H:%M:%S").time()
                        scheduled_datetime = datetime.datetime.combine(datetime.datetime.strptime(reminder_date, "%Y-%m-%d").date(), time_only)
                    except ValueError:
                        # Default to current time + 1 hour if all parsing fails
                        scheduled_datetime = now + datetime.timedelta(hours=1)
            
            # If the reminder is in the future and hasn't been sent yet
            if scheduled_datetime > now and not reminder.get("sent", False):
                upcoming.append(reminder)
        
        self.state["upcoming_reminders"] = sorted(upcoming, key=lambda x: x.get("scheduled_time", "00:00"))
    
    def generate_reminder_message(self, reminder_type: str) -> str:
        """
        Generate a reminder message based on the reminder type.
        
        Args:
            reminder_type: Type of reminder (Medication, Appointment, Exercise, Hydration).
            
        Returns:
            A reminder message.
        """
        if reminder_type == "Medication":
            return "Time to take your medication. Please don't forget!"
        elif reminder_type == "Appointment":
            return "You have an appointment scheduled. Please prepare for it."
        elif reminder_type == "Exercise":
            return "It's time for your daily exercise routine. Stay active!"
        elif reminder_type == "Hydration":
            return "Remember to drink water and stay hydrated throughout the day."
        else:
            return f"Reminder: {reminder_type}"
    
    def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle received messages from other agents.
        
        Args:
            message: The message to handle.
        """
        message_type = message.get("type")
        
        if message_type == "reminder_data":
            # Process new reminder data
            self.process_data(message.get("data"))
            
        elif message_type == "request_reminders":
            # Someone is requesting the current reminders
            if "sender_id" in message:
                self.send_reminders(message["sender_id"])
        
        elif message_type == "acknowledge_reminder":
            # Acknowledge a reminder
            reminder_id = message.get("reminder_id")
            if reminder_id:
                self.acknowledge_reminder(reminder_id)
                
                # Notify the sender that the reminder was acknowledged
                if "sender_id" in message:
                    response = {
                        "type": "reminder_acknowledged",
                        "reminder_id": reminder_id,
                        "success": True
                    }
                    self.send_message(message["sender_id"], response)
        
        elif message_type == "get_next_reminder":
            # Get the next reminder from the dataset
            self.update_upcoming_reminders()
            
            # If there are upcoming reminders, trigger the next one
            if self.state["upcoming_reminders"]:
                next_reminder = self.state["upcoming_reminders"][0]
                self.trigger_reminder(next_reminder)
                
                # Remove from upcoming and add to active
                self.state["upcoming_reminders"].remove(next_reminder)
                self.state["active_reminders"].append(next_reminder)
                
                # Notify the sender
                if "sender_id" in message:
                    response = {
                        "type": "reminder_triggered",
                        "data": next_reminder
                    }
                    self.send_message(message["sender_id"], response)
    
    def send_reminders(self, recipient_id: str) -> None:
        """
        Send the current reminders to a connected agent.
        
        Args:
            recipient_id: ID of the agent to send the reminders to.
        """
        message = {
            "type": "reminders",
            "active_reminders": self.state["active_reminders"],
            "upcoming_reminders": self.state["upcoming_reminders"]
        }
        self.send_message(recipient_id, message)
    
    def acknowledge_reminder(self, reminder_id: str) -> Dict[str, Any]:
        """
        Acknowledge a reminder.
        
        Args:
            reminder_id: ID of the reminder to acknowledge.
            
        Returns:
            Status of the acknowledgment.
        """
        # Find the reminder in active reminders
        for i, reminder in enumerate(self.state["active_reminders"]):
            if reminder["id"] == reminder_id:
                # Mark as acknowledged
                reminder["acknowledged"] = True
                reminder["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Move from active to completed
                self.state["completed_reminders"].append(reminder)
                self.state["active_reminders"].pop(i)
                
                return {
                    "status": "success",
                    "message": f"Reminder {reminder_id} acknowledged."
                }
        
        return {
            "status": "error",
            "message": f"Reminder {reminder_id} not found in active reminders."
        }
    
    def trigger_reminder(self, reminder: Dict[str, Any]) -> None:
        """
        Trigger a reminder, sending it to the connected agents or systems.
        
        Args:
            reminder: The reminder to trigger.
        """
        # Set the reminder as sent
        reminder["sent"] = True
        reminder["sent_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Print to console
        print(f"\n[REMINDER] {reminder['message']}\n")
        
        # Call the callback if available (for UI updates)
        if self.reminder_callback:
            self.reminder_callback(reminder)
        
        # Add to active reminders if not already there
        if reminder not in self.state["active_reminders"]:
            self.state["active_reminders"].append(reminder)
    
    def get_random_reminder(self) -> Dict[str, Any]:
        """
        Generate a random reminder for testing.
        
        Returns:
            A random reminder object.
        """
        reminder_types = ["Medication", "Appointment", "Exercise", "Hydration"]
        reminder_type = random.choice(reminder_types)
        
        now = datetime.datetime.now()
        scheduled_time = (now + datetime.timedelta(minutes=random.randint(1, 60))).strftime("%H:%M:%S")
        
        return {
            "id": str(uuid.uuid4()),
            "device_id": "SIMULATOR",
            "type": reminder_type,
            "scheduled_time": scheduled_time,
            "message": self.generate_reminder_message(reminder_type),
            "sent": False,
            "acknowledged": False,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "priority": random.choice(["low", "medium", "high"]),
            "date": now.strftime("%Y-%m-%d")
        }
    
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process reminder data and potentially schedule a new reminder.
        
        Args:
            data: Reminder data to process.
            
        Returns:
            Processing results.
        """
        if not data:
            return {"status": "error", "message": "No data provided"}
        
        # Check if this is a reminder object
        if "reminder_type" in data or "type" in data:
            reminder_type = data.get("reminder_type", data.get("type", "General"))
            
            # Create a reminder object
            reminder = {
                "id": data.get("id", str(uuid.uuid4())),
                "device_id": data.get("device_id", "UNKNOWN"),
                "type": reminder_type,
                "scheduled_time": data.get("time", data.get("scheduled_time", "00:00")),
                "message": data.get("description", data.get("message", self.generate_reminder_message(reminder_type))),
                "sent": data.get("sent", False),
                "acknowledged": data.get("acknowledged", False),
                "created_at": data.get("timestamp", data.get("created_at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
                "priority": data.get("priority", "medium"),
                "date": data.get("date", datetime.datetime.now().strftime("%Y-%m-%d"))
            }
            
            # Add the reminder to scheduled reminders
            self.state["scheduled_reminders"].append(reminder)
            
            # Update upcoming reminders
            self.update_upcoming_reminders()
            
            return {
                "status": "success",
                "message": f"Reminder scheduled for {reminder['scheduled_time']}",
                "reminder_id": reminder["id"]
            }
        
        return {"status": "error", "message": "Invalid reminder data format"}
    
    def process_reminder(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a reminder entry, converting it into a scheduled reminder.
        Alias for process_data for compatibility.
        
        Args:
            data: Reminder data to process.
            
        Returns:
            Processing results.
        """
        return self.process_data(data)
    
    def process_csv_data(self, csv_file: str) -> pd.DataFrame:
        """
        Process reminder data from a CSV file.
        
        Args:
            csv_file: Path to the CSV file.
            
        Returns:
            The processed DataFrame.
        """
        try:
            # Read the CSV
            df = pd.read_csv(csv_file)
            
            # Store the data
            self.data = df
            
            # Extract reminders
            self.extract_scheduled_reminders()
            
            # Update upcoming reminders
            self.update_upcoming_reminders()
            
            return df
        except Exception as e:
            print(f"Error processing reminder CSV data: {str(e)}")
            return pd.DataFrame()
    
    def run_periodic_check(self) -> None:
        """
        Run a periodic check to trigger due reminders.
        """
        self.update_upcoming_reminders()
        
        now = datetime.datetime.now()
        triggered_reminders = []
        
        # Check for reminders that are due but haven't been sent yet
        for reminder in self.state["upcoming_reminders"][:]:
            scheduled_time = reminder["scheduled_time"]
            reminder_date = reminder.get("date", now.strftime("%Y-%m-%d"))
            
            # Handle different time formats
            try:
                if ":" in scheduled_time and len(scheduled_time) <= 8:
                    # It's just a time like "08:00" or "08:00:00"
                    scheduled_datetime = datetime.datetime.strptime(f"{reminder_date} {scheduled_time}", "%Y-%m-%d %H:%M:%S" if ":" in scheduled_time else "%Y-%m-%d %H:%M")
                else:
                    # It's a full datetime
                    scheduled_datetime = datetime.datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # Default to current time + 1 hour if parsing fails
                scheduled_datetime = now + datetime.timedelta(hours=1)
            
            # If the reminder is due
            if scheduled_datetime <= now:
                # Trigger the reminder
                self.trigger_reminder(reminder)
                
                # Remove from upcoming
                self.state["upcoming_reminders"].remove(reminder)
                
                # Add to triggered reminders
                triggered_reminders.append(reminder)
                
                # Make sure it's in active reminders
                if reminder not in self.state["active_reminders"]:
                    self.state["active_reminders"].append(reminder)
        
        return triggered_reminders
    
    def run_scheduler(self) -> List[Dict[str, Any]]:
        """
        Run the reminder scheduler to check for due reminders and trigger them.
        This method should be called periodically by the coordinator.
        
        Returns:
            List of reminders that were triggered.
        """
        # Update upcoming reminders first
        self.update_upcoming_reminders()
        
        # Run the periodic check to trigger due reminders
        triggered_reminders = self.run_periodic_check()
        
        # Add a new reminder for demo purposes if we have CSV data
        if self.data is not None and not self.data.empty and random.random() < 0.05:  # 5% chance
            self.current_data_index = (self.current_data_index + 1) % len(self.data)
            data = self.row_to_dict(self.data.iloc[self.current_data_index])
            
            # Override the scheduled time to be in the future
            now = datetime.datetime.now()
            future_time = now + datetime.timedelta(minutes=random.randint(5, 60))
            data["time"] = future_time.strftime("%H:%M:%S")
            
            # Process the data to create a new reminder
            self.process_data(data)
        
        return triggered_reminders
    
    def add_reminder(self, reminder_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new reminder to the system.
        
        Args:
            reminder_data: Data for the new reminder.
            
        Returns:
            Status of the operation.
        """
        # Process the data to create a reminder
        result = self.process_data(reminder_data)
        
        # Update upcoming reminders
        self.update_upcoming_reminders()
        
        return result
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get the current reminder settings.
        
        Returns:
            Dictionary with reminder settings.
        """
        return {
            "reminder_lead_time": 15,  # minutes before scheduled time to start sending notifications
            "reminder_repeat_interval": 5,  # minutes between reminder repeats
            "max_reminder_repeats": 3,  # maximum number of repeats for unacknowledged reminders
            "notify_caregiver_after_max_repeats": True  # whether to notify caregiver after max repeats
        }
    
    def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update reminder settings.
        
        Args:
            settings: New settings values.
            
        Returns:
            Updated settings.
        """
        # In a real system, we would update internal settings here
        return {
            "status": "success",
            "message": "Settings updated",
            "settings": settings
        } 