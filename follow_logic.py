import os
import json
import time
import random
import datetime
from instagrapi import Client
from instagrapi.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

# Constants
TARGETS_FILE = "targets.json"
ALREADY_FOLLOWED_FILE = "already_followed.json"
FOLLOWS_TODAY_FILE = "follows_today.json"
LAST_REFRESH_FILE = "last_follow_refresh.txt"
LOG_FILE = "bot.log"
SESSION_FILE = "session.json"

# Configuration
MIN_SLEEP = 45
MAX_SLEEP = 120
ERROR_SLEEP = 300
DAILY_LIMIT = 25
MAX_FEEDBACK_ERRORS = 2
STRATEGIC_DELAY_INTERVAL = 8
STRATEGIC_DELAY_MIN = 120
STRATEGIC_DELAY_MAX = 300

def refresh_targets_if_needed():
    if not os.path.exists(LAST_REFRESH_FILE):
        return True
    with open(LAST_REFRESH_FILE, "r") as f:
        last = datetime.datetime.strptime(f.read().strip(), "%Y-%m-%d")
    return (datetime.datetime.now() - last).days >= 1

def update_last_refresh():
    with open(LAST_REFRESH_FILE, "w") as f:
        f.write(datetime.datetime.now().strftime("%Y-%m-%d"))

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")

def safe_json_load(file_path, default=None):
    if default is None:
        default = []
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return default

def challenge_code_handler(username, choice):
    # For manual code input during challenges
    if choice and choice.isdigit():
        return input(f"Enter verification code for {username}: ")
    return False

def run_follow_logic():
    cl = Client()
    cl.challenge_code_handler = challenge_code_handler
    
    # Session management
    try:
        if os.path.exists(SESSION_FILE):
            cl.load_settings(SESSION_FILE)
            log("🔑 Session loaded")
    except Exception as e:
        log(f"⚠️ Couldn't load session: {str(e)}")
    
    try:
        cl.login(os.getenv("IG_USERNAME"), os.getenv("IG_PASSWORD"))
        if os.path.exists(SESSION_FILE):
            cl.dump_settings(SESSION_FILE)
        log("🔑 Login successful")
    except Exception as e:
        log(f"❌ Login failed: {str(e)}")
        return

    # Target refresh logic
    if refresh_targets_if_needed():
        log("🔁 Refreshing targets...")
        update_last_refresh()

    # Load data files
    targets = safe_json_load(TARGETS_FILE, [])
    already_followed = set(safe_json_load(ALREADY_FOLLOWED_FILE, []))
    daily_data = safe_json_load(FOLLOWS_TODAY_FILE, {})
    
    # Reset daily counter if new day
    today = datetime.date.today().isoformat()
    if daily_data.get("date") != today:
        daily_data = {"date": today, "count": 0}
        log("🔄 New day - reset follow counter")

    feedback_errors = 0
    successful_follows = 0
    total_attempts = 0

    for username in targets:
        # Exit conditions
        if daily_data["count"] >= DAILY_LIMIT:
            log(f"🚫 Daily limit reached ({DAILY_LIMIT} follows)")
            break
        if feedback_errors >= MAX_FEEDBACK_ERRORS:
            log("❌ Max feedback errors reached - stopping")
            break

        # Skip already followed users
        if username in already_followed:
            continue

        total_attempts += 1

        # Strategic delay every X follows
        if successful_follows > 0 and successful_follows % STRATEGIC_DELAY_INTERVAL == 0:
            delay = random.uniform(STRATEGIC_DELAY_MIN, STRATEGIC_DELAY_MAX)
            log(f"⏳ Strategic delay after {successful_follows} follows: {delay:.1f}s")
            time.sleep(delay)
            
        # Progress logging
        if total_attempts % 5 == 0:
            log(f"ℹ️ Progress: {daily_data['count']}/{DAILY_LIMIT} follows today")

        try:
            user_id = cl.user_id_from_username(username)
            cl.user_follow(user_id)
            
            successful_follows += 1
            daily_data["count"] += 1
            already_followed.add(username)
            
            log(f"✅ Followed {username} ({daily_data['count']}/{DAILY_LIMIT} today)")
            
            # Random delay between follows
            delay = random.uniform(MIN_SLEEP, MAX_SLEEP)
            time.sleep(delay)

        except ClientError as e:
            error_msg = str(e).lower()
            log(f"❌ Error following {username}: {e}")

            if "feedback_required" in error_msg:
                feedback_errors += 1
                log(f"⚠️ Feedback required ({feedback_errors}/{MAX_FEEDBACK_ERRORS})")
                time.sleep(ERROR_SLEEP)
            elif "wait a few minutes" in error_msg:
                cool_down = 600
                log(f"⏳ Instagram cooldown - sleeping {cool_down}s")
                time.sleep(cool_down)
            elif "too many requests" in error_msg:
                cool_down = 900
                log(f"⏳ Rate limited - sleeping {cool_down}s")
                time.sleep(cool_down)

        except Exception as e:
            log(f"❌ Unexpected error following {username}: {e}")
            time.sleep(ERROR_SLEEP)

    # Save progress
    try:
        with open(ALREADY_FOLLOWED_FILE, "w") as f:
            json.dump(list(already_followed), f, indent=2)
        with open(FOLLOWS_TODAY_FILE, "w") as f:
            json.dump(daily_data, f, indent=2)
        log(f"💾 Saved progress: {daily_data['count']} follows today")
    except Exception as e:
        log(f"❌ Failed to save progress: {e}")

    log("🏁 Follow logic completed")