import pytz
from datetime import datetime, timezone
from typing import Optional, Any, Dict

class TimeManager:
    @staticmethod
    def get_user_time(user_timezone: str = "UTC") -> datetime:
        # Using localized time directly from the timezone object is safer
        tz = pytz.timezone(user_timezone)
        return datetime.now(tz) # This gets the current time ALREADY in that TZ

    @staticmethod
    def format_for_ai(dt: datetime) -> str:
        return dt.strftime("%A, %B %d, %Y, at %I:%M %p")



    @staticmethod
    def localize_timestamp(utc_val: Any, user_timezone: str) -> str:
        if not utc_val: return "Unknown Time"
        try:
            if isinstance(utc_val, datetime):
                dt_utc = utc_val
            else:
                dt_utc = datetime.fromisoformat(str(utc_val).replace('Z', '+00:00'))
            
            if dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=timezone.utc)

            tz = pytz.timezone(user_timezone)
            # Use normalize to handle daylight savings or historical shifts correctly
            dt_local = dt_utc.astimezone(tz)
            return TimeManager.format_for_ai(dt_local)
        except Exception as e:
            return str(utc_val)
    @staticmethod
    def localize_device_time(device_str: str, user_timezone: str) -> str:
        """Converts browser string 'DD/MM/YYYY, HH:MM:SS' to pretty format."""
        if not device_str: return "Unknown"
        try:
            # Parse the format: 22/04/2026, 23:02:22
            # Note: This parser is flexible for most common browser locales
            clean_str = device_str.replace(',', '')
            dt = datetime.strptime(clean_str, "%d/%m/%Y %H:%M:%S")
            
            # Since this comes from the device, we treat it as already localized
            return TimeManager.format_for_ai(dt)
        except:
            return device_str # Fallback to raw if parsing fails
        

    # @staticmethod
    # def get_time_period(dt: datetime) -> str:
    #     # determines the time period of the day (morning, afternoon, evening, night) based on the hour of a given datetime object. This can be used to provide more contextually relevant responses in AI interactions, such as greeting users with "Good morning" or "Good evening" based on the current time.
    #     hour = dt.hour
    #     if 5 <= hour < 12: return "morning"
    #     if 12 <= hour < 17: return "afternoon"
    #     if 17 <= hour < 21: return "evening"
    #     return "night"