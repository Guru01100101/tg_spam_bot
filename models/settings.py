# settings.py

import os
import re
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Main bot settings
# BOT_TOKEN is loaded in main.py and passed to the bot class
# Spam filter settings
SPAM_PATTERN_STRING = r'([рp][уy]бл(и|ей|ий|ями|я)?)|([уy]д[аa]л[еe]нн[оo])|(₽)|(\$)'
# The pattern will be compiled in the SpamFilter class

# Admin panel settings
def get_admin_ids():
    """Get admin IDs from environment variable"""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if not admin_ids_str:
        return []
    
    try:
        # Parse comma-separated IDs
        admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
        return admin_ids
    except ValueError:
        print("Warning: Invalid ADMIN_IDS format in .env file")
        return []

def get_all_admin_ids():
    """Get all admin IDs (from .env + dynamic admins)"""
    env_admins = get_admin_ids()
    dynamic_admins = get_dynamic_admin_ids()
    return list(set(env_admins + dynamic_admins))

def get_dynamic_admin_ids():
    """Get dynamically added admin IDs"""
    try:
        if os.path.exists("admins.json"):
            with open("admins.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading dynamic admins: {e}")
    return []

def save_dynamic_admin_ids(admin_ids: list):
    """Save dynamically added admin IDs"""
    try:
        with open("admins.json", "w", encoding="utf-8") as f:
            json.dump(admin_ids, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving dynamic admins: {e}")

def add_dynamic_admin(admin_id: int) -> bool:
    """Add a new dynamic admin"""
    if admin_id in get_admin_ids():  # Don't add if already in .env
        return False
    
    dynamic_admins = get_dynamic_admin_ids()
    if admin_id not in dynamic_admins:
        dynamic_admins.append(admin_id)
        save_dynamic_admin_ids(dynamic_admins)
        return True
    return False

def remove_dynamic_admin(admin_id: int) -> bool:
    """Remove a dynamic admin"""
    if admin_id in get_admin_ids():  # Can't remove .env admins
        return False
    
    dynamic_admins = get_dynamic_admin_ids()
    if admin_id in dynamic_admins:
        dynamic_admins.remove(admin_id)
        save_dynamic_admin_ids(dynamic_admins)
        return True
    return False

def is_env_admin(admin_id: int) -> bool:
    """Check if admin is from .env file"""
    return admin_id in get_admin_ids()

ADMIN_IDS = get_all_admin_ids()
MUTE_DURATION_DAYS = int(os.getenv("MUTE_DURATION_DAYS", 2)) or 2   # наприклад, 2 дні
BAN_DURATION_DAYS = int(os.getenv("BAN_DURATION_DAYS", 30)) or 30   # наприклад, 30 днів