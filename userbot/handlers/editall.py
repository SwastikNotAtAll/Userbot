import asyncio
import random
from telethon import events
from shared.state import state, register_handler_doc
from .error import safe_handler

SET_HANDLER = True
# Random messages to edit to
EDIT_TEXTS = ["selling drugs at @999 per 5g dm fast", "wanna get **cked ?", "selling allen modules at negotiatable prices, only at @1999","test", "itna add na kr skta ab msgs"]


def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r"^\.editall(?:\s|$)(.*)"))
    @safe_handler("editall.py", sync_callback)
    async def editall_handler(event):

        # Owner-only
        if event.sender_id != state["owner_id"]:
            return

        arg = event.pattern_match.group(1).strip()
        if not arg:
            await event.reply("Usage: .editall <chat_id>")
            return

        # Convert chat_id
        try:
            chat_id = int(arg)
        except Exception as e:
            await event.reply(f"Invalid chat id. Error: {e}")
            return

        # Fetch chat entity
        try:
            chat = await client.get_entity(chat_id)
            chat_name = chat.title if hasattr(chat, "title") else "Private Chat"
        except Exception:
            await event.reply("ƒαιℓє∂ вƈσz уσυ αяєηт α ραят σƒ тнє тαяgєт ƈнαт!")
            return

        # Start progress message
        try:
            progress_msg = await event.reply(f"Editing messages from {chat_name}...")
        except Exception as e:
            await event.reply(str(e))
            return

        edited_count = 0

        try:
            async for msg in client.iter_messages(chat_id, from_user=state["owner_id"]):

                # Random content for edit
                new_text = random.choice(EDIT_TEXTS)

                try:
                    await msg.edit(new_text)
                    edited_count += 1
                except Exception:
                    continue  # Skip failed edits

                # Update every 50 edits
                if edited_count % 50 == 0:
                    try:
                        await progress_msg.edit(f"Edited {edited_count} msgs from {chat_name}")
                    except:
                        pass

                # Delay ~3 seconds (20 edits per minute)
                await asyncio.sleep(3)

        except Exception as e:
            await event.reply(f"{e}")
            return

        # Final summary
        try:
            await progress_msg.edit(f"Edited {edited_count} msgs from {chat_name}")
        except:
            pass

        # Auto delete after 5 minutes
        try:
            await asyncio.sleep(300)
            await progress_msg.delete()
        except:
            pass

    # Register handler info
    async def register_handler_info():
        await register_handler_doc(
            filename="editall.py",
            command="Editall",
            description="Edits all your messages slowly in a chat.",
            usage=".editall <chat_id>"
        )

    asyncio.create_task(register_handler_info())
