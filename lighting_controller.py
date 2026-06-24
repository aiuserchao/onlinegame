#!/usr/bin/env python3
"""
Lighting Controller Script
Detects daytime/nighttime transitions and controls lights accordingly.
Configured for US Eastern Time zone.

Features:
- Checks current time in US Eastern Time using zoneinfo (built-in)
- Defines configurable night start/end times
- Determines if lights should be ON (nighttime) or OFF (daytime)
- Can be extended to interface with smart home systems
"""

import datetime
import sys
import argparse
import json
import os
from typing import Tuple, Optional

# Try to use zoneinfo (Python 3.9+), fallback to pytz if needed
try:
    from zoneinfo import ZoneInfo
    HAS_ZONEINFO = True
except ImportError:
    HAS_ZONEINFO = False
    try:
        import pytz
        HAS_PYTZ = True
    except ImportError:
        HAS_PYTZ = False
        print("Error: Neither zoneinfo nor pytz available for timezone handling", file=sys.stderr)
        sys.exit(1)

# Configuration - adjust these as needed
DEFAULT_NIGHT_START_HOUR = 21  # 9 PM
DEFAULT_NIGHT_END_HOUR = 6     # 6 AM
TIMEZONE = "America/New_York"  # US Eastern Time (handles EST/EDT automatically)

class LightingController:
    def __init__(self, night_start_hour: int = DEFAULT_NIGHT_START_HOUR, 
                 night_end_hour: int = DEFAULT_NIGHT_END_HOUR,
                 timezone_str: str = TIMEZONE):
        self.night_start_hour = night_start_hour
        self.night_end_hour = night_end_hour
        self.timezone_str = timezone_str
        if HAS_ZONEINFO:
            self.timezone = ZoneInfo(timezone_str)
        else:
            self.timezone = pytz.timezone(timezone_str)
        self.state_file = os.path.join(os.path.dirname(__file__), ".lighting_state.json")
    
    def get_current_time(self) -> datetime.datetime:
        """Get current time in configured timezone."""
        return datetime.datetime.now(self.timezone)
    
    def is_nighttime(self, dt: Optional[datetime.datetime] = None) -> bool:
        """
        Determine if the given time is nighttime.
        
        Nighttime is defined as:
        - From night_start_hour to 23:59:59
        - From 00:00:00 to night_end_hour
        
        Example: night_start=21 (9PM), night_end=6 (6AM)
        Nighttime: 9PM-11:59PM and 12AM-6AM
        """
        if dt is None:
            dt = self.get_current_time()
        
        hour = dt.hour
        
        # Handle case where night_end_hour < night_start_hour (overnight period)
        if self.night_end_hour < self.night_start_hour:
            # Night spans midnight: e.g., 21:00 to 06:00
            return hour >= self.night_start_hour or hour < self.night_end_hour
        else:
            # Night is within same day: e.g., 01:00 to 05:00
            return self.night_start_hour <= hour < self.night_end_hour
    
    def get_light_state(self) -> str:
        """Return what the light state should be: 'ON' for night, 'OFF' for day."""
        return "ON" if self.is_nighttime() else "OFF"
    
    def get_transition_info(self) -> dict:
        """Get information about upcoming transitions."""
        now = self.get_current_time()
        today = now.date()
        
        # Calculate next transition times
        night_start_today = datetime.datetime.combine(today, datetime.time(self.night_start_hour, 0, 0)).replace(tzinfo=self.timezone)
        night_end_today = datetime.datetime.combine(today, datetime.time(self.night_end_hour, 0, 0)).replace(tzinfo=self.timezone)
        
        # Adjust for overnight periods
        if self.night_end_hour < self.night_start_hour:
            # Night spans midnight
            if now >= night_start_today:
                # We're in the evening part of night (after start time today)
                next_transition = night_end_today + datetime.timedelta(days=1)  # Ends tomorrow
                next_state = "OFF"  # Will turn off at morning end
            elif now < night_end_today:
                # We're in the morning part of night (before end time today)
                next_transition = night_end_today  # Ends today
                next_state = "OFF"  # Will turn off at this time
            else:
                # We're in daytime (between end and start)
                next_transition = night_start_today  # Starts today
                next_state = "ON"  # Will turn on at this time
        else:
            # Night is within same day
            if now < night_start_today:
                # Before night starts today
                next_transition = night_start_today
                next_state = "ON"  # Will turn on at night start
            elif now < night_end_today:
                # During night today
                next_transition = night_end_today
                next_state = "OFF"  # Will turn off at night end
            else:
                # After night ends today, next night starts tomorrow
                next_transition = night_start_today + datetime.timedelta(days=1)
                next_state = "ON"  # Will turn on at next night start
        
        time_until = next_transition - now
        hours_until = time_until.total_seconds() / 3600
        
        return {
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "is_nighttime": self.is_nighttime(now),
            "light_should_be": self.get_light_state(),
            "next_transition": next_transition.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "next_action": f"Turn lights {next_state}",
            "hours_until_transition": round(hours_until, 2)
        }
    
    def save_state(self, state: str):
        """Save current state to file for persistence."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    "state": state,
                    "timestamp": self.get_current_time().isoformat()
                }, f)
        except Exception as e:
            print(f"Warning: Could not save state: {e}", file=sys.stderr)
    
    def load_state(self) -> Optional[str]:
        """Load last known state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return data.get("state")
        except Exception:
            pass
        return None
    
    def control_lights(self, action: str, simulate: bool = True):
        """
        Control the lights based on action.
        In simulation mode, just prints what would be done.
        Replace with actual smart home API calls as needed.
        """
        timestamp = self.get_current_time().strftime("%Y-%m-%d %H:%M:%S %Z")
        
        if action.upper() == "ON":
            message = f"[{timestamp}] Turning lights ON (nighttime)"
        elif action.upper() == "OFF":
            message = f"[{timestamp}] Turning lights OFF (daytime)"
        else:
            message = f"[{timestamp}] Unknown action: {action}"
        
        if simulate:
            print(f"SIMULATION: {message}")
            # In real implementation, replace with actual API calls like:
            # self._call_smart_home_api(action)
        else:
            print(message)
            # Actual implementation would go here
            # Example for various systems:
            # if using Philips Hue: call hue API
            # if using MQTT: publish to topic
            # if using HTTP: call local API endpoint
        
        self.save_state(action.upper())
        return message

