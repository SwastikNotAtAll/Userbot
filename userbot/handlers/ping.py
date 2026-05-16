from telethon import events
from shared.state import state, register_handler_doc, maybe_warn_spammer, is_authorized
import time
import asyncio


SET_HANDLER = True
# Uptime starts fresh every time the bot launches
uptime_start = time.time()

def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r'\.ping'))
    async def ping(event):
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        # Measure latency
        start = time.time()
        msg = await event.reply("..")
        latency = time.time() - start

        # Calculate uptime since bot start
        uptime_sec = int(time.time() - uptime_start)
        days, remainder = divmod(uptime_sec, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime_parts = []
        if days: uptime_parts.append(f"{days}d")
        if hours: uptime_parts.append(f"{hours}h")
        if minutes: uptime_parts.append(f"{minutes}m")
        if seconds: uptime_parts.append(f"{seconds}s")
        uptime_str = ":".join(uptime_parts)

        # Owner info (clickable)
        owner_id = state["owner_id"]
        owner = await client.get_entity(owner_id)
        clickable = f"[{owner.first_name}](tg://user?id={owner.id})"

        # Final response
        await msg.edit(
            f"**Pong!** `{latency:.2f}s`\n"
            f"**Uptime** - `{uptime_str}`\n"
            f"**Bot of** {clickable}",
            parse_mode="md"
        )

    # prevent duplicate registration
    ping._from_userbot_reload = True
    async def register_handler_info():
        await register_handler_doc(
            filename="ping.py",
            command="Ping",
            description="Checks latency of Userbot.",
            usage=".ping"
        )

    # Schedule registration task
    asyncio.create_task(register_handler_info())
