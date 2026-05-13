# 🏋️ Mātra — Your Desi Fitness OS

A Telegram bot combining gym coaching + nutrition tracking with full Indian context.

---

## What it does

- Onboards you with a 2-minute profile setup
- Tracks workouts conversationally — "did chest today, bench 80kg 4x8"
- Remembers history — next session: "last time 80kg, try 82.5 today"
- Tracks meals, estimates macros, shows running totals
- Indian-context suggestions — chole, paneer bhurji, dal, not chicken & broccoli
- Rest day intelligence — protein still matters for recovery
- /summary — macro snapshot + tomorrow's suggestion

---

## Setup (10 minutes)

### 1. Get your Telegram Bot Token
Open Telegram → search @BotFather → /newbot → copy the token

### 2. Get your Anthropic API Key
Go to console.anthropic.com → create an API key

### 3. Install and run

    pip install -r requirements.txt
    cp .env.example .env
    # Edit .env with your keys
    python bot.py

Open Telegram, find your bot, send /start.

---

## Project structure

    matra/
    ├── bot.py          — Telegram handlers + onboarding flow
    ├── ai_engine.py    — Builds context, calls Claude, parses logs
    ├── storage.py      — JSON file storage (one file per user)
    ├── data/           — Auto-created, stores profiles + history
    ├── requirements.txt
    └── .env.example

---

## How memory works

Every message → ai_engine.py builds a prompt with:
  - Full user profile (goal, weight, diet, cook situation, city)
  - Last 10 workout + meal logs
  - Auto-calculated macro targets

Sent to Claude on every message. AI parses response for structured data and saves it.

---

## Cost estimate for beta (15-50 users)

- Telegram Bot API: Free
- Claude API: ~Rs 2-5 per user/day
- Hosting (Railway/Render free tier): Free
- Total for 50 users: ~Rs 100-250/day — works at Rs 299/user/month

---

## Next features post-beta

- Voice message support
- Photo meal logging (snap your thali)
- Weekly report every Sunday
- Proactive 8am morning check-in
- WhatsApp migration when proven