def main():
    parser = argparse.ArgumentParser(description="Control lights based on daytime/nighttime")
    parser.add_argument("--night-start", type=int, default=DEFAULT_NIGHT_START_HOUR,
                        help=f"Hour when night starts (0-23, default: {DEFAULT_NIGHT_START_HOUR})")
    parser.add_argument("--night-end", type=int, default=DEFAULT_NIGHT_END_HOUR,
                        help=f"Hour when night ends (0-23, default: {DEFAULT_NIGHT_END_HOUR})")
    parser.add_argument("--timezone", type=str, default=TIMEZONE,
                        help=f"Timezone for calculations (default: {TIMEZONE})")
    parser.add_argument("--check", action="store_true",
                        help="Just check current state and exit")
    parser.add_argument("--transition-info", action="store_true",
                        help="Show information about upcoming transitions")
    parser.add_argument("--force-on", action="store_true",
                        help="Force lights ON regardless of time")
    parser.add_argument("--force-off", action="store_true",
                        help="Force lights OFF regardless of time")
    parser.add_argument("--simulate", action="store_true", default=True,
                        help="Run in simulation mode (default: don't actually control lights)")
    parser.add_argument("--real", action="store_true",
                        help="Actually control lights (overrides --simulate)")
    
    args = parser.parse_args()
    
    # Validate hours
    if not (0 <= args.night_start <= 23):
        print("Error: --night-start must be between 0 and 23", file=sys.stderr)
        sys.exit(1)
    if not (0 <= args.night_end <= 23):
        print("Error: --night-end must be between 0 and 23", file=sys.stderr)
        sys.exit(1)
    
    # Determine if we should actually control lights or just simulate
    simulate = args.simulate and not args.real
    
    controller = LightingController(
        night_start_hour=args.night_start,
        night_end_hour=args.night_end,
        timezone_str=args.timezone
    )
    
    if args.force_on:
        controller.control_lights("ON", simulate=simulate)
    elif args.force_off:
        controller.control_lights("OFF", simulate=simulate)
    elif args.transition_info:
        info = controller.get_transition_info()
        print(json.dumps(info, indent=2))
    elif args.check:
        state = controller.get_light_state()
        print(f"Current time: {controller.get_current_time().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Is nighttime: {controller.is_nighttime()}")
        print(f"Lights should be: {state}")
    else:
        # Default behavior: check and control lights based on time
        state = controller.get_light_state()
        print(f"Current time: {controller.get_current_time().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Is nighttime: {controller.is_nighttime()}")
        print(f"Lights should be: {state}")
        controller.control_lights(state, simulate=simulate)

if __name__ == "__main__":
    main()