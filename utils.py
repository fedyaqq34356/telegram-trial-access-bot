from datetime import datetime
from typing import Optional

def format_username(username: Optional[str]) -> str:
    return f"@{username}" if username else "тег отсутствует"

def get_status_emoji(status: str) -> str:
    return "🟢" if status == "approved" else "🟡"

def minutes_remaining(trial_end: str) -> int:
    end_date = datetime.fromisoformat(trial_end)
    delta = end_date - datetime.now()
    return max(0, int(delta.total_seconds() / 60))

def format_time_remaining(minutes: int) -> str:
    if minutes <= 0:
        return "Истек"
    
    days = minutes // (24 * 60)
    hours = (minutes % (24 * 60)) // 60
    mins = minutes % 60
    
    return f"{days} д. {hours} ч. {mins} мин."

def format_user_info(user, show_time: bool = False) -> str:
    name = user['name']
    uid = user['telegram_id']
    tag = format_username(user['username'])
    status = get_status_emoji(user['status'])
    
    info = f"{status} {name}\nID: {uid}\n{tag}"
    
    if show_time and user['status'] == 'trial':
        minutes = minutes_remaining(user['trial_end_date'])
        time_str = format_time_remaining(minutes)
        info += f"\nОсталось: {time_str}"
    
    return info

def format_user_list_item(user, show_status: bool = True) -> str:
    uid = user['telegram_id']
    tag = format_username(user['username'])
    name = user['name']
    
    result = f"{uid} | {tag} | {name}"
    
    if show_status:
        if user['status'] == 'trial':
            minutes = minutes_remaining(user['trial_end_date'])
            time_str = format_time_remaining(minutes)
            result += f" | {time_str}"
        else:
            result += " | Оставлен"
    
    return result

def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]