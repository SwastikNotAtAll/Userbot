import asyncio
from telethon import events
from shared.state import state, register_handler_doc
from .error import safe_handler

SET_HANDLER = True
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r"^\.delall(?:\s|$)(.*)"))
    @safe_handler("delall.py", sync_callback)
    async def delall_handler(event):

        # OWNER ONLY
        if event.sender_id != state["owner_id"]:
            return

        arg = event.pattern_match.group(1).strip()
        if not arg:
            await event.reply("**Usage:** `.delall <chat_id>`")
            return

        # Convert chat_id
        try:
            chat_id = int(arg)
        except Exception as e:
            await event.reply(f"{e}")
            return

        # Fetch chat entity (error handled)
        try:
            chat = await client.get_entity(chat_id)
            chat_name = chat.title if hasattr(chat, "title") else "Private Chat"
        except Exception as e:
            await event.reply(f"ƒαιℓє∂ вƈσz уσυ αяєηт α ραят σƒ тнє тαяgєт ƈнαт!")
            return

        # Start progress message
        try:
            progress_msg = await event.reply(f"Deleting msgs from {chat_name}...")
        except Exception as e:
            await event.reply(f"{e}")
            return

        deleted_count = 0
        batch = []

        try:
            async for msg in client.iter_messages(chat_id, from_user=state["owner_id"]):
                batch.append(msg.id)

                if len(batch) == 100:
                    try:
                        await client.delete_messages(chat_id, batch)
                        deleted_count += 100
                        await progress_msg.edit(f"Deleted **{deleted_count}** msgs from **{chat_name}**")
                    except Exception as e:
                        await event.reply(f"Error: {e}")
                        return
                    batch.clear()

            # Delete leftover messages
            if batch:
                try:
                    await client.delete_messages(chat_id, batch)
                    deleted_count += len(batch)
                    await progress_msg.edit(f"Deleted **{deleted_count}** msgs from **{chat_name}**")
                except Exception as e:
                    await event.reply(f"Error: {e}")
                    return

        except Exception as e:
            await event.reply(f"{e}")
            return

        # Final summary update
        try:
            await progress_msg.edit(f"Deleted **{deleted_count}** msgs from **{chat_name}**")
        except:
            pass

    # Register handler
    async def register_handler_info():
        await register_handler_doc(
            filename="delall.py",
            command="Delall",
            description="Deletes all your own messages silently in a chat.",
            usage=".delall <chat_id>"
        )

    asyncio.create_task(register_handler_info())
