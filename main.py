from keep_alive import keep_alive
from follow_logic import run_follow_logic
from refresh_targets import refresh_targets
from openai import OpenAI
import time
import random
import json
import os
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

# Setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
keep_alive()

# Constants
USED_INDEX_FILE = "used_captions.json"
REFRESH_FILE = "last_refresh.txt"
POST_LIMIT_FILE = "posts_today.json"
MAX_DAILY_POSTS = 2

with open("caption_prompt_pairs.json", "r") as f:
    caption_prompt_pairs = json.load(f)

def load_used_indices():
    if os.path.exists(USED_INDEX_FILE):
        with open(USED_INDEX_FILE, "r") as f:
            return json.load(f)
    return []

def save_used_indices(indices):
    with open(USED_INDEX_FILE, "w") as f:
        json.dump(indices, f)

def get_unique_pair():
    used = load_used_indices()
    if len(used) == len(caption_prompt_pairs):
        print("⚠️ All captions used! Restarting from beginning.")
        used = []
    while True:
        i = random.randint(0, len(caption_prompt_pairs) - 1)
        if i not in used:
            used.append(i)
            save_used_indices(used)
            return caption_prompt_pairs[i]

def generate_image(prompt_text, size="1024x1024", output_path="generated_image.png", retries=3):
    for attempt in range(retries):
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt_text,
                size=size,
                quality="standard",
                n=1
            )
            image_url = response.data[0].url
            img_data = requests.get(image_url).content
            with open(output_path, 'wb') as f:
                f.write(img_data)
            print("📸 Image saved locally:", output_path)
            return image_url
        except Exception as e:
            if attempt == retries - 1:
                print("❌ Image generation failed after retries:", e)
                return None
            print(f"⚠️ Retrying image generation ({attempt + 1}/{retries})...")
            time.sleep(5)

def should_refresh_targets():
    if not os.path.exists(REFRESH_FILE):
        return True
    with open(REFRESH_FILE, "r") as f:
        last_time = datetime.datetime.strptime(f.read(), "%Y-%m-%d")
    return (datetime.datetime.now() - last_time).days >= 1

def update_last_refresh_time():
    with open(REFRESH_FILE, "w") as f:
        f.write(datetime.datetime.now().strftime("%Y-%m-%d"))

def check_post_limit():
    today = datetime.date.today().isoformat()
    try:
        with open(POST_LIMIT_FILE, "r") as f:
            data = json.load(f)
            if data.get("date") == today and data.get("count", 0) >= MAX_DAILY_POSTS:
                return True
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return False

def update_post_count():
    today = datetime.date.today().isoformat()
    try:
        with open(POST_LIMIT_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"date": today, "count": 0}
    
    if data.get("date") != today:
        data = {"date": today, "count": 1}
    else:
        data["count"] = data.get("count", 0) + 1
    
    with open(POST_LIMIT_FILE, "w") as f:
        json.dump(data, f)

# Configuration
action = 3  # 1 = Post only, 2 = Follow only, 3 = Both
DEBUG = True

# Main Execution
if should_refresh_targets():
    print("🔁 Refreshing targets.json automatically...")
    refresh_targets()
    update_last_refresh_time()

# Action sequencing
if action in [1, 3] and not check_post_limit():  # Posting modes
    pair = get_unique_pair()
    caption = pair["caption"]
    prompt = pair["prompt"]
    print("\n📝 POSTING:", caption)
    print("🎯 Prompt:", prompt)

    size = "1024x1024" if "Day 70" in caption or "Day 71" in caption else "512x512"
    image_url = generate_image(prompt, size=size)

    if image_url:
        print("🖼️ IMAGE URL:", image_url)
        update_post_count()
    else:
        print("⚠️ No image was generated.")
    
    # Add delay between posting and following
    if action == 3:
        delay = random.uniform(120, 300)
        print(f"⏳ Waiting {delay:.1f}s between posting and following...")
        time.sleep(delay)

if action in [2, 3]:  # Following modes
    print("\n🤝 Running follow logic...")
    run_follow_logic()

if action not in [1, 2, 3]:
    print("💤 Silent cycle... No post or follow.")