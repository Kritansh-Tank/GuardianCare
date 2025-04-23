"""
Safety Monitoring Agent for Elderly Care System.
Monitors movement, detects falls, and identifies unusual behavior.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import datetime
import random

from elderly_care_system.agents.base_agent import Agent


class SafetyMonitoringAgent(Agent):
    """
    Agent responsible for monitoring safety-related data such as
    movement activity, falls, and location.
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "Safety Monitoring Agent"):
        """
        Initialize the safety monitoring agent.
        
        Args:
            agent_id: Optional unique identifier for the agent.
            name: Name of the agent for display purposes.
        """
        super().__init__(agent_id, name)
        
        # Initialize state
        self.state = {
            "latest_readings": {},
            "alerts": [],
            "historical_data": [],
            "fall_incidents": []
        }
        
        # Store the full dataset
        self.data = None
        self.current_data_index = 0
    
    def initialize_with_data(self, data: pd.DataFrame) -> None:
        """
        Initialize the agent with data from a CSV file.
        
        Args:
            data: DataFrame containing safety monitoring data.
        """
        self.data = data
        
        if self.data is not None and not self.data.empty:
            # Process some initial data points to populate the state
            sample_data = self.data.sample(min(5, len(self.data)))
            
            for _, row in sample_data.iterrows():
                data_point = self.row_to_dict(row)
                self.process_data(data_point)
            
            # Set the next data point to process
            self.current_data_index = 0
    
    def row_to_dict(self, row: pd.Series) -> Dict[str, Any]:
        """
        Convert a DataFrame row to a dictionary for processing.
        
        Args:
            row: A row from the safety monitoring DataFrame.
            
        Returns:
            Dictionary with the extracted data.
        """
        data = {}
        
        # Extract the data we need
        if "Device-ID/User-ID" in row:
            data["device_id"] = row["Device-ID/User-ID"]
        
        if "Timestamp" in row:
            data["timestamp"] = row["Timestamp"]
        
        if "Movement Activity" in row:
            data["Movement Activity"] = row["Movement Activity"]
        
        if "Fall Detected (Yes/No)" in row:
            data["Fall Detected"] = row["Fall Detected (Yes/No)"] == "Yes"
        
        if "Impact Force Level" in row:
            data["Impact Force Level"] = row["Impact Force Level"]
        
        if "Post-Fall Inactivity Duration (Seconds)" in row:
            try:
                data["Post-Fall Inactivity Duration"] = int(row["Post-Fall Inactivity Duration (Seconds)"])
            except (ValueError, TypeError):
                data["Post-Fall Inactivity Duration"] = 0
        
        if "Location" in row:
            data["Location"] = row["Location"]
        
        if "Alert Triggered (Yes/No)" in row:
            data["Alert Triggered"] = row["Alert Triggered (Yes/No)"] == "Yes"
        
        return data
    
    def get_next_data_point(self) -> Dict[str, Any]:
        """
        Get the next data point from the dataset.
        
        Returns:
            Dictionary with the next data point, or empty dict if no more data.
        """
        if self.data is None or self.data.empty or self.current_data_index >= len(self.data):
            return {}
        
        row = self.data.iloc[self.current_data_index]
        self.current_data_index = (self.current_data_index + 1) % len(self.data)
        
        return self.row_to_dict(row)
    
    def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle received messages from other agents.
        
        Args:
            message: The message to handle.
        """
        message_type = message.get("type")
        
        if message_type == "safety_data":
            # Process new safety data
            self.process_data(message.get("data"))
            
        elif message_type == "request_status":
            # Someone is requesting the latest safety status
            if "sender_id" in message:
                self.send_safety_status(message["sender_id"])
        
        elif message_type == "get_next_reading":
            # Return the next safety reading from the dataset
            data = self.get_next_data_point()
            if data:
                self.process_data(data)
                
                # Send the processed data to the requester
                if "sender_id" in message:
                    response = {
                        "type": "safety_data_response",
                        "data": self.state["latest_readings"],
                        "alerts": []  # Will be filled if there are any alerts
                    }
                    self.send_message(message["sender_id"], response)
    
    def send_safety_status(self, recipient_id: str) -> None:
        """
        Send the latest safety status to a connected agent.
        
        Args:
            recipient_id: ID of the agent to send the status to.
        """
        message = {
            "type": "safety_status",
            "data": self.state["latest_readings"],
            "alerts": self.state["alerts"][-5:] if self.state["alerts"] else []
        }
        self.send_message(recipient_id, message)
    
    def check_safety_conditions(self, data: Dict[str, Any]) -> List[str]:
        """
        Check if safety conditions raise any alerts.
        
        Args:
            data: Dictionary of safety data.
            
        Returns:
            List of alert messages for concerning conditions.
        """
        alerts = []
        
        # Check if a fall is detected
        if data.get("fall_detected", False):
            impact_level = data.get("impact_force_level", "Unknown")
            inactivity_duration = data.get("post_fall_inactivity_duration", 0)
            
            if impact_level == "High" or inactivity_duration > 300:  # 5 minutes
                alerts.append(f"CRITICAL FALL DETECTED: High impact force or prolonged inactivity ({inactivity_duration} seconds)!")
            elif impact_level == "Medium" or inactivity_duration > 120:  # 2 minutes
                alerts.append(f"FALL DETECTED: Medium impact force with {inactivity_duration} seconds of inactivity!")
            else:
                alerts.append(f"Minor fall detected: Low impact with {inactivity_duration} seconds of inactivity.")
        
        # Check for concerning lack of movement
        if data.get("movement_activity", "") == "No Movement" and not data.get("fall_detected", False):
            location = data.get("location", "Unknown")
            alerts.append(f"Extended period of no movement detected in the {location}.")
        
        return alerts
    
    def trigger_alert(self, alerts: List[str], data: Dict[str, Any]) -> None:
        """
        Trigger alerts for safety concerns.
        
        Args:
            alerts: List of alert messages.
            data: Safety data that triggered the alerts.
        """
        if not alerts:
            return
            
        # Add timestamp to the alert
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create alert message
        alert_message = {
            "type": "safety_alert",
            "timestamp": timestamp,
            "alert_messages": alerts,
            "data": data
        }
        
        # Store the alert
        self.state["alerts"].append(alert_message)
        
        # Send alert through callback if available
        self.send_alert(alert_message)
        
        # Broadcast the alert to all connected agents
        self.broadcast_message(alert_message)
    
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process safety monitoring data and trigger alerts if necessary.
        
        Args:
            data: Safety monitoring data to process.
            
        Returns:
            Processed data with any alerts triggered.
        """
        processed_data = {}
        
        # Extract relevant data points
        if "Movement Activity" in data:
            processed_data["movement_activity"] = data["Movement Activity"]
        
        if "Fall Detected" in data:
            processed_data["fall_detected"] = data["Fall Detected"]
        
        if "Impact Force Level" in data:
            processed_data["impact_force_level"] = data["Impact Force Level"]
        
        if "Post-Fall Inactivity Duration" in data:
            processed_data["post_fall_inactivity_duration"] = data["Post-Fall Inactivity Duration"]
        
        if "Location" in data:
            processed_data["location"] = data["Location"]
        
        # Add timestamp if available
        if "timestamp" in data:
            processed_data["timestamp"] = data["timestamp"]
        else:
            processed_data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update latest readings, keeping only values that are actually present
        self.state["latest_readings"].update(processed_data)
        
        # Add to historical data (limited to last 100 readings)
        self.state["historical_data"].append(processed_data)
        if len(self.state["historical_data"]) > 100:
            self.state["historical_data"] = self.state["historical_data"][-100:]
        
        # Store fall incidents separately
        if processed_data.get("fall_detected", False):
            self.state["fall_incidents"].append({
                "timestamp": processed_data.get("timestamp"),
                "impact_level": processed_data.get("impact_force_level", "Unknown"),
                "inactivity_duration": processed_data.get("post_fall_inactivity_duration", 0),
                "location": processed_data.get("location", "Unknown")
            })
        
        # Check for safety concerns
        alerts = self.check_safety_conditions(processed_data)
        
        # Trigger alerts if necessary
        if alerts:
            self.trigger_alert(alerts, processed_data)
        
        return {
            "processed_data": processed_data,
            "alerts": alerts
        }
    
    def process_csv_data(self, csv_file: str) -> pd.DataFrame:
        """
        Process safety monitoring data from a CSV file.
        
        Args:
            csv_file: Path to the CSV file containing safety monitoring data.
            
        Returns:
            DataFrame of processed safety data with alerts.
        """
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        # Store the data for future use
        self.data = df
        
        # Process a few rows for initial state
        if not df.empty:
            self.initialize_with_data(df)
        
        return df
    
    def run_periodic_check(self) -> None:
        """
        Run a periodic check to update safety data and alerts.
        This method is called by the coordinator agent periodically.
        """
        # Get a new data point from the dataset and process it
        data = self.get_next_data_point()
        if data:
            self.process_data(data)
            
            # Notify connected agents
            self.broadcast_message({
                "type": "safety_update",
                "data": self.state["latest_readings"],
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }) 