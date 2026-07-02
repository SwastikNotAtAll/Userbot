from telethon import events
from shared.state import state, register_handler_doc, maybe_warn_spammer, is_authorized
import time
import asyncio
import random
import os
import telethon


SET_HANDLER = True
# Uptime starts fresh every time the bot launches
uptime_start = time.time()
# Path to your resource images
IMAGE_POOL = [
    "resources/waguri.jpeg",
    "resources/waguri1.jpeg", 
    "resources/waguri2.jpg", 
    "resources/waguri3.mp4"
]

def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r'\.alive'))
    async def alive(event):
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        try:
            # Pick a random image
            img_path = random.choice(IMAGE_POOL)
            if not os.path.exists(img_path):
                await event.reply("Image not found in resources!")
                return

            # Measure ping/latency internally
            latency_start = time.time()

            # Calculate uptime
            uptime_sec = int(time.time() - uptime_start)
            days, remainder = divmod(uptime_sec, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)

            uptime_parts = []
            if days:
                uptime_parts.append(f"{days}d")
            if hours:
                uptime_parts.append(f"{hours}h")
            if minutes:
                uptime_parts.append(f"{minutes}m")
            uptime_parts.append(f"{seconds}s")  # Always show seconds
            uptime_str = " ".join(uptime_parts)

            # Owner info (clickable)
            owner_id = state.get("owner_id")
            owner = await client.get_entity(owner_id)
            clickable = f"[{owner.first_name}](tg://user?id={owner.id})"

            # Telethon version
            tele_ver = telethon.__version__

            # Final caption
            caption = (
                "𝐇𝐞𝐲𝐚! 𝐈 𝐚𝐦 𝐀𝐥𝐢𝐯𝐞!\n\n"
                "┏━━━━━━━━━━━━━━━━┓\n"
                f"┃ • ᴛᴇʟᴇᴛʜᴏɴ : ᴠ{tele_ver}\n"
                f"┃ • ᴀʟɪᴠᴇ ꜱɪɴᴄᴇ: {uptime_str}\n"
                f"┃ • ꜱᴇɴꜱᴇɪ: {clickable}\n"
                f"┃ • ꜱᴛᴀᴛᴜꜱ: ʀᴜɴɴɪɴɢ!\n"
                "┗━━━━━━━━━━━━━━━━┛\n"
                "┏━━━━━━━━━━━━━━┓\n"
                f"┃ ⁭⁫ • ᴘɪɴɢ : {(time.time() - latency_start)*1000:.2f}ᴍs\n"
                "┗━━━━━━━━━━━━━━┛"
            )

            # Send the image with caption, with error handling
            try:
                await event.reply(file=img_path, message=caption, parse_mode="md")
            except telethon.errors.ChatSendMediaForbiddenError:
                # If sending images is not allowed
                await event.reply("Sending pics isn't allowed in this chat")

        except Exception as e:
            # Catch all other unexpected errors
            await event.reply(f"An error occurred while executing .alive:\n`{e}`")

    # prevent duplicate registration
    alive._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="alive.py",
            command="Alive",
            description="Shows UserBot's Status with uptime.",
            usage=".alive"
        )

    asyncio.create_task(register_handler_info())
