import pytz
from datetime import datetime, timezone
from typing import Optional




class TimeManager:
    # This class provides utility functions for handling time-related operations, such as converting between timezones and formatting datetime objects. It is designed to help manage time effectively in applications that may need to support users across different timezones.   
    @staticmethod
    def get_user_time(user_timezone: str = "UTC") -> datetime:
       # calculates the current time in the user's timezone. It takes a timezone string as input and returns a datetime object representing the current time in that timezone. If the provided timezone is invalid, it defaults to UTC.
        try:
            tz = pytz.timezone(user_timezone)
        except Exception:
            # Fallback to UTC if the timezone string is corrupted or missing
            tz = pytz.utc
            
        return datetime.now(timezone.utc).astimezone(tz)
    

    @staticmethod
    def format_for_ai(dt: datetime) -> str:
        # formats a datetime object into a human-readable string format that is suitable for display in AI-generated responses. The format includes the full day of the week, month name, day number, year, and time in 12-hour format with AM/PM. This makes it easier for users to understand the date and time information provided by the AI.
        # %A = Day, %B = Month, %d = Day number, %Y = Year
        # %I = Hour (12hr), %M = Minute, %p = AM/PM
        return dt.strftime("%A, %B %d, %Y, at %I:%M %p")
    

    # @staticmethod
    # def get_time_period(dt: datetime) -> str:
    #     # determines the time period of the day (morning, afternoon, evening, night) based on the hour of a given datetime object. This can be used to provide more contextually relevant responses in AI interactions, such as greeting users with "Good morning" or "Good evening" based on the current time.
    #     hour = dt.hour
    #     if 5 <= hour < 12: return "morning"
    #     if 12 <= hour < 17: return "afternoon"
    #     if 17 <= hour < 21: return "evening"
    #     return "night"