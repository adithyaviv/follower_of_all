from instagrapi import Client
from instagrapi.exceptions import ClientError, UserNotFound
import json
import os
import time
import random
import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")
SESSION_FILE = "session.json"

# Targeting parameters
SOURCE_USERNAMES = ["nasa", "beeple_crap", "obeygiant", "pubity"]
NUM_TARGETS_PER_SOURCE = 100
HASHTAGS = ["digitalart", "artlife", "loneliness"]
NUM_HASHTAG_USERS = 100

# Engagement filters
MIN_LIKES = 50
MIN_COMMENTS = 5
MIN_FOLLOWERS = 100
MIN_POSTS = 3
MIN_CAPTION_LENGTH = 10

# Files
TARGETS_FILE = "targets.json"
ARCHIVE_FILE = "already_followed.json"
LOG_FILE = "refresh_log.txt"

# Rate limiting
DELAY_BETWEEN_REQUESTS = random.uniform(5, 10)
ERROR_DELAY = 60

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

def safe_json_load(filename, default=None):
    if default is None:
        default = []
    try:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log(f"⚠️ Error loading {filename}: {str(e)}")
    return default

def challenge_code_handler(username, choice):
    # For manual code input during challenges
    if choice and choice.isdigit():
        return input(f"Enter verification code for {username}: ")
    return False

def initialize_client():
    cl = Client()
    cl.challenge_code_handler = challenge_code_handler
    
    try:
        # Try loading existing session
        if os.path.exists(SESSION_FILE):
            cl.load_settings(SESSION_FILE)
            log("🔑 Session loaded")
            return cl
        
        # New login
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings(SESSION_FILE)
        log("🔑 New login successful")
        return cl
    except Exception as e:
        log(f"❌ Login failed: {str(e)}")
        return None

def get_following_targets(cl, username, limit):
    targets = set()
    try:
        log(f"🔍 Scraping users followed by @{username}")
        user_id = cl.user_id_from_username(username)
        following = cl.user_following(user_id, amount=limit)
        
        for user in following.values():
            try:
                # Skip private/invalid users
                if user.is_private or not user.username:
                    continue
                
                # Get full user info for detailed attributes
                user_info = cl.user_info(user.pk)
                
                # Get attributes safely
                follower_count = getattr(user_info, 'follower_count', 0)
                media_count = getattr(user_info, 'media_count', 0)
                
                # Apply filters
                if (follower_count < MIN_FOLLOWERS or 
                    media_count < MIN_POSTS or 
                    not getattr(user_info, 'biography', None)):
                    continue
                
                targets.add(user.username)
                log(f"➕ Added @{user.username} (Followers: {follower_count})")
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
            except (ClientError, UserNotFound) as e:
                log(f"⚠️ User info error: {str(e)}")
                continue
            except Exception as e:
                log(f"⚠️ Unexpected error: {str(e)}")
                continue
                
    except Exception as e:
        log(f"❌ Error scraping @{username}: {str(e)}")
        time.sleep(ERROR_DELAY)
    
    return targets

def get_hashtag_targets(cl, tag, limit):
    targets = set()
    try:
        log(f"🔍 Searching hashtag: #{tag}")
        medias = cl.hashtag_medias_top(tag, amount=limit)
        
        for media in medias:
            try:
                # Skip if invalid media
                if not hasattr(media, 'user') or not media.user.username:
                    continue
                
                username = media.user.username
                
                # Get full user info
                user_info = cl.user_info_by_username(username)
                
                # Get attributes safely
                follower_count = getattr(user_info, 'follower_count', 0)
                media_count = getattr(user_info, 'media_count', 0)
                like_count = getattr(media, 'like_count', 0)
                comment_count = getattr(media, 'comment_count', 0)
                caption = getattr(media, 'caption_text', '')
                
                # Apply filters
                if (user_info.is_private or 
                    media_count < MIN_POSTS or 
                    follower_count < MIN_FOLLOWERS or
                    (like_count < MIN_LIKES and comment_count < MIN_COMMENTS) or
                    len(caption) < MIN_CAPTION_LENGTH):
                    continue
                
                targets.add(username)
                log(f"➕ Added @{username} from #{tag} ({like_count} likes)")
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
            except (ClientError, UserNotFound) as e:
                log(f"⚠️ User error: {str(e)}")
                continue
            except Exception as e:
                log(f"⚠️ Media processing error: {str(e)}")
                continue
                
    except Exception as e:
        log(f"❌ Hashtag search failed for #{tag}: {str(e)}")
        time.sleep(ERROR_DELAY)
    
    return targets

def refresh_targets():
    log("🔄 Starting target refresh")
    
    cl = initialize_client()
    if not cl:
        log("❌ Aborting refresh - client initialization failed")
        return
    
    targets_set = set()
    
    # Get targets from sources
    for source in SOURCE_USERNAMES:
        new_targets = get_following_targets(cl, source, NUM_TARGETS_PER_SOURCE)
        targets_set.update(new_targets)
        log(f"🔍 Found {len(new_targets)} targets from @{source}")
        time.sleep(random.uniform(15, 30))
    
    # Get targets from hashtags
    for tag in HASHTAGS:
        new_targets = get_hashtag_targets(cl, tag, NUM_HASHTAG_USERS)
        targets_set.update(new_targets)
        log(f"🔍 Found {len(new_targets)} targets from #{tag}")
        time.sleep(random.uniform(15, 30))
    
    # Filter out already followed
    already_followed = set(safe_json_load(ARCHIVE_FILE, []))
    final_targets = sorted(list(targets_set - already_followed))
    
    # Save results
    with open(TARGETS_FILE, "w") as f:
        json.dump(final_targets, f, indent=2)
    
    log(f"✅ Refresh complete. Found {len(final_targets)} new targets")
    log("──────────────────────────────")

if __name__ == "__main__":
    refresh_targets()