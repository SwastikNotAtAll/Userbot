# userbot/handlers/cmds.py
from telethon import events
from shared.state import state, register_handler_doc, is_authorized, maybe_warn_spammer
from .error import safe_handler
from config import BOT_USERNAME
import asyncio


SET_HANDLER = True
# ----------------------------
# Init Function
# ----------------------------
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r"^\.help$"))
    @safe_handler("help.py", sync_callback)
    async def cmds_handler(event):
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        if not BOT_USERNAME:
            await event.reply("BOT_USERNAME not set in config.py.")
            return

        try:
            # Inline query via your bot
            results = await client.inline_query(BOT_USERNAME, "help_menu")

            if not results:
                await event.reply("No inline results found.")
                return

            # Send inline result to same chat
            await results[0].click(
                event.chat_id,
                reply_to=event.id,
                hide_via=True,
            )

        except Exception as e:
            await event.reply(f"Failed: `{e}`")

    cmds_handler._from_userbot_reload = True

    # Register handler documentation
    asyncio.create_task(register_handler_doc(
        filename="help.py",
        command="Help",
        description="Shows all registered userbot commands.",
        usage=".help"
    ))
