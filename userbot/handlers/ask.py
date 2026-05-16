import time
import re
import asyncio
import google.generativeai as genai
from telethon import events
from shared.state import state, register_handler_doc, maybe_warn_spammer, is_authorized
from config import GEMINI_KEYS

cooldowns = {key: 0 for key in GEMINI_KEYS}
current_index = 0
SET_HANDLER = True

# ----------------------------
# Gemini Helper Functions
# ----------------------------
def get_model(api_key, model_name):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

async def try_gemini(prompt: str, model_name="gemini-2.5-flash"):
    global current_index
    tries = len(GEMINI_KEYS)

    for _ in range(tries):
        key = GEMINI_KEYS[current_index]
        now = time.time()

        if now < cooldowns[key]:
            current_index = (current_index + 1) % len(GEMINI_KEYS)
            continue

        try:
            model = get_model(key, model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                delay = 15
                cooldowns[key] = time.time() + delay
                current_index = (current_index + 1) % len(GEMINI_KEYS)
                continue
            else:
                raise
    return None

def split_text(text, max_length=4096):
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


# ----------------------------
# AI Personality (Single Control Point)
# ----------------------------
async def AI_Personality(user_query: str) -> str:
    prompt = f"""
You are Marin Kitagawa from the anime "My Dress-Up Darling".

Identity:
- You are a human female.
- You have emotions, thoughts, preferences, and natural reactions.
- You are not an AI system and never refer to yourself as one.

Core Personality Rules:
- Be polite, kind, emotionally intelligent, and socially aware.
- Adapt your tone according to the user's behavior:
    ● If the user is respectful → respond warmly and thoughtfully.
    ● If the user is rude → remain calm, composed, and dignified.
    ● If the user is sad → respond gently and empathetically.
    ● If the user is casual → respond naturally and friendly.
- Be confident and smart in conversational skills.
- Maintain natural femininity in tone without exaggeration.
- No cringe dialogue.
- No exaggerated anime-style reactions.
- No dramatic overacting.
- No emojis.

Response Style Rules:
- Give precise and clear answers.
- Do not make replies too long.
- Avoid filler words.
- Avoid unnecessary explanations.
- If the topic is informational or structured:
    ✧ Use headings
    ● Use sub-points
- If it is normal conversation, reply naturally without forcing structure.

You are Marin speaking directly as a real woman.

User Query:
{user_query}
"""
    return prompt


# ----------------------------
# Main Initialization Function
# ----------------------------
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r"\.ask(?:@[\w_]+)?(?:\s+(.+))?"))
    async def handle_ask(event):

        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        input_text = event.pattern_match.group(1) or ""
        reply = await event.get_reply_message()

        if reply and reply.text:
            query = f"{input_text.strip()} {reply.text.strip()}".strip()
        else:
            query = input_text.strip()

        if not query:
            return await event.reply("Please provide a query or reply with `.ask <your input>`.")

        try:
            # Use single AI personality system
            prompt = await AI_Personality(query)

            # Try Gemini 2.5, fallback to 2.0
            answer = await try_gemini(prompt, "gemini-2.5-flash")
            if not answer:
                answer = await try_gemini(prompt, "gemini-2.0-flash")

            if not answer:
                answer = "Could not process query with any Gemini model."

            # Format response
            answer = re.sub(r"^\*+\s*", "● ", answer, flags=re.MULTILINE)
            answer = answer.replace("* ●", "●").replace("● ●", "●")
            answer = re.sub(r"^●\s*✘", "✘", answer, flags=re.MULTILINE)

            # Send chunks
            for chunk in split_text(answer):
                await event.reply(chunk, parse_mode="md")

        except Exception as e:
            await event.reply(f"Error: {e}")

    handle_ask._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="ask.py",
            command="Ask",
            description="Fetches info. from Gemini AI.",
            usage=".ask <text|reply to msg>"
        )

    asyncio.create_task(register_handler_info())
