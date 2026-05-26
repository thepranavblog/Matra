"""
Mātra — Your Desi Fitness OS
Telegram Bot

Setup:
    pip install -r requirements.txt
    cp .env.example .env
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
    ("name",           None),
    ("age",            None),  # personalised with name after Q1
    ("weight_kg",      "What's your current weight in kg?"),
    ("height_cm",      "And your height in cm?"),
    ("goal",           "Alright, what are we working towards?\nTrying to bulk up, cut down, or just stay consistent?"),
    ("gym_days",       None),  # goal reaction injected dynamically
    ("experience",     "Got it. Are you just starting out, been lifting for a year or two, or have you been at this for a while?"),
    ("diet_type",      "Quick one — vegetarian or non-vegetarian?"),
    ("cook_situation", "Tell me about your meals — who cooks, do you eat out, office canteen? Just give me a rough picture."),
    ("wake_up_time",   "Last one — what time do you usually wake up?"),
]

GOAL_REACTIONS = {
    "bulk":      "Bulk mode ON 🔥 Every session and every meal is going to count.",
    "gain":      "Bulk mode ON 🔥 Every session and every meal is going to count.",
    "muscle":    "Bulk mode ON 🔥 Every session and every meal is going to count.",
    "cut":       "Cut mode. We're going to be smart about this — lose fat, keep the muscle.",
    "lose":      "Cut mode. We're going to be smart about this — lose fat, keep the muscle.",
    "fat":       "Cut mode. We're going to be smart about this — lose fat, keep the muscle.",
    "maintain":  "Staying consistent is underrated. Let's keep you dialled in.",
    "consistent":"Staying consistent is underrated. Let's keep you dialled in.",
}


# ── /start ────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = load_user(user_id)

    if user.get("profile_complete"):
        name = user["profile"].get("name", "")
        await update.message.reply_text(
            f"Welcome back{', ' + name if name else ''}! 💪\n\n"
            "Gym day or rest day today?\n\n"
            "Just talk to me — tell me what you ate, what you trained, or ask me anything.\n\n"
            "Commands:\n"
            "/summary — today's nutrition snapshot\n"
            "/reset — clear your profile"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Yo! Welcome to Mātra 🏋️ I'm your gym and nutrition coach.\n"
        "Let's get you set up real quick. What do I call you?"
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
    data[key] = text
    context.user_data["onboarding"] = data
    step += 1
    context.user_data["step"] = step

    if step < len(ONBOARDING_QUESTIONS):
        next_key, next_q = ONBOARDING_QUESTIONS[step]

        if next_key == "age":
            name = data.get("name", "")
            await update.message.reply_text(f"{name}, let's get it! 💪 How old are you?")
        elif next_key == "gym_days":
            goal_text = data.get("goal", "").lower()
            reaction = next(
                (msg for kw, msg in GOAL_REACTIONS.items() if kw in goal_text),
                "Staying consistent is underrated. Let's keep you dialled in."
            )
            await update.message.reply_text(reaction)
            await update.message.reply_text("How many days a week are you hitting the gym?")
        else:
            await update.message.reply_text(next_q)
        return "ONBOARDING"

    # ── Profile complete ──
    user_id = str(update.effective_user.id)
    user = load_user(user_id)
    user["profile"] = data
    user["profile_complete"] = True
    user["joined"] = datetime.now().isoformat()
    user["history"] = []
    save_user(user_id, user)

    await update.message.reply_text(
        f"You're all set! Here's what I've got on you:\n\n"
        f"Goal: {data.get('goal')}\n"
        f"Gym: {data.get('gym_days')} days/week\n"
        f"Experience: {data.get('experience')}\n"
        f"Diet: {data.get('diet_type')}\n"
        f"Wake up: {data.get('wake_up_time')}\n\n"
        "Now just talk to me like you'd talk to your gym buddy.\n"
        "Tell me what you trained, what you ate, or ask me anything.\n"
        "Let's get to work 💪"
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
    summary_prompt = (
        "Give me today's end of day summary in this exact structure:\n\n"
        "1. What I ate today and estimated macros (calories, protein, carbs, fat)\n"
        "2. How I'm tracking against my daily targets — what I hit, what I missed\n"
        "3. Workout done today if any\n"
        "4. One specific action for tomorrow to correct or build on today\n\n"
        "Keep it punchy. Gym bro tone. No long paragraphs."
    )
    response = await get_matra_response(user_id, user, summary_prompt)
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
