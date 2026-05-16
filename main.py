import os
import asyncio
import threading
import importlib
from aiohttp import web
from telethon.errors import FloodWaitError
from telethon import TelegramClient
from userbot.handlers import help_inline, calculator_inline
from config import API_ID, API_HASH, BOT_TOKEN
from shared.state import (
    state,
    register_sync_callback,
    sync_state_to_user_dm,
    restore_state_from_user_dm
)

#---------------- Paths ----------------
HANDLERS_DIR = "userbot/handlers"
#---------------- Clients ----------------
user_client = TelegramClient("sessions/Ub_session", API_ID, API_HASH)
bot_client = TelegramClient("bot_session", API_ID, API_HASH)
#---------------- Locks ----------------
reload_lock = asyncio.Lock()
active_handlers = []
#---------------- Early Inline Init ----------------
calculator_inline.init(bot_client)
help_inline.init(bot_client)
#---------------- Reload Telethon Handlers ----------------

async def reload_handlers(client, sync_callback=None, ignore_files=None):
    async with reload_lock:
        global active_handlers
        ignore_files = ignore_files or []

        for h in active_handlers:
            try:
                client.remove_event_handler(h)
            except Exception:
                pass
        active_handlers.clear()

        for file in os.listdir(HANDLERS_DIR):
            if not file.endswith(".py") or file == "__init__.py" or file in ignore_files:
                continue

            module_name = file[:-3]
            try:
                module = importlib.import_module(f"userbot.handlers.{module_name}")
                importlib.reload(module)
                if hasattr(module, "init"):
                    before = len(client.list_event_handlers())
                    module.init(client, sync_callback)
                    after = len(client.list_event_handlers())
                    active_handlers.extend(client.list_event_handlers()[before:after])
                    state["handlers"][file] = "ok"
            except Exception as e:
                print(f"[Reload error in {file}]: {e}")
                state["handlers"][file] = "error"

        if sync_callback:
            await sync_callback()

#---------------- Web Server ----------------
async def handle(request):
    return web.Response(text="Bot is alive and running.")

async def run_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[Render] Web server running on port {port}")

def start_web_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_web_server())
    loop.run_forever()

threading.Thread(target=start_web_server, daemon=True).start()

#---------------- Main ----------------
async def main():
    # 1️⃣ Start Telethon user
    await user_client.start()

    # 4️⃣ Restore state + load Telethon handlers
    register_sync_callback(lambda: sync_state_to_user_dm(user_client))
    await restore_state_from_user_dm(user_client)

    await reload_handlers(
        user_client,
        sync_callback=lambda: sync_state_to_user_dm(user_client),
        ignore_files=["restart.py"],
    )

    # 5️⃣ Start Telethon bot
    while True:
        try:
            await bot_client.start(bot_token=BOT_TOKEN)
            print("🤖 Bot client started")
            break
        except FloodWaitError as e:
            print(f"[BOT] FloodWait: sleeping {e.seconds} seconds")
            await asyncio.sleep(e.seconds + 5)

    print("✅ Telethon + bot started")

    # 6️⃣ Keep alive
    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected(),
    )

#---------------- Run ----------------
if __name__ == "__main__":
    asyncio.run(main())
