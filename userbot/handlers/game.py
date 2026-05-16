import aiohttp
from telethon import events
from telethon.errors import ChatWriteForbiddenError, ChatSendMediaForbiddenError
from shared.state import state, register_handler_doc, is_authorized, maybe_warn_spammer
import datetime
import asyncio
from config import GIANTBOMB_API_KEY, RAWG_API_KEY


SET_HANDLER = True
# --- Helper: shorten summary intelligently ---
def shorten_text(text: str, max_len: int = 780) -> str:
    """Shortens long text intelligently without losing meaning."""
    if len(text) <= max_len:
        return text.strip()

    # Cut to max length but try not to break a sentence mid-way
    truncated = text[:max_len]
    last_period = truncated.rfind(". ")
    if last_period != -1:
        truncated = truncated[: last_period + 1]

    # Add ellipsis and a concise note
    return truncated.strip() + "..."


def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r"\.game (.+)"))
    async def game(event):
        # Restrict to owner/sudo users
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        query = event.pattern_match.group(1).strip()
        if not query:
            await event.reply("Usage: `.game <game name>`")
            return

        async with aiohttp.ClientSession() as session:
            try:
                # ---------------------------------------------------
                # 🔹 1. Fetch POSTER from GiantBomb API
                # ---------------------------------------------------
                poster = None
                try:
                    gb_url = "https://www.giantbomb.com/api/search/"
                    gb_params = {
                        "api_key": GIANTBOMB_API_KEY,
                        "format": "json",
                        "query": query,
                        "resources": "game",
                        "field_list": "name,image",
                        "limit": 1,
                    }
                    gb_headers = {"User-Agent": "Userbot/1.0"}

                    async with session.get(gb_url, params=gb_params, headers=gb_headers) as resp:
                        gb_data = await resp.json()

                    if gb_data.get("results"):
                        poster = (
                            gb_data["results"][0]
                            .get("image", {})
                            .get("medium_url")
                            or gb_data["results"][0]
                            .get("image", {})
                            .get("small_url")
                        )
                except Exception:
                    poster = None

                # ---------------------------------------------------
                # 🔹 2. Fetch DETAILS from RAWG API
                # ---------------------------------------------------
                rawg_search_url = "https://api.rawg.io/api/games"
                rawg_params = {"search": query, "key": RAWG_API_KEY, "page_size": 1}

                async with session.get(rawg_search_url, params=rawg_params) as resp:
                    rawg_data = await resp.json()

                if not rawg_data.get("results"):
                    await event.reply("`No game found with that name.`")
                    return

                game_info = rawg_data["results"][0]
                game_slug = game_info.get("slug")

                # Fetch full detail
                rawg_detail_url = f"https://api.rawg.io/api/games/{game_slug}"
                async with session.get(rawg_detail_url, params={"key": RAWG_API_KEY}) as resp:
                    details = await resp.json()

                # ---------------------------------------------------
                # 🔹 3. Extract details
                # ---------------------------------------------------
                name = details.get("name", "Unknown")
                released = details.get("released") or "N/A"
                year_of_announcement = (
                    datetime.datetime.strptime(released, "%Y-%m-%d").year
                    if released != "N/A"
                    else "N/A"
                )
                developers = (
                    ", ".join([d["name"] for d in details.get("developers", [])]) or "Unknown"
                )
                platforms = (
                    ", ".join([p["platform"]["name"] for p in details.get("platforms", [])])
                    or "Unknown"
                )
                rating = details.get("rating") or "N/A"
                metacritic = details.get("metacritic") or "N/A"
                downloads = details.get("added", "N/A")
                price = details.get("price", "N/A")
                about = details.get("description_raw", "No description available.")
                about = shorten_text(about)

                # ---------------------------------------------------
                # 🔹 4. Format caption
                # ---------------------------------------------------
                caption = (
                    f"➤ 𝗡𝗮𝗺𝗲: `{name}`\n\n"
                    f"⦁ 𝗬𝗲𝗮𝗿 𝗼𝗳 𝗔𝗻𝗻𝗼𝘂𝗻𝗰𝗲𝗺𝗲𝗻𝘁: `{year_of_announcement}`\n"
                    f"⦁ 𝗥𝗲𝗹𝗲𝗮𝘀𝗲𝗱 𝗼𝗻 `{released}`\n"
                    f"⦁ 𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿𝘀 & 𝗦𝘁𝘂𝗱𝗶𝗼𝘀: `{developers}`\n"
                    f"⦁ 𝗣𝗹𝗮𝘁𝗳𝗼𝗿𝗺𝘀: `{platforms}`\n"
                    f"⦁ 𝗥𝗮𝘁𝗲𝗱: `{rating}/5`\n\n"                    
                    f"➤ 𝗔𝗯𝗼𝘂𝘁 𝗧𝗵𝗲 𝗚𝗮𝗺𝗲— \n**{about}**"
                )

                # ---------------------------------------------------
                # 🔹 5. Send Media + Caption
                # ---------------------------------------------------
                try:
                    if poster:
                        await event.reply(file=poster, message=caption, link_preview=False)
                    else:
                        await event.reply(caption, link_preview=False)
                except (ChatSendMediaForbiddenError, ChatWriteForbiddenError):
                    await event.reply(caption, link_preview=False)
                except Exception as e:
                    await event.reply(f"Failed:\n`{e}`")

            except Exception as e:
                await event.reply(f"Failed:\n`{e}`")

    game._from_userbot_reload = True
    async def register_handler_info():
        await register_handler_doc(
            filename="game.py",
            command="Game",
            description="Fetches details of Games .",
            usage=".game <game name>"
        )

    # Schedule registration task
    asyncio.create_task(register_handler_info())
