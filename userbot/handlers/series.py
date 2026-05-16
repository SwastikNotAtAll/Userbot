import os
import aiohttp
from telethon import events
from shared.state import state, register_handler_doc, is_authorized, maybe_warn_spammer
from .error import safe_handler
import requests
from datetime import datetime
import asyncio
from config import TMDB_API_KEY

SET_HANDLER = True
def format_series_info(series: dict, actors: list):
    title = series.get("name", "N/A")
    first_air_date = series.get("first_air_date", "N/A")
    try:
        year = first_air_date.split("-")[0]
        formatted_date = datetime.strptime(first_air_date, "%Y-%m-%d").strftime("%d %B %Y")
    except Exception:
        year = "N/A"
        formatted_date = first_air_date
    genres = ", ".join([g["name"] for g in series.get("genres", [])]) or "N/A"
    studios = ", ".join([s["name"] for s in series.get("production_companies", [])]) or "N/A"
    rating = series.get("vote_average", "N/A")
    overview = series.get("overview", "Not available")
    actors_list = ", ".join(actors[:3]) if actors else "N/A"
    seasons = series.get("number_of_seasons", "N/A")
    episodes = series.get("number_of_episodes", "N/A")
    status = series.get("status", "N/A")

    return (
        f"➤ 𝗡𝗮𝗺𝗲: `{title}`\n\n"
        f"● 𝗚𝗲𝗻𝗿𝗲: `{genres}`\n"
        f"● 𝗬𝗲𝗮𝗿 𝗼𝗳 𝗔𝗶𝗿𝗶𝗻𝗴: `{year}`\n"
        f"● 𝗙𝗶𝗿𝘀𝘁 𝗔𝗶𝗿𝗲𝗱 𝗼𝗻 `{formatted_date}`\n"
        f"● 𝗦𝘁𝘂𝗱𝗶𝗼𝘀: `{studios}`\n"
        f"● 𝗥𝗮𝘁𝗶𝗻𝗴: `{rating}/10`\n"
        f"● 𝗦𝗲𝗮𝘀𝗼𝗻𝘀: `{seasons}` | 𝗘𝗽𝗶𝘀𝗼𝗱𝗲𝘀: `{episodes}`\n"
        f"● 𝗦𝘁𝗮𝘁𝘂𝘀: `{status}`\n"
        f"● 𝗔𝗰𝘁𝗼𝗿𝘀: `{actors_list}`\n\n"
        f"➤ 𝗦𝘂𝗺𝗺𝗮𝗿𝘆\n{overview}"
    )


def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r"^\.series (.+)"))
    @safe_handler("series.py", sync_callback)
    async def series_handler(event):
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        query = event.pattern_match.group(1).strip()
        if not query:
            await event.reply("`Please provide a series name.`")
            return

        # Search TV Series on TMDb
        search_url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={query}"
        resp = requests.get(search_url).json()
        results = resp.get("results")
        if not results:
            await event.reply("`No results found.`")
            return

        series_data = results[0]
        series_id = series_data["id"]

        # Fetch full series details
        series_details_url = f"https://api.themoviedb.org/3/tv/{series_id}?api_key={TMDB_API_KEY}"
        series = requests.get(series_details_url).json()

        # Fetch top actors from credits
        credits_url = f"https://api.themoviedb.org/3/tv/{series_id}/credits?api_key={TMDB_API_KEY}"
        credits = requests.get(credits_url).json()
        cast = credits.get("cast", [])
        actors = [c["name"] for c in cast[:3]] if cast else []

        poster_path = series.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

        reply_text = format_series_info(series, actors)

        try:
            if poster_url:
                # Download poster
                async with aiohttp.ClientSession() as session:
                    async with session.get(poster_url) as resp:
                        data = await resp.read()
                os.makedirs("./temp", exist_ok=True)
                temp_file = "./temp/series_poster.jpg"
                with open(temp_file, "wb") as f:
                    f.write(data)

                # Send poster with caption
                await event.reply(file=temp_file, message=reply_text)
                os.remove(temp_file)
            else:
                await event.reply(reply_text)
        except Exception as e:
            await event.reply(f"Error: `{e}`")

    async def register_handler_info():
        await register_handler_doc(
            filename="series.py",
            command="Series",
            description="Fetches detailed info about TV series.",
            usage=".series <series name>"
        )
    asyncio.create_task(register_handler_info())
