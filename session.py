from datetime import datetime

POLL_START = 8
POLL_END   = 18

def is_session_active() -> bool:
    hour = datetime.now().hour
    return POLL_START <= hour < POLL_END

def current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def time_remaining() -> str:
    now  = datetime.now()
    end  = now.replace(hour=POLL_END, minute=0, second=0)
    diff = end - now
    if diff.total_seconds() <= 0:
        return "Session Ended"
    hours, rem = divmod(int(diff.total_seconds()), 3600)
    mins = rem // 60
    return f"{hours}h {mins}m remaining"
