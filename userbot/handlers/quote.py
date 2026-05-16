import asyncio
import os
from telethon import events
from telethon.errors.rpcerrorlist import YouBlockedUserError
from shared.state import state, register_handler_doc, is_owner_or_super

SET_HANDLER = True
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r'^\.q$', func=lambda e: e.is_group or e.is_private))
    async def quote_handler(event):
        """Generate a quote sticker using @QuotLyBot (owner + sudo)."""
        if not is_owner_or_super(event.sender_id):
            return

        if not event.reply_to_msg_id:
            await event.reply("Reply to a user's text to quote.")
            return

        reply_msg = await event.get_reply_message()
        if not reply_msg.text:
            await event.reply("Reply to a text message only.")
            return

        status = await event.reply("`Quoting the text...`")

        try:
            chat = "@QuotLyBot"

            async with client.conversation(chat) as conv:
                try:
                    response_future = conv.wait_event(
                        events.NewMessage(incoming=True, from_users=1031952739)
                    )
                    await client.forward_messages(chat, reply_msg)
                    response = await response_future
                except YouBlockedUserError:
                    await status.edit("Unable to quote, re-try later.")
                    return

                if response.text and response.text.startswith("Hi!"):
                    await status.edit("Disable your forward privacy settings and try again.")
                    return

                temp_path = await client.download_media(response.message)
                if temp_path:
                    await client.send_file(event.chat_id, temp_path)
                    os.remove(temp_path)

                await status.delete()

        except Exception as e:
            await status.edit(f"Error: {type(e).__name__}: {e}")


    @client.on(events.NewMessage(pattern=r'^\.q r$', func=lambda e: e.is_group or e.is_private))
    async def quote_reply_chain_handler(event):
        """Generate a quote including replied message chain (owner + sudo)."""
        if not is_owner_or_super(event.sender_id):
            return

        if not event.reply_to_msg_id:
            await event.reply("Reply to a message.")
            return

        reply_msg = await event.get_reply_message()
        if not reply_msg.text:
            await event.reply("Reply to a text.")
            return

        try:
            parent_msg = None
            if reply_msg.reply_to_msg_id:
                parent_msg = await reply_msg.get_reply_message()

            if not parent_msg:
                await event.reply("That message isn’t a reply — use `.q` instead.")
                return

            status = await event.reply("`Quoting..`")
            chat = "@QuotLyBot"

            async with client.conversation(chat) as conv:
                try:
                    response_future = conv.wait_event(
                        events.NewMessage(incoming=True, from_users=1031952739)
                    )
                    await client.forward_messages(chat, [parent_msg, reply_msg])
                    response = await response_future
                except YouBlockedUserError:
                    await status.edit("Unable to quote, re-try later.")
                    return

                if response.text and response.text.startswith("Hi!"):
                    await status.edit("Disable your forward privacy settings and try again.")
                    return

                temp_path = await client.download_media(response.message)
                if temp_path:
                    await client.send_file(event.chat_id, temp_path)
                    os.remove(temp_path)

                await status.delete()

        except Exception as e:
            await status.edit(f"Error: {type(e).__name__}: {e}")


    # --- Mark for reload system ---
    quote_handler._from_userbot_reload = True
    quote_reply_chain_handler._from_userbot_reload = True

    # --- Register handler documentation ---
    async def register_handler_info():
        await register_handler_doc(
            filename="quote.py",
            command="Quote",
            description="Generates quote sticker of target msg.",
            usage=".q (reply to a message)\n.q r (reply to a reply to include both)",
        )

    asyncio.create_task(register_handler_info())
