import asyncio
import aiohttp
import io
import time
from telethon import events
from shared.state import state, register_handler_doc, maybe_warn_spammer, is_authorized, is_owner_or_super
from config import RAPIDAPI_KEYS, YOUTUBE_API_KEY

SET_HANDLER = True

# ---------------------------------------------
# GLOBAL SUDO COOLDOWN
# ---------------------------------------------
SUDO_GLOBAL_COOLDOWN = 30  # seconds
LAST_SUDO_USED = 0

# ---------------------------------------------
# RAPIDAPI MP3 FETCH
# ---------------------------------------------
async def get_mp3_link(video_id):
    url = "https://youtube-mp36.p.rapidapi.com/dl"

    for key in RAPIDAPI_KEYS:
        headers = {
            "X-RapidAPI-Key": key,
            "X-RapidAPI-Host": "youtube-mp36.p.rapidapi.com"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={"id": video_id}, headers=headers) as r:
                    if r.status != 200:
                        continue
                    data = await r.json()

            if not data.get("link"):
                continue

            return data["link"]

        except:
            continue

    return None

# ---------------------------------------------
# MAIN TELETHON MODULE
# ---------------------------------------------
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r'^\.song (.+)$'))
    async def song_handler(event):
        global LAST_SUDO_USED

        # ---------------- OWNER and SUPERSUDO (NO COOLDOWN)
        if is_owner_or_super(event.sender_id):
            pass

        # ---------------- SUDO USERS (GLOBAL COOLDOWN)
        elif is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            now = time.time()
            diff = now - LAST_SUDO_USED

            if diff < SUDO_GLOBAL_COOLDOWN:
                wait = int(SUDO_GLOBAL_COOLDOWN - diff)
                await event.reply(
                    f"✧ 𝐓𝐫𝐲 .𝐬𝐨𝐧𝐠 𝐚𝐟𝐭𝐞𝐫 {wait // 60}𝐦:{wait % 60}𝐬"
                )
                return

            LAST_SUDO_USED = now

        # ---------------- BLOCK OTHERS
        else:
            return

        query = event.pattern_match.group(1).strip()

        try:
            # YOUTUBE SEARCH
            yt_url = (
                "https://www.googleapis.com/youtube/v3/search"
                f"?part=snippet&type=video&maxResults=1&q={query}&key={YOUTUBE_API_KEY}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(yt_url) as r:
                    yt_data = await r.json()

            if not yt_data.get("items"):
                await event.reply("No results found.")
                return

            item = yt_data["items"][0]
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]

            # MP3 LINK
            mp3_url = await get_mp3_link(video_id)
            if not mp3_url:
                await event.reply("Api error.")
                return

            # DOWNLOAD MP3
            async with aiohttp.ClientSession() as session:
                async with session.get(mp3_url) as r:
                    audio = await r.read()

            file = io.BytesIO(audio)
            file.name = f"{title}.mp3"

            await client.send_file(
                event.chat_id,
                file,
                reply_to=event.id
            )

        except Exception as e:
            await event.reply(f"Error: {e}")

    song_handler._from_userbot_reload = True

    async def register_info():
        await register_handler_doc(
            filename="song.py",
            command="Song",
            description="Fetches Song from Youtube.",
            usage=".song <name>"
        )

    asyncio.create_task(register_info())
