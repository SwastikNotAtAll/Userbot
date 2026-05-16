import aiohttp
from telethon import events
from telethon.errors import ChatWriteForbiddenError, ChatSendMediaForbiddenError
from shared.state import state, register_handler_doc, is_owner_or_super
import asyncio
import re
from config import TAVILY_KEY

SET_HANDLER = True
MAX_CHARS = 4096
# ──────────────────────────────
# Chunk System
# ──────────────────────────────
def chunk_text(text, limit=MAX_CHARS):
    chunks = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks
# ──────────────────────────────
# Tavily Search
# ──────────────────────────────
async def search_web(query):
    if not TAVILY_KEY:
        return []

    payload = {
        "api_key": TAVILY_KEY,
        "query": query,
        "max_results": 5,
        "include_raw_content": True
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.tavily.com/search",
            json=payload
        ) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            return data.get("results", [])

# ──────────────────────────────
# Build Context
# ──────────────────────────────
def build_context(results):
    text = ""
    for item in results:
        title = item.get("title", "")
        content = item.get("raw_content") or item.get("content", "")
        text += f"{title}\n{content[:500]}\n\n"
    return text[:3500]

# ──────────────────────────────
# Binjie Answer
# ──────────────────────────────
async def generate_answer(user_prompt, context):

    full_prompt = (
        f"Context:\n{context}\n\n"
        f"Question: {user_prompt}\n"
        f"Answer clearly and concisely:"
    )
    payload = {
        "prompt": full_prompt,
        "network": True,
        "stream": False,
        "system": {
            "userId": "#/chat/1722576084617",
            "withoutContext": False
        }
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.binjie.fun/api/generateStream",
            headers=headers,
            json=payload,
            timeout=60
        ) as resp:
            return await resp.text()

# ──────────────────────────────
# Main Handler
# ──────────────────────────────
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r"(?i)^\.ai(?:\s+(.*))?$"))
    async def ai(event):
        if not is_owner_or_super(event.sender_id):
            return

        user_prompt = event.pattern_match.group(1)

        if not user_prompt:
            await event.reply("**Usage: .ai <query>**")
            return

        user_prompt = user_prompt.strip()

        status = await event.reply("ᴡᴀɪᴛ ᴀ ᴍɪɴ..")

        try:
            # 1️⃣ Search
            results = await search_web(user_prompt)
            context = build_context(results)

            # 2️⃣ Generate
            answer = await generate_answer(user_prompt, context)

            # Clean unwanted symbols
            answer_clean = re.sub(r"[\[\]\*\_`]", "", answer).strip()

            await status.delete()

            # 3️⃣ Send in chunks
            chunks = chunk_text(answer_clean, MAX_CHARS)
            for chunk in chunks:
                try:
                    await event.reply(chunk)
                except (ChatSendMediaForbiddenError, ChatWriteForbiddenError):
                    await event.reply(chunk)
                except Exception as e:
                    await event.reply(f"Failed:\n{e}")

        except Exception as e:
            await status.edit(f"Failed:\n{e}")

    ai._from_userbot_reload = True
    
    async def register_handler_info():
        await register_handler_doc(
            filename="ai.py",
            command="AI",
            description="AI with web search.",
            usage=".ai <query>"
        )
    asyncio.create_task(register_handler_info())
