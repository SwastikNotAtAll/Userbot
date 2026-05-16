import asyncio
from telethon import events
from telethon.errors import (
    UsernameNotOccupiedError,
    UserIdInvalidError,
    ChatAdminRequiredError,
)
from shared.state import state, register_handler_doc, is_owner_or_super

SET_HANDLER = True
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r'^\.pic(?: |$)(.*)'))
    async def potocmd(event):
        """Fetch and send all profile photos of a user, by username, ID, or reply (owner-only)."""

        if not is_owner_or_super(event.sender_id):
            return

        input_arg = event.pattern_match.group(1).strip()
        reply = await event.get_reply_message()

        try:
            # --- Determine Target ---
            target = None

            if input_arg:
                try:
                    if input_arg.isdigit():
                        target = await client.get_entity(int(input_arg))
                    else:
                        target = await client.get_entity(input_arg)
                except (UsernameNotOccupiedError, ValueError, UserIdInvalidError):
                    await event.reply("𝙽𝚘 𝙿𝙵𝙿𝚜 𝚏𝚘𝚞𝚗𝚍.")
                    return

            elif reply:
                target = await client.get_entity(reply.sender_id)
            else:
                target = await event.get_chat()

            # --- Fetch Photos ---
            photos = await client.get_profile_photos(target)

            if not photos:
                try:
                    photo = await client.download_profile_photo(target)
                    if photo:
                        await client.send_file(event.chat_id, photo)
                    else:
                        await event.reply("𝚃𝚑𝚎 𝚞𝚜𝚎𝚛 𝚑𝚊𝚜 𝚗𝚘 𝚙𝚏𝚙𝚜.")
                except Exception:
                    await event.reply("𝚃𝚑𝚎 𝚞𝚜𝚎𝚛 𝚑𝚊𝚜 𝚗𝚘 𝚙𝚏𝚙𝚜.")
                return

            # --- Send All Photos (no caption, no deletion) ---
            await client.send_file(event.chat_id, photos)

        except ChatAdminRequiredError:
            await event.reply("𝙽𝚎𝚎𝚍 𝚙𝚎𝚛𝚖𝚒𝚜𝚜𝚒𝚘𝚗 𝚝𝚘 𝚜𝚎𝚗𝚍 𝚖𝚎𝚍𝚒𝚊 𝚑𝚎𝚛𝚎.")
        except Exception as e:
            await event.reply(f"𝙴𝚛𝚛𝚘𝚛: {type(e).__name__}")

    potocmd._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="pic.py",
            command="Pic",
            description="Fetches and sends all profile photos of a user or chat.",
            usage=".pic @username |  reply to user and send .pic",
        )

    asyncio.create_task(register_handler_info())
