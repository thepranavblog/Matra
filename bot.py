"""
Mātra — Your Desi Fitness OS
Telegram Bot Prototype

Setup:
    pip install python-telegram-bot anthropic python-dotenv
    Add TELEGRAM_TOKEN and ANTHROPIC_API_KEY to .env
    python bot.py
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler,
)
from dotenv import load_dotenv
import os

from ai_engine import get_matra_response
from storage import load_user, save_user

load_dotenv()
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ── Onboarding questions ──────────────────────────────────────────────────────
ONBOARDING_QUESTIONS = [
    ("name",          "What's your name?"),
    ("age",           "How old are you?"),
    ("weight_kg",     "Current weight in kg?"),
    ("height_cm",     "Height in cm?"),
    ("goal",          "Main goal?\n\n1️⃣ Gain muscle\n2️⃣ Lose fat\n3️⃣ Maintain & stay fit\n\nType 1, 2 or 3."),
    ("gym_days",      "How many days a week do you gym? (e.g. 3)"),
    ("diet_type",     "Vegetarian or non-vegetarian?"),
    ("cook_situation","Who mostly cooks your meals?\n\n1️⃣ Home cook / mum / spouse\n2️⃣ I cook myself\n3️⃣ Mix of home + office canteen\n\nType 1, 2 or 3."),
    ("city",          "Which city are you in? (helps with food suggestions)"),
]

GOAL_MAP = {"1": "gain muscle", "2": "lose fat", "3": "maintain & stay fit"}
COOK_MAP = {"1": "home cook", "2": "self cook", "3": "mix of home cook + office canteen"}


# ── /start ────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = load_user(user_id)

    if user.get("profile_complete"):
        name = user["profile"].get("name", "bhai")
        await update.message.reply_text(
            f"Welcome back, {name}! 💪\n\n"
            "Gym day or rest day today?\n\n"
            "Just talk to me naturally — tell me what you ate, "
            "what you trained, or ask me anything.\n\n"
            "Commands:\n"
            "/summary — today's nutrition snapshot\n"
            "/reset — clear your profile"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🏋️ *Welcome to Mātra* — your desi fitness OS.\n\n"
        "I'm your gym + nutrition coach. I'll remember your workouts, "
        "track your macros, and give you suggestions that actually make "
        "sense for Indian food and your lifestyle.\n\n"
        "Let's set up your profile real quick.\n\n"
        "What's your name?",
        parse_mode="Markdown"
    )
    context.user_data["step"] = 0
    context.user_data["onboarding"] = {}
    return "ONBOARDING"


# ── Onboarding handler ────────────────────────────────────────────────────────
async def handle_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step", 0)
    data = context.user_data.get("onboarding", {})
    text = update.message.text.strip()

    key, _ = ONBOARDING_QUESTIONS[step]

    # Normalise choice fields
    if key == "goal":
        text = GOAL_MAP.get(text, text)
    elif key == "cook_situation":
        text = COOK_MAP.get(text, text)

    data[key] = text
    context.user_data["onboarding"] = data
    step += 1
    context.user_data["step"] = step

    if step < len(ONBOARDING_QUESTIONS):
        _, next_q = ONBOARDING_QUESTIONS[step]
        await update.message.reply_text(next_q)
        return "ONBOARDING"

    # ── Profile complete ──
    user_id = str(update.effective_user.id)
    user = load_user(user_id)
    user["profile"] = data
    user["profile_complete"] = True
    user["joined"] = datetime.now().isoformat()
    user["history"] = []      # workout + meal logs live here
    save_user(user_id, user)

    name = data.get("name", "bhai")
    await update.message.reply_text(
        f"✅ All set, {name}!\n\n"
        f"*Goal:* {data.get('goal')}\n"
        f"*Gym:* {data.get('gym_days')} days/week\n"
        f"*Diet:* {data.get('diet_type')}\n"
        f"*Meals:* {data.get('cook_situation')}\n\n"
        "Now just talk to me naturally 👇\n\n"
        "🏋️ Tell me what you trained today\n"
        "🍽️ Tell me what you ate\n"
        "💬 Ask me anything\n\n"
        "So — gym day or rest day today?",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ── Main chat ─────────────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = load_user(user_id)

    if not user.get("profile_complete"):
        await update.message.reply_text("Type /start to set up your profile first.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    response = await get_matra_response(user_id, user, update.message.text.strip())
    await update.message.reply_text(response, parse_mode="Markdown")


# ── /summary ──────────────────────────────────────────────────────────────────
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = load_user(user_id)
    if not user.get("profile_complete"):
        await update.message.reply_text("Set up your profile first — type /start")
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    response = await get_matra_response(
        user_id, user,
        "Give me today's full nutrition summary and one specific suggestion for tomorrow."
    )
    await update.message.reply_text(response, parse_mode="Markdown")


# ── /reset ────────────────────────────────────────────────────────────────────
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(str(update.effective_user.id), {})
    await update.message.reply_text("Profile cleared. Type /start to begin again.")


# ── Run ───────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={"ONBOARDING": [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_onboarding)]},
        fallbacks=[CommandHandler("start", start)],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🏋️ Mātra is live.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
