import time
import threading
from datetime import datetime

from app.db.database import get_database
from app.services.redis_service import get_redis_manager
from app.core.constants import TIME_OUT

class MeetingScheduler:
    def __init__(self, scan_interval=60):
        self.db = get_database()
        self.redis_mgr = get_redis_manager()
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
            # Get current active meetings in Redis
            active_meetings = set(self.redis_mgr.get_active_meetings())
            
            # Get meetings that should be active from the database
            db_active_meetings = self.db.get_active_meetings()
            db_active_meetings_set = set(db_active_meetings)
            
            # Meetings to activate (in DB active but not in Redis)
            meetings_to_activate = db_active_meetings_set - active_meetings
            for meeting_id in meetings_to_activate:
                self._activate_meeting(meeting_id)
            
            # Meetings to deactivate (in Redis but not in DB active)
            meetings_to_deactivate = active_meetings - db_active_meetings_set
            for meeting_id in meetings_to_deactivate:
                self._deactivate_meeting(meeting_id)
        except Exception as e:
            print(f"Error scanning meetings: {e}")
    
    def _activate_meeting(self, meeting_id):
        """Activate a meeting in Redis"""
        try:
            meeting = self.db.get_meeting(meeting_id)
            
            if meeting:
                self.redis_mgr.activate_meeting(
                    meeting_id=meeting_id,
                    title=meeting["title"],
                    description=meeting["description"],
                    lat=meeting["lat"],
                    long=meeting["long"],
                    participants=meeting["participants"],
                    t2=meeting["t2"]
                )
                print(f"Activated meeting {meeting_id}: {meeting['title']}")
        except Exception as e:
            print(f"Error activating meeting {meeting_id}: {e}")
    
    def _deactivate_meeting(self, meeting_id):
        """Deactivate a meeting in Redis and log timeouts"""
        try:
            remaining_participants = self.redis_mgr.deactivate_meeting(meeting_id)
            
            # Log timeouts for remaining participants
            for email in remaining_participants:
                self.db.log_action(email, meeting_id, TIME_OUT)
            
            print(f"Deactivated meeting {meeting_id} with {len(remaining_participants)} remaining participants")
        except Exception as e:
            print(f"Error deactivating meeting {meeting_id}: {e}")
            
    def scan_now(self):
        """Manually trigger a scan for testing"""
        self._scan_meetings()

# Create a single instance of the scheduler
scheduler = MeetingScheduler()