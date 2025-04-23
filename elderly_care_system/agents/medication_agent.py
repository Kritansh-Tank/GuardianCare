"""
Medication Management Agent for Elderly Care System.
Handles medication scheduling, reminders, and tracking compliance.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import datetime
import uuid

from elderly_care_system.agents.base_agent import Agent


class MedicationAgent(Agent):
    """
    Agent responsible for managing medication schedules and compliance tracking.
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "Medication Agent"):
        """
        Initialize the medication management agent.
        
        Args:
            agent_id: Optional unique identifier for the agent.
            name: Name of the agent for display purposes.
        """
        super().__init__(agent_id, name)
        
        # Initialize state
        self.state = {
            "medications": {},           # Dictionary of all medications
            "schedule": {},              # Daily schedule of medications
            "taken_doses": [],           # Record of taken medications
            "missed_doses": [],          # Record of missed medications
            "upcoming_medications": [],  # Medications due in the next hour
            "refill_alerts": []          # Alerts for medications that need refills
        }
        
        # Store the full dataset
        self.data = None
        self.current_data_index = 0
    
    def initialize_with_data(self, data: pd.DataFrame) -> None:
        """
        Initialize the agent with data from a CSV file.
        
        Args:
            data: DataFrame containing medication data.
        """
        self.data = data
        
        if self.data is not None and not self.data.empty:
            # Reset current index
            self.current_data_index = 0
            # Process the data to populate our state
            self.extract_medications_from_data()
    
    def row_to_dict(self, row: pd.Series) -> Dict[str, Any]:
        """
        Convert a DataFrame row to a dictionary for processing.
        
        Args:
            row: A row from the medication data DataFrame.
            
        Returns:
            Dictionary with the extracted data.
        """
        data = {}
        
        # Extract the data we need
        if "Medication Name" in row:
            data["medication_name"] = row["Medication Name"]
        
        if "Dosage" in row:
            data["dosage"] = row["Dosage"]
        
        if "Frequency" in row:
            data["frequency"] = row["Frequency"]
        
        if "Time of Day" in row:
            data["time_of_day"] = row["Time of Day"]
        
        if "Instructions" in row:
            data["instructions"] = row["Instructions"]
        
        if "Start Date" in row:
            data["start_date"] = row["Start Date"]
        
        if "End Date" in row:
            data["end_date"] = row["End Date"]
        
        if "Current Supply" in row:
            try:
                data["current_supply"] = int(row["Current Supply"])
            except (ValueError, TypeError):
                data["current_supply"] = 0
        
        if "Refill Threshold" in row:
            try:
                data["refill_threshold"] = int(row["Refill Threshold"])
            except (ValueError, TypeError):
                data["refill_threshold"] = 5
        
        if "Patient ID" in row:
            data["patient_id"] = row["Patient ID"]
        
        return data
    
    def extract_medications_from_data(self) -> None:
        """
        Extract medication information from the dataset and store in the agent's state.
        """
        if self.data is None or self.data.empty:
            return
        
        medications = {}
        schedule = {}
        
        for _, row in self.data.iterrows():
            medication_data = self.row_to_dict(row)
            
            if "medication_name" not in medication_data:
                continue
            
            # Generate unique ID for this medication
            med_id = str(uuid.uuid4())
            
            # Add to medications dictionary
            medications[med_id] = {
                "id": med_id,
                "name": medication_data.get("medication_name", ""),
                "dosage": medication_data.get("dosage", ""),
                "frequency": medication_data.get("frequency", ""),
                "instructions": medication_data.get("instructions", ""),
                "start_date": medication_data.get("start_date", ""),
                "end_date": medication_data.get("end_date", ""),
                "current_supply": medication_data.get("current_supply", 0),
                "refill_threshold": medication_data.get("refill_threshold", 5),
                "patient_id": medication_data.get("patient_id", ""),
                "compliance_rate": 100.0  # Initial compliance rate
            }
            
            # Parse schedule information
            if "time_of_day" in medication_data:
                time_str = medication_data["time_of_day"]
                
                # Handle multiple times (e.g., "8:00 AM, 2:00 PM, 8:00 PM")
                times = [t.strip() for t in time_str.split(",")]
                
                for time in times:
                    # Convert time string to datetime.time object
                    try:
                        time_obj = datetime.datetime.strptime(time, "%I:%M %p").time()
                    except ValueError:
                        # Skip invalid time
                        continue
                    
                    # Create key for the schedule dictionary (HH:MM format)
                    time_key = time_obj.strftime("%H:%M")
                    
                    if time_key not in schedule:
                        schedule[time_key] = []
                    
                    schedule[time_key].append({
                        "medication_id": med_id,
                        "name": medication_data.get("medication_name", ""),
                        "dosage": medication_data.get("dosage", ""),
                        "instructions": medication_data.get("instructions", ""),
                    })
        
        # Update state
        self.state["medications"] = medications
        self.state["schedule"] = schedule
        
        # Check if any medications need refills
        self.check_refill_needs()
        
        # Update upcoming medications
        self.update_upcoming_medications()
    
    def get_next_data_point(self) -> Dict[str, Any]:
        """
        Get the next data point from the dataset.
        
        Returns:
            The next data point.
        """
        if self.data is None or self.data.empty or self.current_data_index >= len(self.data):
            return {}
        
        # Get the current row
        row = self.data.iloc[self.current_data_index]
        
        # Convert row to dictionary
        data = self.row_to_dict(row)
        
        # Increment index for next call
        self.current_data_index += 1
        
        return data
    
    def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle received messages from other agents.
        
        Args:
            message: The message to handle.
        """
        message_type = message.get("type")
        
        if message_type == "medication_taken":
            # Record that a medication has been taken
            medication_id = message.get("medication_id")
            timestamp = message.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.record_medication_taken(medication_id, timestamp)
            
        elif message_type == "medication_missed":
            # Record that a medication has been missed
            medication_id = message.get("medication_id")
            timestamp = message.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.record_medication_missed(medication_id, timestamp)
            
        elif message_type == "request_medication_schedule":
            # Send medication schedule to the requesting agent
            if "sender_id" in message:
                self.send_medication_schedule(message["sender_id"])
                
        elif message_type == "update_medication_supply":
            # Update the supply of a medication
            medication_id = message.get("medication_id")
            new_supply = message.get("supply")
            if medication_id and new_supply is not None:
                self.update_medication_supply(medication_id, new_supply)
        
        elif message_type == "get_next_data_point":
            # Send the next medication data point
            data_point = self.get_next_data_point()
            
            if data_point and "sender_id" in message:
                response = {
                    "type": "medication_data_point",
                    "data": data_point
                }
                self.send_message(message["sender_id"], response)
    
    def record_medication_taken(self, medication_id: str, timestamp: str) -> Dict[str, Any]:
        """
        Record that a medication has been taken.
        
        Args:
            medication_id: ID of the medication that was taken.
            timestamp: Time when the medication was taken.
            
        Returns:
            Status of the operation.
        """
        if medication_id not in self.state["medications"]:
            return {
                "success": False,
                "message": f"Unknown medication ID: {medication_id}"
            }
        
        # Get medication info
        medication = self.state["medications"][medication_id]
        
        # Record the taken medication
        taken_record = {
            "id": str(uuid.uuid4()),
            "medication_id": medication_id,
            "medication_name": medication["name"],
            "timestamp": timestamp,
            "status": "taken"
        }
        self.state["taken_doses"].append(taken_record)
        
        # Decrease supply
        if "current_supply" in medication:
            medication["current_supply"] = max(0, medication["current_supply"] - 1)
            
            # Check if refill needed
            if medication["current_supply"] <= medication.get("refill_threshold", 5):
                self.create_refill_alert(medication_id)
        
        # Update medication in state
        self.state["medications"][medication_id] = medication
        
        # Update compliance rate
        self.update_compliance_rate(medication_id)
        
        return {
            "success": True,
            "message": f"Recorded {medication['name']} as taken at {timestamp}",
            "remaining_supply": medication.get("current_supply", 0)
        }
    
    def record_medication_missed(self, medication_id: str, timestamp: str) -> Dict[str, Any]:
        """
        Record that a medication has been missed.
        
        Args:
            medication_id: ID of the medication that was missed.
            timestamp: Time when the medication was supposed to be taken.
            
        Returns:
            Status of the operation.
        """
        if medication_id not in self.state["medications"]:
            return {
                "success": False,
                "message": f"Unknown medication ID: {medication_id}"
            }
        
        # Get medication info
        medication = self.state["medications"][medication_id]
        
        # Record the missed medication
        missed_record = {
            "id": str(uuid.uuid4()),
            "medication_id": medication_id,
            "medication_name": medication["name"],
            "timestamp": timestamp,
            "status": "missed"
        }
        self.state["missed_doses"].append(missed_record)
        
        # Update compliance rate
        self.update_compliance_rate(medication_id)
        
        # Create alert for missed medication
        alert = {
            "type": "medication_alert",
            "alert_id": str(uuid.uuid4()),
            "medication_id": medication_id,
            "medication_name": medication["name"],
            "message": f"Missed dose of {medication['name']} at {timestamp}",
            "severity": "medium",
            "timestamp": timestamp
        }
        
        # Broadcast the alert
        self.broadcast_message(alert)
        
        return {
            "success": True,
            "message": f"Recorded {medication['name']} as missed at {timestamp}"
        }
    
    def update_compliance_rate(self, medication_id: str) -> None:
        """
        Update the compliance rate for a medication.
        
        Args:
            medication_id: ID of the medication to update.
        """
        if medication_id not in self.state["medications"]:
            return
        
        # Count taken and missed doses for this medication
        taken_count = sum(1 for dose in self.state["taken_doses"] 
                         if dose["medication_id"] == medication_id)
        
        missed_count = sum(1 for dose in self.state["missed_doses"] 
                          if dose["medication_id"] == medication_id)
        
        total_doses = taken_count + missed_count
        
        if total_doses > 0:
            compliance_rate = (taken_count / total_doses) * 100
        else:
            compliance_rate = 100.0
        
        # Update compliance rate
        self.state["medications"][medication_id]["compliance_rate"] = compliance_rate
    
    def create_refill_alert(self, medication_id: str) -> None:
        """
        Create a refill alert for a medication.
        
        Args:
            medication_id: ID of the medication that needs a refill.
        """
        if medication_id not in self.state["medications"]:
            return
        
        medication = self.state["medications"][medication_id]
        
        # Check if we already have an active refill alert for this medication
        for alert in self.state["refill_alerts"]:
            if alert["medication_id"] == medication_id and not alert.get("resolved", False):
                # Already have an active alert
                return
        
        # Create a new refill alert
        refill_alert = {
            "id": str(uuid.uuid4()),
            "type": "refill_alert",
            "medication_id": medication_id,
            "medication_name": medication["name"],
            "current_supply": medication.get("current_supply", 0),
            "refill_threshold": medication.get("refill_threshold", 5),
            "message": f"Low supply of {medication['name']}: {medication.get('current_supply', 0)} remaining",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "resolved": False
        }
        
        # Add to refill alerts
        self.state["refill_alerts"].append(refill_alert)
        
        # Broadcast the alert
        self.broadcast_message(refill_alert)
    
    def update_medication_supply(self, medication_id: str, new_supply: int) -> Dict[str, Any]:
        """
        Update the supply of a medication.
        
        Args:
            medication_id: ID of the medication to update.
            new_supply: New supply count.
            
        Returns:
            Status of the operation.
        """
        if medication_id not in self.state["medications"]:
            return {
                "success": False,
                "message": f"Unknown medication ID: {medication_id}"
            }
        
        # Update supply
        self.state["medications"][medication_id]["current_supply"] = new_supply
        
        # Check if any refill alerts can be resolved
        for alert in self.state["refill_alerts"]:
            if alert["medication_id"] == medication_id and not alert.get("resolved", False):
                if new_supply > alert["refill_threshold"]:
                    alert["resolved"] = True
                    alert["resolution_timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    alert["resolution_message"] = f"Medication resupplied with {new_supply} doses"
        
        return {
            "success": True,
            "message": f"Updated supply of {self.state['medications'][medication_id]['name']} to {new_supply}",
            "new_supply": new_supply
        }
    
    def update_upcoming_medications(self) -> List[Dict[str, Any]]:
        """
        Update the list of medications due in the next hour.
        
        Returns:
            List of upcoming medications.
        """
        upcoming = []
        now = datetime.datetime.now()
        one_hour_later = now + datetime.timedelta(hours=1)
        
        # Check each time slot in the schedule
        for time_str, medications in self.state["schedule"].items():
            # Convert time string to datetime
            try:
                hours, minutes = map(int, time_str.split(":"))
                med_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                
                # If the time has already passed for today, it's for tomorrow
                if med_time < now:
                    med_time = med_time + datetime.timedelta(days=1)
                
                # Check if it's within the next hour
                if now <= med_time <= one_hour_later:
                    for med in medications:
                        # Add to upcoming list
                        upcoming.append({
                            "medication_id": med["medication_id"],
                            "name": med["name"],
                            "dosage": med["dosage"],
                            "instructions": med["instructions"],
                            "scheduled_time": med_time.strftime("%Y-%m-%d %H:%M:%S")
                        })
            except (ValueError, TypeError):
                # Skip invalid time format
                continue
        
        # Update state
        self.state["upcoming_medications"] = upcoming
        
        return upcoming
    
    def send_medication_schedule(self, recipient_id: str) -> None:
        """
        Send the current medication schedule to a connected agent.
        
        Args:
            recipient_id: ID of the agent to send the schedule to.
        """
        # Update upcoming medications first
        self.update_upcoming_medications()
        
        # Create the message
        message = {
            "type": "medication_schedule",
            "schedule": self.state["schedule"],
            "upcoming": self.state["upcoming_medications"],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Send to the recipient
        self.send_message(recipient_id, message)
    
    def check_refill_needs(self) -> List[Dict[str, Any]]:
        """
        Check if any medications need refills.
        
        Returns:
            List of medications that need refills.
        """
        needs_refill = []
        
        for med_id, medication in self.state["medications"].items():
            current_supply = medication.get("current_supply", 0)
            refill_threshold = medication.get("refill_threshold", 5)
            
            if current_supply <= refill_threshold:
                needs_refill.append(medication)
                self.create_refill_alert(med_id)
        
        return needs_refill
    
    def get_daily_schedule(self, date_str: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the medication schedule for a specific date.
        
        Args:
            date_str: Date string in YYYY-MM-DD format. Defaults to today.
            
        Returns:
            Medication schedule for the specified date.
        """
        if date_str is None:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Create a structured schedule object
        daily_schedule = {}
        
        for time_str, medications in self.state["schedule"].items():
            # Add the time slot to the schedule
            daily_schedule[time_str] = [
                {
                    "id": med["medication_id"],
                    "name": med["name"],
                    "dosage": med["dosage"],
                    "instructions": med["instructions"],
                    "scheduled_time": f"{date_str} {time_str}"
                }
                for med in medications
            ]
        
        return daily_schedule
    
    def process_csv_data(self, csv_file: str) -> pd.DataFrame:
        """
        Process medication data from a CSV file.
        
        Args:
            csv_file: Path to the CSV file containing medication data.
            
        Returns:
            DataFrame of processed medication data.
        """
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        # Initialize with data
        self.initialize_with_data(df)
        
        return df
    
    def get_medication_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about medication compliance and refill needs.
        
        Returns:
            Dictionary with medication statistics.
        """
        total_medications = len(self.state["medications"])
        
        # Count medications that need refills
        needs_refill_count = sum(
            1 for med in self.state["medications"].values()
            if med.get("current_supply", 0) <= med.get("refill_threshold", 5)
        )
        
        # Calculate average compliance rate
        all_compliance_rates = [
            med.get("compliance_rate", 100) 
            for med in self.state["medications"].values()
        ]
        
        avg_compliance = (
            sum(all_compliance_rates) / len(all_compliance_rates)
            if all_compliance_rates else 100
        )
        
        # Count total taken vs. missed doses
        total_taken = len(self.state["taken_doses"])
        total_missed = len(self.state["missed_doses"])
        
        # Calculate overall compliance rate
        overall_compliance = (
            (total_taken / (total_taken + total_missed)) * 100
            if (total_taken + total_missed) > 0 else 100
        )
        
        return {
            "total_medications": total_medications,
            "needs_refill_count": needs_refill_count,
            "needs_refill_percentage": (needs_refill_count / total_medications * 100) if total_medications > 0 else 0,
            "average_compliance_rate": avg_compliance,
            "overall_compliance_rate": overall_compliance,
            "total_doses_taken": total_taken,
            "total_doses_missed": total_missed
        } 