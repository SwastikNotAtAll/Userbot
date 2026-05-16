# userbot/handlers/speedtest.py
import speedtest
from telethon import events
import asyncio
from shared.state import state, register_handler_doc, is_authorized, maybe_warn_spammer
from .error import safe_handler

SET_HANDLER = True

def convert_from_bytes(size):
    power = 2 ** 10
    n = 0
    units = {0: "", 1: "KB/s", 2: "MB/s", 3: "GB/s", 4: "TB/s"}
    while size > power:
        size /= power
        n += 1
    return f"{round(size, 2)} {units[n]}"

def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r"^\.sptest$"))
    @safe_handler("speedtest.py", sync_callback)
    async def speedtest_handler(event):
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        original_message = await event.reply("`Checking server speed...`")

        try:
            # Run speedtest
            s = speedtest.Speedtest()
            s.get_best_server()
            download_speed = s.download()
            upload_speed = s.upload()
            ping_time = s.results.ping
            client_info = s.results.client
            isp = client_info.get("isp")
            isp_rating = client_info.get("isprating")

            result_text = (
                f"**Speedtest Completed**\n\n"
                f"**Download:** `{convert_from_bytes(download_speed)}`\n"
                f"**Upload:** `{convert_from_bytes(upload_speed)}`\n"
                f"**Ping:** `{ping_time} ms`\n"
                f"**ISP:** {isp}\n"
                f"**ISP Rating:** {isp_rating}"
            )

            try:
                # Get official Ookla image URL
                speedtest_image_url = s.results.share()
                # Send image with caption
                await event.client.send_file(
                    event.chat_id,
                    speedtest_image_url,
                    caption=result_text,
                    force_document=False,  # True if you want it as file
                    reply_to=event.message.id,
                    allow_cache=False
                )
                await original_message.delete()
            except Exception:
                # Fallback to text if media restricted
                await original_message.edit(result_text)

        except Exception as e:
            await original_message.edit(f"Error: `{e}`")

    speedtest_handler._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="speedtest.py",
            command="Speedtest",
            description="Checks server speed using Ookla with optional image output.",
            usage=".sptest"
        )

    asyncio.create_task(register_handler_info())
