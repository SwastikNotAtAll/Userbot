import asyncio
import wikipediaapi
from telethon import events
from shared.state import is_authorized, maybe_warn_spammer, register_handler_doc
from .error import safe_handler

SET_HANDLER = True

# Wikipedia API (User-Agent is required)
wiki = wikipediaapi.Wikipedia(
    user_agent="SwastikNotAtAll/1.0 (Project)",
    language="en",
    extract_format=wikipediaapi.ExtractFormat.WIKI
)

# ───────────────────────────────────────────────
#  FETCH WIKIPEDIA
# ───────────────────────────────────────────────
async def fetch_wiki(query: str):
    try:
        page = await asyncio.to_thread(wiki.page, query)

        if not page.exists():
            return None

        summary = page.summary.strip()

        text = (
            f"**{page.title}**\n\n"
            f"{summary}"
        )

        return text

    except Exception:
        return None


# ───────────────────────────────────────────────
#  SPLIT MESSAGE > 4096 CHAR
# ───────────────────────────────────────────────
def split_message(text: str):
    limit = 4096
    parts = []

    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit

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

        query = event.pattern_match.group(1).strip()

        result = await fetch_wiki(query)

        if not result:
            return await event.reply("No Wikipedia article found for this query.")

        parts = split_message(result)

        await event.reply(parts[0])

        for part in parts[1:]:
            await event.respond(part)

    async def register_handler_info():
        await register_handler_doc(
            filename="wikipedia.py",
            command="Wikipedia",
            description="Fetch information from Wikipedia.",
            usage=".wiki <query>"
        )

    asyncio.create_task(register_handler_info())
