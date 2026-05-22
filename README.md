<h1 align="center">🏋️ Mātra</h1>
<p align="center"><b>Your Desi Fitness OS — Telegram bot for gym tracking + nutrition, built for urban Indians.</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/Telegram-Bot-2CA5E0?style=flat&logo=telegram" />
  <img src="https://img.shields.io/badge/AI-Groq%20%7C%20Llama%203.3-orange?style=flat" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat" />
</p>

---

## What is Mātra?

Mātra is a conversational fitness companion on Telegram. It combines gym coaching and nutrition tracking into one chat interface — with full Indian food and lifestyle context baked in.

No app downloads. No dashboards. Just talk to it.

---

## Features

| Feature | Description |
|---|---|
| 🏋️ Workout tracking | Log sessions conversationally — "bench 80kg 4x8" |
| 📈 Progressive overload | Compares to last session, nudges you to go heavier |
| 🍽️ Macro tracking | Estimates calories, protein, carbs, fat from your meals |
| 🇮🇳 Indian food context | Thinks in dal, paneer, roti — not chicken & broccoli |
| 🧠 Memory | Remembers your last 10 logs, profile, and targets |
| 📊 Daily summary | `/summary` gives a full nutrition snapshot |
| 😴 Rest day support | Reminds you protein targets still matter on rest days |

---

## Getting Started

### 1. Get your keys

- **Telegram token** → [@BotFather](https://t.me/BotFather) → `/newbot`
- **Groq API key** → [console.groq.com](https://console.groq.com) (free, no credit card)

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Fill in TELEGRAM_TOKEN and GROQ_API_KEY
```

### 4. Run

```bash
python bot.py
```

Open Telegram, find your bot, send `/start`.

---

## Project Structure

```
matra/
├── bot.py            # Telegram handlers + onboarding flow
├── ai_engine.py      # Builds context, calls Groq, parses structured logs
├── storage.py        # JSON file storage (one file per user)
├── data/             # Auto-created at runtime — stores profiles + history
├── requirements.txt
└── .env.example
```

---

## How It Works

Every message goes through `ai_engine.py`:

1. Loads the user's profile + last 10 logs from `data/<user_id>.json`
2. Calculates macro targets from weight + goal
3. Builds a system prompt with full context
4. Calls Groq (`llama-3.3-70b-versatile`)
5. Parses the response for structured meal/workout data and saves it

---

## Roadmap

- [ ] Voice message support
- [ ] Photo meal logging (snap your thali)
- [ ] Weekly report every Sunday
- [ ] Proactive morning check-in at 8am
- [ ] WhatsApp support when proven

---

<p align="center">Built with ❤️ for the Indian fitness community</p>
