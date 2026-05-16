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

def format_duration(minutes: int):
    if not minutes:
        return "N/A"
    hrs, mins = divmod(minutes, 60)
    return f"{hrs} hours {mins} minutes"

def format_movie_info(movie: dict, actors: list):
    title = movie.get("title", "N/A")
    release_date = movie.get("release_date", "N/A")
    try:
        year = release_date.split("-")[0]
        formatted_date = datetime.strptime(release_date, "%Y-%m-%d").strftime("%d %B %Y")
    except Exception:
        year = "N/A"
        formatted_date = release_date
    runtime = format_duration(movie.get("runtime"))
    genres = ", ".join([g["name"] for g in movie.get("genres", [])]) or "N/A"
    studios = ", ".join([s["name"] for s in movie.get("production_companies", [])]) or "N/A"
    rating = movie.get("vote_average", "N/A")
    overview = movie.get("overview", "Not available")
    actors_list = ", ".join(actors[:3]) if actors else "N/A"
    
    return (
        f"➤ 𝗡𝗮𝗺𝗲: `{title}`\n\n"
        f"● 𝗗𝘂𝗿𝗮𝘁𝗶𝗼𝗻: `{runtime}`\n"
        f"● 𝗚𝗲𝗻𝗿𝗲: `{genres}`\n"
        f"● 𝗬𝗲𝗮𝗿 𝗼𝗳 𝗔𝗻𝗻𝗼𝘂𝗻𝗰𝗲𝗺𝗲𝗻𝘁: `{year}`\n"
        f"● 𝗥𝗲𝗹𝗲𝗮𝘀𝗲𝗱 𝗼𝗻 `{formatted_date}`\n"
        f"● 𝗦𝘁𝘂𝗱𝗶𝗼𝘀: `{studios}`\n"
        f"● 𝗥𝗮𝘁𝗶𝗻𝗴𝘀: `{rating}/10`\n"
        f"● 𝗔𝗰𝘁𝗼𝗿𝘀: `{actors_list}`\n\n"
        f"➤ 𝗦𝘂𝗺𝗺𝗮𝗿𝘆 \n{overview}"
    )

def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r"^\.movie (.+)"))
    @safe_handler("movie.py", sync_callback)
    async def movie_handler(event):
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        query = event.pattern_match.group(1).strip()

        # Check if year is included
        parts = query.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 4:
            search_query, search_year = parts[0], parts[1]
        else:
            search_query, search_year = query, None


        # Search movie on TMDb
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={search_query}"
        resp = requests.get(search_url).json()
        results = resp.get("results")
        if not results:
            await event.reply("`No results found.`")
            return

        # Filter by year if specified
        movie_data = None
        if search_year:
            for r in results:
                if r.get("release_date", "").startswith(search_year):
                    movie_data = r
                    break
        if not movie_data:
            movie_data = results[0]  # fallback to first result

        movie_id = movie_data["id"]
        movie_details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
        movie = requests.get(movie_details_url).json()

        # Fetch top actors from credits
        credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}"
        credits = requests.get(credits_url).json()
        cast = credits.get("cast", [])
        actors = [c["name"] for c in cast[:3]] if cast else []

        poster_path = movie.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

        reply_text = format_movie_info(movie, actors)

        try:
            if poster_url:
                # Download poster
                async with aiohttp.ClientSession() as session:
                    async with session.get(poster_url) as resp:
                        data = await resp.read()
                os.makedirs("./temp", exist_ok=True)
                temp_file = "./temp/poster.jpg"
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
            filename="movie.py",
            command="Movie",
            description="Fetches detailed info about movies.",
            usage=".movie <movie name>"
        )
    asyncio.create_task(register_handler_info())
