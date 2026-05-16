import asyncio
from telethon import events
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator
from shared.state import state, register_handler_doc

SET_HANDLER = True
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r'^\.purge$'))
    async def purge_handler(event):
        # --- Owner-only check ---
        if event.sender_id != state["owner_id"]:
            return

        try:
            chat = await event.get_chat()
            user = await event.get_sender()

            # Check admin rights for current user in this chat
            is_admin = False
            if getattr(chat, "admin_rights", None) or getattr(chat, "creator", None):
                try:
                    participant = await client(GetParticipantRequest(chat.id, user.id))
                    is_admin = isinstance(participant.participant,
                                         (ChannelParticipantAdmin, ChannelParticipantCreator))
                except Exception:
                    pass

            # Ensure `.purge` is used as a reply
            if not event.is_reply:
                error_msg = await event.respond(
                    "Reply to a message with `.purge` to delete msgs."
                )
                await asyncio.sleep(2)
                await error_msg.delete()
                return

            reply_msg_id = event.reply_to_msg_id
            messages_to_delete = []

            # Iterate messages starting from the replied message
            async for msg in client.iter_messages(event.chat_id, min_id=reply_msg_id):
                if is_admin:
                    messages_to_delete.append(msg.id)
                else:
                    # Non-admin logic: delete only owner messages
                    if msg.sender_id == state["owner_id"]:
                        messages_to_delete.append(msg.id)
                        
            if messages_to_delete:
                await client.delete_messages(event.chat_id, messages_to_delete, revoke=True)

            if is_admin:
                confirmation = await event.respond(f"ᴘᴜʀɢᴇᴅ `{len(messages_to_delete)}` ᴍsɢs ғʀᴏᴍ ᴛʜᴇ ɢʀᴏᴜᴘ.")
            else:
                confirmation = await event.respond(
                    f"ᴘᴜʀɢᴇᴅ ʏᴏᴜʀ `{len(messages_to_delete)}` ᴍsɢs ғʀᴏᴍ ʜᴇʀᴇ."
                )

            await asyncio.sleep(8)
            await confirmation.delete()

        except Exception as e:
            error_msg = await event.respond(f"`Error: {str(e)}`")
            await asyncio.sleep(4)
            await error_msg.delete()

    # Required for dynamic reload system
    purge_handler._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="purge.py",
            command="purge",
            description="Deletes messages from the replied message onwards.",
            usage=".purge (reply to target message)"
        )

    asyncio.create_task(register_handler_info())
