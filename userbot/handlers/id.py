from telethon import events
from shared.state import state, register_handler_doc, is_authorized, maybe_warn_spammer
from .error import safe_handler
import asyncio


SET_HANDLER = True
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r"^\.id(?:\s|$)(.*)"))
    @safe_handler("id.py", sync_callback)
    async def id_handler(event):
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        # Case 1: Reply to a user
        if event.is_reply:
            reply = await event.get_reply_message()
            user = await reply.get_sender()
            first_name = getattr(user, "first_name", None)
            if first_name:
                await event.reply(f"**{first_name}'s ID is:** `{user.id}`")
            else:
                await event.reply(f"**User's ID is:** `{user.id}`")
            return

        # Case 2: Mentioned @username or ID
        arg = event.pattern_match.group(1).strip()
        if arg:
            try:
                user = await client.get_entity(arg)
                first_name = getattr(user, "first_name", None)
                if first_name:
                    await event.reply(f"**{first_name}'s ID is:** `{user.id}`")
                else:
                    await event.reply(f"**User's ID is:** `{user.id}`")
            except Exception as e:
                await event.reply(f"**Could not fetch user info**: `{e}`")
            return

        # Case 3: No argument — give info of current chat OR current user
        chat = await event.get_chat()

        if event.is_group or event.is_channel:
            # For groups/supergroups/channels
            chat_name = chat.title or "Group"
            gid = f"-100{chat.id}"
            await event.reply(f"**{chat_name} Chat ID:** `{gid}`")
        else:
            # Private chat
            user = await event.get_sender()
            first_name = getattr(user, "first_name", None)
            if first_name:
                await event.reply(f"**{first_name}'s ID is:** `{user.id}`")
            else:
                await event.reply(f"**User's ID is:** `{user.id}`")

    id_handler._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="id.py",
            command="ID",
            description="Fetches User's or Chat's id.",
            usage=".id <username|reply to user|normally>"
        )

    asyncio.create_task(register_handler_info())
