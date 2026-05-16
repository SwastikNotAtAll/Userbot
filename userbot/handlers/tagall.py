import asyncio
import re
from telethon import events
from shared.state import state, register_handler_doc, is_authorized, is_owner_or_super

SET_HANDLER = True
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r'^\.tagall(?:\s+([\s\S]+))?$'))
    async def tagall_handler(event):
        if not is_owner_or_super(event.sender_id):
            return
        # Extract optional custom text (supports multiline)
        cmd_text = event.pattern_match.group(1)
        cmd_text = cmd_text.strip() if cmd_text else ""
        # Check if command used as reply
        reply_msg = await event.get_reply_message()
        # Decide reply target
        target_reply_id = reply_msg.id if reply_msg else event.id
        chat_id = event.chat_id
        # Fetch valid participants (skip bots + deleted)
        users = []
        try:
            async for user in client.iter_participants(chat_id):
                if not user.bot and not user.deleted:
                    users.append(user)
        except Exception as e:
            await event.reply(f"Error fetching users: {e}")
            return

        if not users:
            await event.reply("No valid users found to tag.")
            return

        # Send in chunks of 5
        batch = []
        for user in users:
            mention = f"<a href=\"tg://user?id={user.id}\">{user.first_name}</a>"
            batch.append(mention)

            if len(batch) == 5:
                tag_text = ", ".join(batch)
                if cmd_text:
                    tag_text += f"\n\n{cmd_text}"

                await client.send_message(
                    chat_id,
                    tag_text,
                    reply_to=target_reply_id,
                    parse_mode="html"
                )

                batch.clear()
                await asyncio.sleep(1.5)

        # Leftover batch
        if batch:
            tag_text = ", ".join(batch)
            if cmd_text:
                tag_text += f"\n\n{cmd_text}"

            await client.send_message(
                chat_id,
                tag_text,
                reply_to=target_reply_id,
                parse_mode="html"
            )
    tagall_handler._from_userbot_reload = True
    # ----------------------------
    # Async registration for cmds.py
    # ----------------------------
    async def register_handler_info():
        await register_handler_doc(
            filename="tagall.py",
            command="Tagall",
            description="Tags all users in a chat.",
            usage=".tagall <text> OR reply + .tagall"
        )
    asyncio.create_task(register_handler_info())
