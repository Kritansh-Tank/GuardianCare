"""
Health Monitoring Agent for Elderly Care System.
Monitors vital signs, analyzes patterns, and raises health alerts.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import datetime
import statistics
import uuid

from elderly_care_system.agents.base_agent import Agent


class HealthMonitoringAgent(Agent):
    """
    Agent responsible for monitoring health metrics and raising alerts.
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "Health Monitoring Agent"):
        """
        Initialize the health monitoring agent.
        
        Args:
            agent_id: Optional unique identifier for the agent.
            name: Name of the agent for display purposes.
        """
        super().__init__(agent_id, name)
        
        # Initialize state
        self.state = {
            "health_data": [],
            "alerts": [],
            "heartrate_threshold": 100,
            "blood_pressure_threshold": 140,
            "blood_pressure_lower_threshold": 90,
            "temperature_threshold": 37.5,
            "blood_glucose_threshold": 180,
            "blood_glucose_lower_threshold": 70,
            "oxygen_level_threshold": 92
        }
        
        # Store the full dataset
        self.data = None
        self.current_data_index = 0
        
        # Store historical metrics
        self.historical_metrics = {
            "heartrate": [],
            "systolic_bp": [],
            "diastolic_bp": [],
            "temperature": [],
            "blood_glucose": [],
            "oxygen_level": []
        }
    
    def initialize_with_data(self, data: pd.DataFrame) -> None:
        """
        Initialize the agent with data from a CSV file.
        
        Args:
            data: DataFrame containing health data.
        """
        self.data = data
        
        if self.data is not None and not self.data.empty:
            # Reset current index
            self.current_data_index = 0
    
    def row_to_dict(self, row: pd.Series) -> Dict[str, Any]:
        """
        Convert a DataFrame row to a dictionary for processing.
        
        Args:
            row: A row from the health data DataFrame.
            
        Returns:
            Dictionary with the extracted data.
        """
        data = {}
        
        # Extract the data we need
        if "Device-ID/User-ID" in row:
            data["device_id"] = row["Device-ID/User-ID"]
        
        if "Timestamp" in row:
            data["timestamp"] = row["Timestamp"]
        
        if "Heart Rate" in row:
            try:
                data["heartrate"] = float(row["Heart Rate"])
                
                # Also extract threshold status if available
                if "Heart Rate Below/Above Threshold (Yes/No)" in row:
                    data["heartrate_threshold_exceeded"] = row["Heart Rate Below/Above Threshold (Yes/No)"] == "Yes"
            except (ValueError, TypeError):
                pass
        
        if "Blood Pressure" in row:
            try:
                bp_str = row["Blood Pressure"]
                # Parse values like "120/80 mmHg"
                if isinstance(bp_str, str):
                    # Remove 'mmHg' if present and split on '/'
                    bp_str = bp_str.replace("mmHg", "").strip()
                    if "/" in bp_str:
                        sys_bp, dia_bp = bp_str.split("/")
                        data["systolic_bp"] = float(sys_bp)
                        data["diastolic_bp"] = float(dia_bp)
                        
                # Also extract threshold status if available
                if "Blood Pressure Below/Above Threshold (Yes/No)" in row:
                    data["blood_pressure_threshold_exceeded"] = row["Blood Pressure Below/Above Threshold (Yes/No)"] == "Yes"
            except (ValueError, TypeError):
                pass
        
        if "Temperature (°C)" in row:
            try:
                data["temperature"] = float(row["Temperature (°C)"])
            except (ValueError, TypeError):
                pass
        
        if "Glucose Levels" in row:
            try:
                data["blood_glucose"] = float(row["Glucose Levels"])
                
                # Also extract threshold status if available
                if "Glucose Levels Below/Above Threshold (Yes/No)" in row:
                    data["glucose_threshold_exceeded"] = row["Glucose Levels Below/Above Threshold (Yes/No)"] == "Yes"
            except (ValueError, TypeError):
                pass
        
        if "Oxygen Saturation (SpO₂%)" in row or "SpO2 (%)" in row:
            try:
                # Handle different column names
                o2_column = "Oxygen Saturation (SpO₂%)" if "Oxygen Saturation (SpO₂%)" in row else "SpO2 (%)"
                data["oxygen_level"] = float(row[o2_column])
                
                # Also extract threshold status if available
                if "SpO₂ Below Threshold (Yes/No)" in row:
                    data["oxygen_threshold_exceeded"] = row["SpO₂ Below Threshold (Yes/No)"] == "Yes"
            except (ValueError, TypeError):
                pass
        
        # Extract alert information if available
        if "Alert Triggered (Yes/No)" in row:
            data["alert_triggered"] = row["Alert Triggered (Yes/No)"] == "Yes"
            
        if "Caregiver Notified (Yes/No)" in row:
            data["caregiver_notified"] = row["Caregiver Notified (Yes/No)"] == "Yes"
        
        return data
    
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
        
        if message_type == "health_data":
            # Process new health data
            health_data = message.get("data", {})
            self.process_health_data(health_data)
            
        elif message_type == "request_health_status":
            # Send health status to the requesting agent
            if "sender_id" in message:
                self.send_health_status(message["sender_id"])
        
        elif message_type == "update_threshold":
            # Update a threshold value
            metric = message.get("metric")
            value = message.get("value")
            if metric and value is not None:
                self.update_threshold(metric, value)
        
        elif message_type == "get_next_data_point":
            # Send the next health data point
            data_point = self.get_next_data_point()
            
            if data_point and "sender_id" in message:
                response = {
                    "type": "health_data_point",
                    "data": data_point
                }
                self.send_message(message["sender_id"], response)
    
    def process_health_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process health data and check for alerts.
        
        Args:
            data: Health data to process.
            
        Returns:
            Result of processing the data.
        """
        # Add the data to our history
        self.state["health_data"].append(data)
        
        # Update historical metrics
        for metric in ["heartrate", "systolic_bp", "diastolic_bp", "temperature", "blood_glucose", "oxygen_level"]:
            if metric in data:
                self.historical_metrics[metric].append(data[metric])
                
                # Keep only the last 100 data points
                if len(self.historical_metrics[metric]) > 100:
                    self.historical_metrics[metric] = self.historical_metrics[metric][-100:]
        
        # Use predefined alerts from CSV if available, otherwise check for alerts
        if "alert_triggered" in data and data["alert_triggered"]:
            alerts = self.generate_alerts_from_data(data)
        else:
            # Check for alerts based on our thresholds
            alerts = self.check_health_alerts(data)
        
        # Add any alerts to our state
        for alert in alerts:
            self.state["alerts"].append(alert)
            
            # Also broadcast the alert to other agents
            self.broadcast_message(alert)
        
        return {
            "processed_data": data,
            "alerts": alerts
        }
    
    def generate_alerts_from_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate alerts based on the threshold information in the data.
        
        Args:
            data: Health data with threshold information.
            
        Returns:
            List of alerts generated from the data.
        """
        alerts = []
        timestamp = data.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Check each metric that has threshold information
        if "heartrate" in data and "heartrate_threshold_exceeded" in data and data["heartrate_threshold_exceeded"]:
            alerts.append({
                "type": "health_alert",
                "alert_id": str(uuid.uuid4()),
                "metric": "heartrate",
                "value": data["heartrate"],
                "threshold": self.state["heartrate_threshold"],
                "message": f"Heart rate threshold exceeded: {data['heartrate']} BPM",
                "severity": "medium",
                "timestamp": timestamp
            })
        
        if ("systolic_bp" in data and "diastolic_bp" in data and 
            "blood_pressure_threshold_exceeded" in data and data["blood_pressure_threshold_exceeded"]):
            alerts.append({
                "type": "health_alert",
                "alert_id": str(uuid.uuid4()),
                "metric": "blood_pressure",
                "value": f"{data['systolic_bp']}/{data['diastolic_bp']}",
                "threshold": self.state["blood_pressure_threshold"],
                "message": f"Blood pressure threshold exceeded: {data['systolic_bp']}/{data['diastolic_bp']} mmHg",
                "severity": "high",
                "timestamp": timestamp
            })
        
        if "blood_glucose" in data and "glucose_threshold_exceeded" in data and data["glucose_threshold_exceeded"]:
            alerts.append({
                "type": "health_alert",
                "alert_id": str(uuid.uuid4()),
                "metric": "blood_glucose",
                "value": data["blood_glucose"],
                "threshold": self.state["blood_glucose_threshold"],
                "message": f"Blood glucose threshold exceeded: {data['blood_glucose']} mg/dL",
                "severity": "medium",
                "timestamp": timestamp
            })
        
        if "oxygen_level" in data and "oxygen_threshold_exceeded" in data and data["oxygen_threshold_exceeded"]:
            alerts.append({
                "type": "health_alert",
                "alert_id": str(uuid.uuid4()),
                "metric": "oxygen_level",
                "value": data["oxygen_level"],
                "threshold": self.state["oxygen_level_threshold"],
                "message": f"Oxygen level below threshold: {data['oxygen_level']}%",
                "severity": "high",
                "timestamp": timestamp
            })
        
        return alerts
    
    def check_health_alerts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check for health alerts based on the given data.
        
        Args:
            data: Health data to check.
            
        Returns:
            List of alerts generated from the data.
        """
        alerts = []
        timestamp = data.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Check heart rate
        if "heartrate" in data:
            hr = data["heartrate"]
            if hr > self.state["heartrate_threshold"]:
                alerts.append({
                    "type": "health_alert",
                    "alert_id": str(uuid.uuid4()),
                    "metric": "heartrate",
                    "value": hr,
                    "threshold": self.state["heartrate_threshold"],
                    "message": f"High heart rate detected: {hr} BPM",
                    "severity": "medium",
                    "timestamp": timestamp
                })
            
            # Check for unusually low heart rate
            if hr < 50:  # Resting heart rate below 50 is generally concerning
                alerts.append({
                    "type": "health_alert",
                    "alert_id": str(uuid.uuid4()),
                    "metric": "heartrate",
                    "value": hr,
                    "threshold": 50,
                    "message": f"Low heart rate detected: {hr} BPM",
                    "severity": "medium",
                    "timestamp": timestamp
                })
        
        # Check blood pressure
        if "systolic_bp" in data and "diastolic_bp" in data:
            sys_bp = data["systolic_bp"]
            dia_bp = data["diastolic_bp"]
            
            if sys_bp > self.state["blood_pressure_threshold"]:
                alerts.append({
                    "type": "health_alert",
                    "alert_id": str(uuid.uuid4()),
                    "metric": "blood_pressure",
                    "value": f"{sys_bp}/{dia_bp}",
                    "threshold": self.state["blood_pressure_threshold"],
                    "message": f"High blood pressure detected: {sys_bp}/{dia_bp} mmHg",
                    "severity": "high",
                    "timestamp": timestamp
                })
            
            if dia_bp > 90:  # High diastolic pressure
                alerts.append({
                    "type": "health_alert",
                    "alert_id": str(uuid.uuid4()),
                    "metric": "diastolic_bp",
                    "value": dia_bp,
                    "threshold": 90,
                    "message": f"High diastolic blood pressure: {dia_bp} mmHg",
                    "severity": "medium",
                    "timestamp": timestamp
                })
            
            if sys_bp < self.state["blood_pressure_lower_threshold"]:
                alerts.append({
                    "type": "health_alert",
                    "alert_id": str(uuid.uuid4()),
                    "metric": "blood_pressure",
                    "value": f"{sys_bp}/{dia_bp}",
                    "threshold": self.state["blood_pressure_lower_threshold"],
                    "message": f"Low blood pressure detected: {sys_bp}/{dia_bp} mmHg",
                    "severity": "medium",
                    "timestamp": timestamp
                })
        
        # Check temperature
        if "temperature" in data:
            temp = data["temperature"]
            if temp > self.state["temperature_threshold"]:
                alerts.append({
                    "type": "health_alert",
                    "alert_id": str(uuid.uuid4()),
                    "metric": "temperature",
                    "value": temp,
                    "threshold": self.state["temperature_threshold"],
                    "message": f"Elevated temperature detected: {temp}°C",
                    "severity": "medium",
                    "timestamp": timestamp
                })
            
            if temp < 36.0:  # Low body temperature
                alerts.append({
                    "type": "health_alert",
                    "alert_id": str(uuid.uuid4()),
                    "metric": "temperature",
                    "value": temp,
                    "threshold": 36.0,
                    "message": f"Low body temperature detected: {temp}°C",
                    "severity": "medium",
                    "timestamp": timestamp
                })
        
        # Check blood glucose
        if "blood_glucose" in data:
            glucose = data["blood_glucose"]
            if glucose > self.state["blood_glucose_threshold"]:
                alerts.append({
                    "type": "health_alert",
                    "alert_id": str(uuid.uuid4()),
                    "metric": "blood_glucose",
                    "value": glucose,
                    "threshold": self.state["blood_glucose_threshold"],
                    "message": f"High blood glucose detected: {glucose} mg/dL",
                    "severity": "medium",
                    "timestamp": timestamp
                })
            
            if glucose < self.state["blood_glucose_lower_threshold"]:
                alerts.append({
                    "type": "health_alert",
                    "alert_id": str(uuid.uuid4()),
                    "metric": "blood_glucose",
                    "value": glucose,
                    "threshold": self.state["blood_glucose_lower_threshold"],
                    "message": f"Low blood glucose detected: {glucose} mg/dL",
                    "severity": "high",
                    "timestamp": timestamp
                })
        
        # Check oxygen level
        if "oxygen_level" in data:
            oxygen = data["oxygen_level"]
            if oxygen < self.state["oxygen_level_threshold"]:
                alerts.append({
                    "type": "health_alert",
                    "alert_id": str(uuid.uuid4()),
                    "metric": "oxygen_level",
                    "value": oxygen,
                    "threshold": self.state["oxygen_level_threshold"],
                    "message": f"Low oxygen level detected: {oxygen}%",
                    "severity": "high",
                    "timestamp": timestamp
                })
        
        # Check for potentially concerning pattern (rapid heart rate increase)
        if "heartrate" in data and len(self.historical_metrics["heartrate"]) >= 5:
            recent_rates = self.historical_metrics["heartrate"][-5:]
            if data["heartrate"] > recent_rates[0] * 1.3:  # 30% increase
                alerts.append({
                    "type": "health_alert",
                    "alert_id": str(uuid.uuid4()),
                    "metric": "heartrate_change",
                    "value": data["heartrate"],
                    "baseline": recent_rates[0],
                    "message": f"Rapid increase in heart rate: from {recent_rates[0]} to {data['heartrate']} BPM",
                    "severity": "medium",
                    "timestamp": timestamp
                })
        
        return alerts
    
    def update_threshold(self, metric: str, value: Any) -> Dict[str, Any]:
        """
        Update a threshold value.
        
        Args:
            metric: The metric to update.
            value: The new threshold value.
            
        Returns:
            The status of the update.
        """
        threshold_key = f"{metric}_threshold"
        
        if threshold_key in self.state:
            # Update the threshold
            self.state[threshold_key] = value
            return {
                "success": True,
                "message": f"Updated {metric} threshold to {value}."
            }
        else:
            return {
                "success": False,
                "message": f"Unknown metric: {metric}"
            }
    
    def send_health_status(self, recipient_id: str) -> None:
        """
        Send the current health status to a connected agent.
        
        Args:
            recipient_id: ID of the agent to send the status to.
        """
        # Calculate average values for the last 24 hours
        status = self.calculate_health_status()
        
        # Create the message
        message = {
            "type": "health_status",
            "status": status,
            "recent_alerts": self.state["alerts"][-5:] if self.state["alerts"] else [],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Send to the recipient
        self.send_message(recipient_id, message)
    
    def calculate_health_status(self) -> Dict[str, Any]:
        """
        Calculate the current health status based on historical data.
        
        Returns:
            Dictionary with health status metrics.
        """
        status = {}
        
        # Calculate average values for each metric
        for metric, values in self.historical_metrics.items():
            if values:
                status[f"avg_{metric}"] = sum(values) / len(values)
                status[f"max_{metric}"] = max(values)
                status[f"min_{metric}"] = min(values)
                
                if len(values) > 1:
                    status[f"std_{metric}"] = statistics.stdev(values)
        
        # Add overall status assessment
        num_alerts = len(self.state["alerts"])
        if num_alerts == 0:
            status["overall"] = "normal"
        elif num_alerts < 3:
            status["overall"] = "caution"
        else:
            status["overall"] = "concern"
        
        return status
    
    def process_csv_data(self, csv_file: str) -> pd.DataFrame:
        """
        Process health data from a CSV file.
        
        Args:
            csv_file: Path to the CSV file containing health data.
            
        Returns:
            DataFrame of processed health data.
        """
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        # Initialize with data
        self.initialize_with_data(df)
        
        # Process each row
        processed_data = []
        for _, row in df.iterrows():
            # Convert row to dictionary
            data = self.row_to_dict(row)
            
            # Process the health data
            result = self.process_health_data(data)
            
            # Add to processed data
            processed_data.append({
                "data": data,
                "alerts": result["alerts"],
                "timestamp": data.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            })
        
        # Convert to DataFrame
        processed_df = pd.DataFrame(processed_data)
        return processed_df
    
    def analyze_csv_data(self, csv_file: str) -> Dict[str, Any]:
        """
        Analyze health data from a CSV file and provide summary statistics.
        
        Args:
            csv_file: Path to the CSV file containing health data.
            
        Returns:
            Dictionary with analysis results.
        """
        # Process the CSV data
        processed_df = self.process_csv_data(csv_file)
        
        # Count number of alerts by type
        alert_counts = {"total": 0}
        for row in processed_df["alerts"]:
            alert_counts["total"] += len(row)
            for alert in row:
                metric = alert.get("metric", "unknown")
                if metric not in alert_counts:
                    alert_counts[metric] = 0
                alert_counts[metric] += 1
        
        # Calculate percentage of readings that triggered alerts
        alert_percentage = (
            len(processed_df[processed_df["alerts"].apply(lambda x: len(x) > 0)]) / 
            len(processed_df) * 100 if len(processed_df) > 0 else 0
        )
        
        # Count number of readings with caregiver notifications
        notified_count = len(
            processed_df[processed_df["data"].apply(
                lambda x: "caregiver_notified" in x and x["caregiver_notified"]
            )]
        )
        
        # Calculate alert statistics by metric
        metric_stats = {}
        for metric in ["heartrate", "blood_pressure", "blood_glucose", "oxygen_level"]:
            threshold_key = f"{metric}_threshold_exceeded"
            metric_stats[metric] = {
                "total_readings": len(processed_df[processed_df["data"].apply(
                    lambda x: any(m in x for m in ([metric, "systolic_bp"] if metric == "blood_pressure" else [metric]))
                )]),
                "threshold_exceeded": len(processed_df[processed_df["data"].apply(
                    lambda x: threshold_key in x and x[threshold_key]
                )])
            }
            if metric_stats[metric]["total_readings"] > 0:
                metric_stats[metric]["percentage"] = (
                    metric_stats[metric]["threshold_exceeded"] / 
                    metric_stats[metric]["total_readings"] * 100
                )
            else:
                metric_stats[metric]["percentage"] = 0
        
        return {
            "total_readings": len(processed_df),
            "alert_counts": alert_counts,
            "alert_percentage": alert_percentage,
            "notified_count": notified_count,
            "metric_stats": metric_stats,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """
        Get a summary of current health metrics.
        
        Returns:
            Dictionary with health metrics and their latest values.
        """
        metrics = {}
        
        if self.state["health_data"]:
            latest_data = self.state["health_data"][-1]
            
            # Extract key metrics
            for metric in ["heartrate", "systolic_bp", "diastolic_bp", "temperature", "blood_glucose", "oxygen_level"]:
                if metric in latest_data:
                    metrics[metric] = latest_data[metric]
        
        return metrics
        
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a summary report of health metrics and alerts.
        
        Returns:
            Dictionary with summary report data.
        """
        # Get current health metrics
        current_metrics = self.get_health_metrics()
        
        # Get latest alerts
        recent_alerts = self.state["alerts"][-10:] if self.state["alerts"] else []
        
        # Calculate health status
        health_status = self.calculate_health_status()
        
        # Count alerts by severity
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for alert in self.state["alerts"]:
            severity = alert.get("severity", "medium")
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Count alerts by type
        metric_counts = {}
        for alert in self.state["alerts"]:
            metric = alert.get("metric", "unknown")
            if metric not in metric_counts:
                metric_counts[metric] = 0
            metric_counts[metric] += 1
        
        return {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_metrics": current_metrics,
            "health_status": health_status,
            "recent_alerts": recent_alerts,
            "total_alerts": len(self.state["alerts"]),
            "severity_counts": severity_counts,
            "metric_counts": metric_counts
        }
    
    def process_data(self, data: Any) -> Any:
        """
        Process data received by the agent. Implementation of abstract method from base Agent class.
        
        Args:
            data: The data to process, could be health metrics or a CSV file path.
            
        Returns:
            Processed data or results.
        """
        # Check if data is a string (potentially a CSV file path)
        if isinstance(data, str) and data.endswith('.csv'):
            return self.process_csv_data(data)
        
        # If data is a dictionary, process it as health data
        elif isinstance(data, dict):
            return self.process_health_data(data)
            
        # If it's a DataFrame, initialize with it
        elif isinstance(data, pd.DataFrame):
            self.initialize_with_data(data)
            return {"status": "initialized", "rows": len(data)}
            
        return {"error": "Unsupported data format"} 