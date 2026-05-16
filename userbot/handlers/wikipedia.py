import wikipedia
import asyncio
from telethon import events
from shared.state import is_authorized, maybe_warn_spammer, register_handler_doc
from .error import safe_handler


SET_HANDLER = True
# Configure Wikipedia language
wikipedia.set_lang("en")
# ───────────────────────────────────────────────
#  CLEAN + SAFE FETCHER
# ───────────────────────────────────────────────
async def fetch_wiki(query: str):
    try:
        # Get the page title via search
        results = wikipedia.search(query)
        if not results:
            return None

        title = results[0]

        # Fetch the summary
        summary = wikipedia.summary(title, auto_suggest=False)

        # Full formatted output
        text = f"**{title}**\n\n{summary}"
        return text

    except Exception:
        return None


# ───────────────────────────────────────────────
#  SPLIT MESSAGE > 4096 CHAR (NO FORMATTING LOSS)
# ───────────────────────────────────────────────
def split_message(text: str):
    limit = 4096
    parts = []

    while len(text) > limit:
        # split at last newline before 4096 to preserve stanza/paragraph
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit  # fallback

        parts.append(text[:split_at])
        text = text[split_at:].lstrip()

    parts.append(text)
    return parts


# ───────────────────────────────────────────────
#  TELETHON HANDLER
# ───────────────────────────────────────────────
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r"^\.wiki (.+)"))
    @safe_handler("wikipedia.py", sync_callback)
    async def wiki_cmd(event):
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        query = event.pattern_match.group(1)

        result = await fetch_wiki(query)
        if not result:
            return await event.reply("No Wikipedia article found for this query.")

        # Split large outputs
        parts = split_message(result)

        # First reply
        await event.reply(parts[0])

        # Subsequent replies
        for part in parts[1:]:
            await event.respond(part)

    # Register doc
    async def register_handler_info():
        await register_handler_doc(
            filename="wikipedia.py",
            command="Wikipedia",
            description="Fetches information from wikipedia.",
            usage=".wiki <query>"
      )
    asyncio.create_task(register_handler_info())
