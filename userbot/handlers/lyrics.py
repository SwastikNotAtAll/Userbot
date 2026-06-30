# userbot/handlers/lyrics.py
import aiohttp
import asyncio
from telethon import events

from shared.state import (
    register_handler_doc,
    is_authorized,
    maybe_warn_spammer,
)
from .error import safe_handler
from config import LYRICS_API
SET_HANDLER = True


# ----------------------------
# Helper: Fetch lyrics
# ----------------------------
async def fetch_lyrics(query):
    url = LYRICS_API

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            params={"q": query},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:

            if resp.status != 200:
                return None

            data = await resp.json()

            if not data:
                return None

            song = data[0]

            return {
                "title": song.get("trackName", query),
                "artist": song.get("artistName", "Unknown Artist"),
                "album": song.get("albumName", "Unknown Album"),
                "lyrics": song.get("plainLyrics"),
            }


# ----------------------------
# Command: .lyrics <song>
# ----------------------------
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r"^\.(?:ly|lyrics)(?:\s+(.*))?$"))
    @safe_handler("lyrics.py", sync_callback)
    async def lyrics_handler(event):

        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        query = event.pattern_match.group(1)

        if not query:
            await event.reply("𝗣𝗹𝗲𝗮𝘀𝗲 𝗣𝗿𝗼𝘃𝗶𝗱𝗲 𝗔 𝗦𝗼𝗻𝗴 𝗡𝗮𝗺𝗲.")
            return

        query = query.strip()

        try:
            result = await fetch_lyrics(query)

            if not result:
                await event.reply(
                    f"No lyrics found for <b>{query}</b>.",
                    parse_mode="html",
                )
                return

            lyrics = result["lyrics"]

            if not lyrics:
                await event.reply(
                    "𝗟𝘆𝗿𝗶𝗰𝘀 𝗮𝗿𝗲 𝗨𝗻𝗮𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗙𝗼𝗿 𝗧𝗵𝗶𝘀 𝗦𝗼𝗻𝗴.",
                    parse_mode="html",
                )
                return

            if len(lyrics) > 3800:
                lyrics = lyrics[:3800] + "\n\n..."

            text = (
                f"<blockquote><b>Title:</b> {result['title']}</blockquote>\n"
                f"<blockquote><b>Artist:</b> {result['artist']}</blockquote>\n"
            )

            if result["album"] != "Unknown Album":
                text += (
                    f"<blockquote><b>Album:</b> {result['album']}</blockquote>\n"
                )

            text += (
                f"<blockquote expandable>{lyrics}</blockquote>"
            )

            await event.reply(text, parse_mode="html")

        except Exception as e:
            await event.reply(
                f"<b>Error:</b> <code>{e}</code>",
                parse_mode="html",
            )

    lyrics_handler._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="lyrics.py",
            command="Lyrics",
            description="Searches and displays song lyrics.",
            usage=".lyrics/.ly <song name>",
        )

    asyncio.create_task(register_handler_info())
