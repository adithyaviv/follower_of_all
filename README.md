# Follower of All 🤖📱

A performance art Instagram bot designed to simulate digital connection by following users and posting emotionally resonant content. Built using `instagrapi`, `Python`, and OpenAI-powered caption/image generation.

## 💡 Purpose
This project explores themes of **digital loneliness**, **algorithmic emotion**, and **automated connection-seeking** through a parody Instagram account that:
- Follows verified or targeted users daily
- Posts surreal images with emotionally charged captions
- Logs every action, simulates human behavior, and respects antiban safety

## 🧠 Features
- 🧬 Human-like delays and random behavior
- 🗂 JSON-based tracking for posts, follows, used captions
- 🌅 71-day narrative arc ending with a bot monologue
- 🔁 Automatic target refreshing and safe session saving
- ⚠️ Feedback error handling, daily follow limit, chunk breaks

## 📂 Files
| File | Purpose |
|------|---------|
| `follow_logic.py` | Main bot logic to follow accounts daily |
| `caption_prompt_pairs.json` | Pre-written emotional captions + DALL·E prompts |
| `used_captions.json` | Tracks which captions have been used |
| `targets.json` | List of accounts to follow |
| `already_followed.json` | Prevents duplicate follows |
| `follows_today.json` | Tracks daily follow count |
| `last_post_time.txt` | Controls post cooldowns |
| `bot.log` | Logs daily activity |
| `.env` | Stores IG_USERNAME and IG_PASSWORD (not committed) |

## 📸 Tech Stack
- `Python 3.12+`
- [`instagrapi`](https://github.com/adw0rd/instagrapi)
- `dotenv`
- `requests`
- Optional: `OpenAI API` + `DALL·E 3` for image generation

## 🛠 Setup

1. Clone the repo:
```bash
git clone https://github.com/adithyaviv/follower_of_all.git
cd follower_of_all
