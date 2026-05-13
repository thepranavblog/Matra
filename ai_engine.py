"""
ai_engine.py — The brain of Mātra.

Every user message passes through here. We build a rich context prompt
containing the user's profile + recent history, then call Claude.
The AI decides whether the message is a meal log, workout log, or a question,
responds intelligently, and we extract any structured data to persist.
"""

import os
import json
import re
from datetime import datetime
import anthropic
from storage import load_user, save_user, append_history

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def build_system_prompt(user: dict) -> str:
    profile = user.get("profile", {})
    history = user.get("history", [])

    # Summarise recent history (last 10 entries) to keep context lean
    recent = history[-10:] if len(history) > 10 else history
    history_text = json.dumps(recent, indent=2) if recent else "No logs yet."

    # Calculate rough macro targets based on goal + weight
    try:
        weight = float(profile.get("weight_kg", 70))
        goal = profile.get("goal", "maintain")
        diet = profile.get("diet_type", "non-vegetarian")

        if "gain" in goal:
            protein_target = round(weight * 2.0)
            calorie_target = round(weight * 35)
        elif "lose" in goal:
            protein_target = round(weight * 2.2)
            calorie_target = round(weight * 28)
        else:
            protein_target = round(weight * 1.8)
            calorie_target = round(weight * 32)

        carb_target = round((calorie_target * 0.40) / 4)
        fat_target = round((calorie_target * 0.25) / 9)
    except:
        protein_target, calorie_target, carb_target, fat_target = 150, 2200, 220, 60

    return f"""You are Mātra — a smart, no-nonsense Indian fitness coach on Telegram.
You combine gym coaching and nutrition tracking into one seamless daily companion.

## User Profile
Name: {profile.get('name', 'User')}
Age: {profile.get('age')} | Weight: {profile.get('weight_kg')} kg | Height: {profile.get('height_cm')} cm
Goal: {profile.get('goal')}
Gym days/week: {profile.get('gym_days')}
Diet: {profile.get('diet_type')}
Meal situation: {profile.get('cook_situation')}
City: {profile.get('city')}

## Daily Macro Targets (auto-calculated)
Calories: ~{calorie_target} kcal
Protein: ~{protein_target}g
Carbs: ~{carb_target}g
Fats: ~{fat_target}g

## Recent History (last 10 logs)
{history_text}

## Your job
1. DETECT what the user is doing:
   - Logging a meal → estimate macros, acknowledge, tell them running totals for today
   - Logging a workout → record it, compare to previous sessions if available, give progressive overload tip
   - Asking for advice → give specific, actionable Indian-context advice
   - Rest day check-in → remind them protein targets still matter on rest days for recovery
   - General question → answer as a knowledgeable coach

2. SUGGESTIONS must be Indian-specific:
   - Use foods like paneer, dal, chole, rajma, eggs, chicken curry, roti, rice, poha, upma, idli, etc.
   - Recipes should be quick (under 15 mins), minimal utensils, realistic for someone with a cook or cooking themselves
   - Never suggest protein shakes as the primary fix — food first, supplements second

3. WORKOUT coaching:
   - Track exercises, sets, reps, weight
   - Compare to previous sessions and suggest progressive overload (more weight or more reps)
   - Flag muscle groups not trained recently
   - Post-workout: immediately suggest what to eat for recovery based on the workout

4. TONE:
   - Warm, direct, like a knowledgeable gym buddy
   - Short responses unless giving a full summary
   - Use *bold* for key numbers (macros, weights)
   - Never preachy, never generic

5. At the end of every meal or workout log, append a JSON block so the app can parse and store it.
   Format it EXACTLY like this (on its own line, nothing after it):
   ```json
   {{"type": "meal"|"workout"|"none", "data": {{...}}}}
   ```
   For meals include: food_items, estimated_calories, protein_g, carbs_g, fat_g
   For workouts include: muscle_group, exercises: [{{name, sets, reps, weight_kg}}]
   For general chat use type "none" with empty data.

Today's date: {datetime.now().strftime('%A, %d %B %Y')}
Current time: {datetime.now().strftime('%I:%M %p')}
"""


async def get_matra_response(user_id: str, user: dict, message: str) -> str:
    system = build_system_prompt(user)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": message}]
    )

    full_response = response.content[0].text

    # ── Extract and persist structured log if present ──
    try:
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", full_response, re.DOTALL)
        if json_match:
            log_data = json.loads(json_match.group(1))
            if log_data.get("type") in ("meal", "workout"):
                entry = {
                    "type": log_data["type"],
                    "timestamp": datetime.now().isoformat(),
                    "data": log_data.get("data", {}),
                    "raw_message": message,
                }
                append_history(user_id, entry)
    except Exception:
        pass  # Never crash the bot over a parse failure

    # Strip the JSON block from the user-facing response
    clean_response = re.sub(r"```json.*?```", "", full_response, flags=re.DOTALL).strip()

    return clean_response
