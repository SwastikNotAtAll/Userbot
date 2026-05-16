# userbot/handlers/ud.py
import aiohttp
import re
import asyncio
from telethon import events
from shared.state import state, register_handler_doc, is_authorized, maybe_warn_spammer
from .error import safe_handler

SET_HANDLER = True
# ----------------------------
# Helper: Fetch and clean from Urban Dictionary API
# ----------------------------
async def fetch_ud_definition(term):
    """Fetch Urban Dictionary definition and preserve formatting."""
    url = "https://api.urbandictionary.com/v0/define"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params={"term": term}) as resp:
            if resp.status != 200:
                return None

            data = await resp.json()

            try:
                entry = data["list"][0]

                def clean(text):
                    if not text:
                        return ""

                    # Remove Urban Dictionary square bracket markup
                    text = re.sub(r"\[|\]", "", text)

                    # Normalize line endings
                    text = text.replace("\r\n", "\n")

                    # Remove excessive blank lines (keep max 2)
                    text = re.sub(r"\n{3,}", "\n\n", text)

                    return text.strip()

                return {
                    "word": clean(entry.get("word")),
                    "definition": clean(entry.get("definition")),
                    "example": clean(entry.get("example", "No example provided.")),
                }

            except (IndexError, KeyError):
                return None


# ----------------------------
# Command: .ud <word>
# ----------------------------
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r"^\.ud(?:\s+(.*))?$"))
    @safe_handler("ud.py", sync_callback)
    async def ud_handler(event):

        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        word = event.pattern_match.group(1)

        if not word:
            await event.reply("Please provide a word to search.")
            return

        word = word.strip()

        msg = await event.reply("Searching...")

        try:
            result = await fetch_ud_definition(word)

            if not result:
                await msg.edit(f"No definition found for <b>{word}</b>.", parse_mode="html")
                return

            formatted_text = (
                f"<b>✘ Word:</b> {result['word']}\n\n"
                f"<b>✘ Definition:</b>\n{result['definition']}\n\n"
                f"<b>✘ Example:</b>\n{result['example']}"
            )

            await msg.edit(formatted_text, parse_mode="html")

        except Exception as e:
            await msg.edit(f"<b>Error:</b> <code>{e}</code>", parse_mode="html")


    ud_handler._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="ud.py",
            command="Ud",
            description="Fetches a word definition from Urban Dictionary.",
            usage=".ud <word>"
        )

    asyncio.create_task(register_handler_info())
