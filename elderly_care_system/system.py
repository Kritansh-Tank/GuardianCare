"""
Main system module for the Elderly Care System.
Ties all agents together and provides the main interface for running the system.
"""
import threading
import time
import datetime
import pandas as pd
import os
import traceback
from typing import Dict, Any, Optional, List, Tuple

from elderly_care_system.agents.coordinator_agent import CoordinatorAgent
from elderly_care_system.agents.user_interface_agent import UserInterfaceAgent


class ElderlyCareSystem:
    """
    Main system class that ties all agents together and manages the overall system.
    """

    def __init__(self):
        """
        Initialize the Elderly Care System.
        """
        # Initialize system state
        self.running = False
        self.stop_requested = False
        self.initialization_errors = []

        # Initialize configuration
        self.config = {}

        # Initialize components with error handling
        self._initialize_agents()

        # Initialize threads
        self.scheduler_thread = None
        self.ui_thread = None

    def _initialize_agents(self) -> None:
        """Initialize all agents with error handling."""
        try:
            # Create the coordinator agent which manages all specialized agents
            self.coordinator = CoordinatorAgent()

            # Create the user interface agent
            self.ui = UserInterfaceAgent()

            # Connect the agents
            self.connect_agents()

            # If initialization had errors, report them through the UI
            if self.initialization_errors and hasattr(self, 'ui') and self.ui:
                for error in self.initialization_errors:
                    self.ui.display_content(f"WARNING: {error}")
        except Exception as e:
            error_msg = f"Failed to initialize agents: {str(e)}"
            print(error_msg)
            self.initialization_errors.append(error_msg)
            raise  # Re-raise since we can't continue without agents

    def connect_agents(self) -> None:
        """Connect all agents to enable communication between them."""
        # Connect coordinator to UI agent
        self.coordinator.connect_to_agent(self.ui)
        self.ui.connect_to_agent(self.coordinator)

        # Access the specialized agents through the coordinator
        self.health_agent = self.coordinator.health_agent
        self.safety_agent = self.coordinator.safety_agent
        self.reminder_agent = self.coordinator.reminder_agent

    def load_data(self, health_csv: str = None, safety_csv: str = None, reminder_csv: str = None) -> Dict[str, pd.DataFrame]:
        """
        Load data from CSV files and process with the specialized agents.

        Args:
            health_csv: Path to the health monitoring CSV file.
            safety_csv: Path to the safety monitoring CSV file.
            reminder_csv: Path to the daily reminder CSV file.

        Returns:
            Dictionary of DataFrames with the processed data.
        """
        print("Loading and processing data...")
        results = {}
        data_errors = []

        # Find CSV files if not provided
        if not health_csv and not safety_csv and not reminder_csv:
            # Try to find the files in the Dataset directory
            dataset_dir = "Dataset/[Usecase 4] AI for Elderly Care and Support"
            if os.path.exists(dataset_dir):
                print(f"Looking for data files in: {dataset_dir}")
                for filename in os.listdir(dataset_dir):
                    if "health" in filename.lower():
                        health_csv = os.path.join(dataset_dir, filename)
                    elif "safety" in filename.lower():
                        safety_csv = os.path.join(dataset_dir, filename)
                    elif "reminder" in filename.lower() or "daily" in filename.lower():
                        reminder_csv = os.path.join(dataset_dir, filename)

        # Process health data
        if health_csv and os.path.exists(health_csv):
            try:
                print(f"Processing health data from {health_csv}...")
                results["health"] = self.coordinator.process_health_data(
                    health_csv)

                # Store all health data in the database
                if isinstance(results["health"], pd.DataFrame):
                    for _, row in results["health"].iterrows():
                        try:
                            data = self.health_agent.row_to_dict(row)
                        except Exception as e:
                            print(f"Error storing health row: {str(e)}")
            except Exception as e:
                error_msg = f"Error processing health data: {str(e)}"
                print(error_msg)
                data_errors.append(error_msg)
        else:
            print("Health data file not found or specified.")
            self._create_dummy_health_data()

        # Process safety data
        if safety_csv and os.path.exists(safety_csv):
            try:
                print(f"Processing safety data from {safety_csv}...")
                results["safety"] = self.coordinator.process_safety_data(
                    safety_csv)

                # Store all safety data in the database
                if isinstance(results["safety"], pd.DataFrame):
                    for _, row in results["safety"].iterrows():
                        try:
                            data = self.safety_agent.row_to_dict(row)
                        except Exception as e:
                            print(f"Error storing safety row: {str(e)}")
            except Exception as e:
                error_msg = f"Error processing safety data: {str(e)}"
                print(error_msg)
                data_errors.append(error_msg)
        else:
            print("Safety data file not found or specified.")
            self._create_dummy_safety_data()

        # Process reminder data
        if reminder_csv and os.path.exists(reminder_csv):
            try:
                print(f"Processing reminder data from {reminder_csv}...")
                results["reminder"] = self.coordinator.process_reminder_data(
                    reminder_csv)

                # Store all reminder data in the database
                if isinstance(results["reminder"], pd.DataFrame):
                    for _, row in results["reminder"].iterrows():
                        try:
                            data = self.reminder_agent.row_to_dict(row)
                        except Exception as e:
                            print(f"Error storing reminder row: {str(e)}")
            except Exception as e:
                error_msg = f"Error processing reminder data: {str(e)}"
                print(error_msg)
                data_errors.append(error_msg)
        else:
            print("Reminder data file not found or specified.")
            self._create_dummy_reminder_data()

        # Report errors to UI if available
        if data_errors and hasattr(self, 'ui') and self.ui:
            for error in data_errors:
                self.ui.display_content(f"DATA WARNING: {error}")

        print("Data processing complete!")
        return results

    def _create_dummy_health_data(self) -> None:
        """Create dummy health data for testing."""
        print("Creating dummy health data for testing")
        dummy_data = {
            "heartrate": 75,
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "temperature": 36.5,
            "blood_glucose": 100,
            "oxygen_level": 98,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            self.health_agent.state["latest_readings"] = dummy_data
            self.health_agent.process_health_data(dummy_data)
        except Exception as e:
            print(f"Error setting up dummy health data: {str(e)}")

    def _create_dummy_safety_data(self) -> None:
        """Create dummy safety data for testing."""
        print("Creating dummy safety data for testing")
        dummy_safety = {
            "movement_detected": True,
            "fall_detected": False,
            "door_status": "closed",
            "location": "living_room",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            self.safety_agent.state["latest_readings"] = dummy_safety
            self.safety_agent.process_safety_data(dummy_safety)
        except Exception as e:
            print(f"Error setting up dummy safety data: {str(e)}")

    def _create_dummy_reminder_data(self) -> None:
        """Create dummy reminder data for testing."""
        print("Creating dummy reminder data for testing")
        dummy_reminder = {
            "reminder_type": "medication",
            "description": "Take heart medication",
            "time": "08:00",
            "priority": "high",
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        }
        try:
            self.reminder_agent.add_reminder(dummy_reminder)
        except Exception as e:
            print(f"Error setting up dummy reminder data: {str(e)}")

    def start_scheduler(self) -> None:
        """Start the scheduler thread to periodically run system tasks."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            print("Scheduler is already running.")
            return

        self.stop_requested = False
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        print("Scheduler started.")

    def _scheduler_loop(self) -> None:
        """Internal scheduler loop to run periodic tasks."""
        while not self.stop_requested:
            try:
                # Run the coordinator's system routine
                self.coordinator.run_system()

                # Log a heartbeat
                now = datetime.datetime.now()
                timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] System heartbeat")

                # Sleep for a minute before next run
                time.sleep(60)
            except Exception as e:
                error_msg = f"Error in scheduler loop: {str(e)}"
                print(error_msg)
                time.sleep(5)  # Sleep a bit on error to avoid tight loop

    def start_ui(self) -> None:
        """Start the user interface loop in a separate thread."""
        if self.ui_thread and self.ui_thread.is_alive():
            print("UI is already running.")
            return

        self.ui_thread = threading.Thread(target=self._ui_loop)
        self.ui_thread.daemon = True
        self.ui_thread.start()
        print("User interface started.")

    def _ui_loop(self) -> None:
        """Internal UI loop to handle user interactions."""
        try:
            self.ui.run_ui_loop(lambda: self.stop_requested)
        except Exception as e:
            error_msg = f"Error in UI loop: {str(e)}"
            print(error_msg)

    def start(self) -> Tuple[bool, str]:
        """
        Start the entire system.

        Returns:
            Tuple of (success, message)
        """
        if self.running:
            return True, "System is already running."

        print("Starting Elderly Care System...")

        # Check if any critical initialization errors occurred
        if any("Failed to initialize" in error for error in self.initialization_errors):
            critical_errors = [
                e for e in self.initialization_errors if "Failed to initialize" in e]
            error_msg = "; ".join(critical_errors)
            return False, f"Cannot start system due to critical errors: {error_msg}"

        try:
            # Load data
            try:
                self.load_data()
            except Exception as e:
                error_msg = f"Error loading data: {str(e)}"
                print(error_msg)
                # Continue despite data errors

            # Start the system components
            try:
                # Start the scheduler
                self.start_scheduler()

                # Start the UI
                self.start_ui()

                self.running = True

                # Notify that system is running
                start_message = "System started successfully"
                if self.initialization_errors:
                    warning_count = len(self.initialization_errors)
                    start_message += f" with {warning_count} warnings"

                print(start_message)
                if hasattr(self, 'ui') and self.ui:
                    self.ui.display_content(start_message)

                return True, start_message
            except Exception as e:
                error_msg = f"Error starting system components: {str(e)}"
                print(error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error starting system: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return False, error_msg

    def stop(self) -> Tuple[bool, str]:
        """
        Stop the elderly care system.

        Returns:
            Tuple of (success, message)
        """
        if not self.running:
            return True, "System is not running."

        print("Stopping Elderly Care System...")

        try:
            # Signal all threads to stop
            self.stop_requested = True

            # Wait for threads to finish (with timeout)
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)

            if self.ui_thread and self.ui_thread.is_alive():
                self.ui_thread.join(timeout=5)

            self.running = False

            return True, "System stopped successfully."
        except Exception as e:
            error_msg = f"Error stopping system: {str(e)}"
            print(error_msg)
            return False, error_msg

    def process_single_data_point(self, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single data point of a specific type.

        Args:
            data_type: Type of data ('health', 'safety', 'reminder').
            data: Data dictionary to process.

        Returns:
            Result dictionary.
        """
        if not self.running:
            return {"status": "error", "message": "System not running"}

        try:
            if data_type == "health":
                result = self.health_agent.process_health_data(data)
                return result
            elif data_type == "safety":
                result = self.safety_agent.process_safety_data(data)
                return result
            elif data_type == "reminder":
                result = self.reminder_agent.process_reminder(data)
                return result
            else:
                return {"status": "error", "message": f"Unknown data type: {data_type}"}
        except Exception as e:
            error_msg = f"Error processing {data_type} data: {str(e)}"
            print(error_msg)
            return {"status": "error", "message": error_msg}

    def send_system_message(self, message: str) -> None:
        """
        Send a system message to the user interface.

        Args:
            message: Message to send.
        """
        if hasattr(self, 'ui') and self.ui:
            try:
                self.ui.display_content(message)
            except Exception as e:
                print(f"Error sending system message: {str(e)}")

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the current system status.

        Returns:
            Dictionary with system status information.
        """
        status = {
            "running": self.running,
            "initialization_errors": self.initialization_errors,
            "start_time": None,
            "last_heartbeat": None,
        }
        return status

    def run_simulation(self, simulation_data: List[Dict[str, Any]], speed_factor: float = 1.0) -> None:
        """
        Run a simulation with provided data.

        Args:
            simulation_data: List of data points to process in sequence.
            speed_factor: Factor to speed up or slow down the simulation (1.0 = real-time).
        """
        print(
            f"Starting simulation with {len(simulation_data)} data points...")

        for i, data_point in enumerate(simulation_data):
            # Extract data type and actual data
            data_type = data_point.get("type", "unknown")
            data = data_point.get("data", {})

            # Process the data
            print(
                f"Processing {data_type} data point {i+1}/{len(simulation_data)}...")
            self.process_single_data_point(data_type, data)

            # Sleep between data points
            delay = data_point.get("delay", 5) / speed_factor
            time.sleep(delay)

        print("Simulation complete!")

    def get_health_data(self) -> Dict[str, Any]:
        """
        Get the latest health data.

        Returns:
            Dictionary with the latest health readings and alerts.
        """
        if not self.health_agent:
            return {"error": "Health agent not initialized"}

        return {
            "latest_readings": self.health_agent.state.get("latest_readings", {}),
            # Last 5 alerts
            "alerts": self.health_agent.state.get("alerts", [])[-5:]
        }

    def get_safety_data(self) -> Dict[str, Any]:
        """
        Get the latest safety data.

        Returns:
            Dictionary with the latest safety readings and alerts.
        """
        if not self.safety_agent:
            return {"error": "Safety agent not initialized"}

        return {
            "latest_readings": self.safety_agent.state.get("latest_readings", {}),
            # Last 5 alerts
            "alerts": self.safety_agent.state.get("alerts", [])[-5:]
        }

    def get_reminders(self) -> Dict[str, Any]:
        """
        Get active reminders.

        Returns:
            Dictionary with active and completed reminders.
        """
        if not self.reminder_agent:
            return {"error": "Reminder agent not initialized"}

        return {
            "active_reminders": self.reminder_agent.state.get("active_reminders", []),
            # Last 10 completed
            "completed_reminders": self.reminder_agent.state.get("completed_reminders", [])[-10:]
        }


def main():
    """Main function to run the Elderly Care System."""
    # Create the system
    system = ElderlyCareSystem()

    # Load data
    system.load_data()

    # Start the system
    system.start()

    try:
        # Keep the main thread alive
        while system.running:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        system.stop()


if __name__ == "__main__":
    main()
