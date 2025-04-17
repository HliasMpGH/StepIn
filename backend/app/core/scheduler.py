import time
import threading
from datetime import datetime

from app.services.meeting_service import MeetingService
from app.core.constants import TIME_OUT

class MeetingScheduler:
    def __init__(self, scan_interval=60):
        self.meeting_service = MeetingService()
        self.scan_interval = scan_interval
        self.running = False
        self.scheduler_thread = None

    def start(self):
        """Start the meeting scheduler"""
        if self.running:
            return False

        self.running = True
        try:
            # Perform an initial scan
            self._scan_meetings()

            # Start the scheduler thread
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
        except Exception as e:
            print(f"Error in initial scan: {e}")

        return True

    def stop(self):
        """Stop the meeting scheduler"""
        if not self.running:
            return False

        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        return True

    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                self._scan_meetings()
            except Exception as e:
                print(f"Error in scheduler loop: {e}")
            time.sleep(self.scan_interval)

    def _scan_meetings(self):
        """Scan database for meetings to activate or deactivate"""
        try:
            self.meeting_service.sync_meetings()
        except Exception as e:
            print(f"Error scanning meetings: {e}")

    def scan_now(self):
        """Manually trigger a scan for testing"""
        self._scan_meetings()

# Create a single instance of the scheduler
scheduler = MeetingScheduler()