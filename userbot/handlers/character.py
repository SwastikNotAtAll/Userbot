import asyncio
import re
import requests
import calendar
from telethon import events
from shared.state import state, register_handler_doc, is_authorized


SET_HANDLER = True

ANILIST_URL = "https://graphql.anilist.co"

CHARACTER_QUERY = """
query ($search: String) {
  Character(search: $search) {
    id
    name {
      full
      native
    }
    image {
      large
    }
    description(asHtml: false)
    gender
    age
    bloodType
    favourites
    dateOfBirth {
      day
      month
      year
    }
    media(perPage: 3) {
      nodes {
        title {
          romaji
        }
      }
      edges {
        voiceActors(language: JAPANESE) {
          name {
            full
          }
        }
      }
    }
  }
}
"""


def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r'^\.char(?:\s+(.*))?$'))
    async def char_handler(event):

        if not is_authorized(event.sender_id):
            return

        query = event.pattern_match.group(1)
        query = query.strip() if query else ""

        if not query:
            await event.reply("𝗨𝘀𝗮𝗴𝗲: `.char <name>`")
            return

        try:
            response = requests.post(
                ANILIST_URL,
                json={"query": CHARACTER_QUERY, "variables": {"search": query}},
                timeout=10
            ).json()
        except Exception:
            await event.reply("❌ 𝗔𝗣𝗜 𝗘𝗿𝗿𝗼𝗿.")
            return

        char = response.get("data", {}).get("Character")
        if not char:
            await event.reply("❌ 𝗖𝗵𝗮𝗿𝗮𝗰𝘁𝗲𝗿 𝗡𝗼𝘁 𝗙𝗼𝘂𝗻𝗱.")
            return

        # Basic Info
        name = char["name"].get("full", "Unknown")
        native = char["name"].get("native") or name
        cid = char.get("id")
        image = char.get("image", {}).get("large")
        gender = char.get("gender") or "Unknown"
        age = char.get("age") or "Unknown"
        blood = char.get("bloodType") or "Unknown"
        favs = f"{char.get('favourites', 0):,}"

        # Birthday formatting
        dob = char.get("dateOfBirth", {})
        dob_text = "Unknown"
        if dob.get("day") and dob.get("month"):
            month_name = calendar.month_name[dob["month"]]
            dob_text = f"{dob['day']} {month_name}"
            if dob.get("year"):
                dob_text += f" {dob['year']}"

        # Voice Actor (only if exists)
        va_name = None
        media = char.get("media", {})
        edges = media.get("edges", [])

        for edge in edges:
            if not edge:
                continue
            vactors = edge.get("voiceActors")
            if vactors and len(vactors) > 0:
                va_name = vactors[0].get("name", {}).get("full")
                if va_name:
                    break

        # Main Anime Appearance
        media = char.get("media", {})
        nodes = media.get("nodes", [])

        main_anime = "Unknown"
        if nodes and nodes[0].get("title"):
            main_anime = nodes[0]["title"].get("romaji") or nodes[0]["title"].get("english") or "Unknown"

        anime_text = f"✧ ᴀɴɪᴍᴇ - {main_anime}"

        # Description clean
        desc = char.get("description") or "No description available."
        desc = re.sub(r"<.*?>", "", desc)
        sentences = desc.split(". ")
        desc = ". ".join(sentences[:4]).strip()
        if not desc.endswith("."):
            desc += "."

        # Voice Actor Line
        va_text = ""
        if va_name:
            va_text = f"✧ ᴠᴏɪᴄᴇ ᴀᴄᴛᴏʀ: {va_name} 🎙\n\n"

        # Final Caption UI
        caption = (
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "ㅤㅤㅤ🎴 ᴀɴɪʟɪsᴛ ᴄʜᴀʀᴀᴄᴛᴇʀ \n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✧ ᴊᴀᴘᴀɴᴇssᴇ ɴᴀᴍᴇ: {native}\n"
            f"✧ ɴᴀᴍᴇ: {name}\n"
            f"✧ ɪᴅ: `{cid}`\n"
            f"✧ ɢᴇɴᴅᴇʀ: {gender}\n"
            f"✧ ᴀɢᴇ: {age}\n"
            f"✧ ʙʟᴏᴏᴅ ᴛʏᴘᴇ: {blood}\n"
            f"✧ ʙɪʀᴛʜᴅᴀʏ: {dob_text}\n"
            f"⭐ғᴀɴs: {favs}\n"
            f"{va_text}"
            f"{anime_text}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "● ᴅᴇsᴄʀɪᴘᴛɪᴏɴ:\n"
            f"{desc}"
        )

        await client.send_file(
            event.chat_id,
            image,
            caption=caption,
            reply_to=event.id,
            parse_mode="markdown",
            link_preview=False
        )

    char_handler._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="char.py",
            command="Character",
            description="Fetch anime character details from AniList.",
            usage=".char <name>"
        )

    asyncio.create_task(register_handler_info())
