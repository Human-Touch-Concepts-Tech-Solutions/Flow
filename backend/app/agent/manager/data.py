import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timezone

class DataState:
    def __init__(self):
        # Format: {"email@gmail.com": [log_list]}
        self._registry: Dict[str, List[Dict]] = {}
        # self data holding
        self.system_config: Dict = {}
        # Lock to prevent race conditions during high-speed updates
        self._lock = asyncio.Lock()

    async def deposit_log(self, email: str, event_type: str, details: Dict, description: str):
        """Deposits a new update into the user's signal box."""
        async with self._lock:
            if email not in self._registry:
                self._registry[email] = []
            
            log_entry = {
                "utc_timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event_type,
                "description": description, # The "Story" of the change
                "raw_data": details          # The technical data
            }
            self._registry[email].append(log_entry)
            print(f"[DataState] Log deposited for {email}: {event_type}")

    async def consume_logs(self, email: str) -> List[Dict]:
        async with self._lock:
            logs = self._registry.pop(email, [])
            if logs:
                print(f"[DataState] {len(logs)} logs consumed and cleared for {email}")
            return logs
        
    async def update_system_config(self, category: str, data: Dict):
        """Updates global config. Mirrors DB structure exactly."""
        async with self._lock:
           # Convert MongoDB ObjectId to string for JSON compatibility later
            if "_id" in data:
                data["_id"] = str(data["_id"])
                
            self.system_config[category] = data
            print(f"[DataState] ✅ System Config Memory Updated: {category}")

    async def get_config(self) -> Dict:
        """Returns the full system configuration."""
        return self.system_config
    
    
    

