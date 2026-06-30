import os
import aiohttp
import asyncio
from datetime import datetime
from telethon import events

from shared.state import (
    state,
    register_handler_doc,
    is_authorized,
    maybe_warn_spammer
)
from .error import safe_handler
from config import YOUTUBE_API_KEY, API_BASE

SET_HANDLER = True

DOWNLOAD_DIR = "downloads/videos"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ----------------------------
# Helper: format views
# ----------------------------
def format_views(count: str):
    count = int(count)

    thresholds = [
        (1_000_000_000_000, "Trillion"),
        (1_000_000_000, "Billion"),
        (1_000_000, "M"),
        (1_000, "K"),
    ]

    for value, suffix in thresholds:
        if count >= value:
            return f"{count / value:.1f}{suffix}"

    return str(count)


# ----------------------------
# Helper: YouTube search + stats
# ----------------------------
async def get_first_video(query: str):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    video_url = "https://www.googleapis.com/youtube/v3/videos"

    async with aiohttp.ClientSession() as session:

        async with session.get(
            search_url,
            params={
                "part": "snippet",
                "q": query,
                "key": YOUTUBE_API_KEY,
                "maxResults": 1,
                "type": "video",
            },
        ) as resp:

            if resp.status != 200:
                return None

            data = await resp.json()
            items = data.get("items")

            if not items:
                return None

            item = items[0]
            video_id = str(item["id"]["videoId"])
            snippet = item["snippet"]

            published = snippet.get("publishedAt", "")

            if published:
                dt = datetime.strptime(
                    published,
                    "%Y-%m-%dT%H:%M:%SZ"
                )
                published_date = dt.strftime("%B %d, %Y").replace(" 0", " ")
            else:
                published_date = "Unknown"

        async with session.get(
            video_url,
            params={
                "part": "statistics",
                "id": video_id,
                "key": YOUTUBE_API_KEY,
            },
        ) as resp:

            stats = await resp.json()
            views = stats["items"][0]["statistics"].get(
                "viewCount",
                "0"
            )

    return {
        "video_id": video_id,
        "title": snippet["title"],
        "channel": snippet["channelTitle"],
        "views": views,
        "published": published_date,
        "url": f"https://youtu.be/{video_id}",
    }


# ----------------------------
# Helper: FuryAPI video downloader
# ----------------------------
async def download_video(video_id: str):
    video_id = str(video_id)

    file_path = f"{DOWNLOAD_DIR}/{video_id}.mp4"

    if os.path.exists(file_path):
        return file_path

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE}/download",
            params={
                "url": video_id,
                "type": "video",
            },
        ) as r:

            if r.status != 200:
                raise Exception(f"Download failed ({r.status})")

            with open(file_path, "wb") as f:
                async for chunk in r.content.iter_chunked(1024 * 256):
                    f.write(chunk)

    return file_path


# ----------------------------
# Command: .yt <query>
# ----------------------------
def init(client, sync_callback=None):

    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r"^\.yt(?:\s+|$)(.*)"))
    @safe_handler("yt.py", sync_callback)
    async def yt_handler(event):

        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        query = event.pattern_match.group(1).strip()

        if not query:
            await event.reply("Usage: .yt <video name>")
            return

        try:
            result = await get_first_video(query)

            if not result:
                await event.reply("No results found.")
                return

            video = await download_video(result["video_id"])
            views = format_views(result["views"])

            sender = await event.get_sender()
            requester = sender.first_name

            caption = (
                "━─━─━━─━「₪」━━─━─━─━\n\n"
                "࿇ Video Search Completed! Here's your video ;\n\n"
                "❖ Details :\n"
                f"<blockquote>{result['title']}</blockquote>\n"
                "❖ Channel :\n"
                f"<blockquote>{result['channel']}</blockquote>\n"
                "❖ Views :\n"
                f"<blockquote>{views}</blockquote>\n"
                "❖ Released On :\n"
                f"<blockquote>{result['published']}</blockquote>\n"
                "❖ YouTube Link :\n"
                f"<blockquote><a href=\"{result['url']}\">{result['title']}</a></blockquote>\n"
                "• Video Requested By :\n"
                f"<blockquote><a href=\"tg://user?id={event.sender_id}\">{requester}</a></blockquote>\n"
                "━─━─━━─━「₪」━━─━─━─━"
            )

            await event.reply(
                message=caption,
                file=video,
                parse_mode="html",
                link_preview=False
            )

        except Exception as e:
            await event.reply(f"Error: {e}")

    yt_handler._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="yt.py",
            command="Youtube",
            description="Fetches and sends a YouTube video.",
            usage=".yt <video name>"
        )

    asyncio.create_task(register_handler_info())
