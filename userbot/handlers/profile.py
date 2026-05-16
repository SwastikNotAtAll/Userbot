# userbot/handlers/profile.py

import os
import asyncio
from telethon import events
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from shared.state import state, register_handler_doc
from .error import safe_handler

SET_HANDLER = True


def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    # =========================
    # .setbio
    # =========================
    @client.on(events.NewMessage(pattern=r"^\.setbio(?:\s+(.*))?$"))
    @safe_handler("profile.py", sync_callback)
    async def setbio_handler(event):

        if event.sender_id != state["owner_id"]:
            return

        try:
            bio = event.pattern_match.group(1)

            # If reply exists, use reply text
            if event.is_reply:
                reply = await event.get_reply_message()
                if reply.text:
                    bio = reply.text

            if not bio:
                await event.reply("Usage: reply to text or use .setbio <text>")
                return

            await client(UpdateProfileRequest(about=bio.strip()))
            await event.reply("𝗕𝗶𝗼 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗨𝗽𝗱𝗮𝘁𝗲𝗱!")

        except Exception as e:
            await event.reply(f"Error:\n`{e}`")
            raise

    setbio_handler._from_userbot_reload = True

    # =========================
    # .setname
    # =========================
    @client.on(events.NewMessage(pattern=r"^\.setname(?:\s+(.*))?$"))
    @safe_handler("profile.py", sync_callback)
    async def setname_handler(event):

        if event.sender_id != state["owner_id"]:
            return

        try:
            names = event.pattern_match.group(1)

            # If reply exists, use reply text
            if event.is_reply:
                reply = await event.get_reply_message()
                if reply.text:
                    names = reply.text

            if not names:
                await event.reply("Usage: reply to text or use .setname <first>//<last>")
                return

            names = names.strip()
            first_name = names
            last_name = ""

            if "//" in names:
                first_name, last_name = names.split("//", 1)

            await client(
                UpdateProfileRequest(
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                )
            )

            await event.reply("𝗡𝗮𝗺𝗲 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗨𝗽𝗱𝗮𝘁𝗲𝗱!")

        except Exception as e:
            await event.reply(f"Error:\n`{e}`")
            raise

    setname_handler._from_userbot_reload = True

    # =========================
    # .setpic
    # =========================
    @client.on(events.NewMessage(pattern=r"^\.setpic$"))
    @safe_handler("profile.py", sync_callback)
    async def setpic_handler(event):

        if event.sender_id != state["owner_id"]:
            return

        try:
            if not event.is_reply:
                await event.reply("Reply to a photo, sticker, or document.")
                return

            reply = await event.get_reply_message()

            if not (reply.photo or reply.sticker or reply.document):
                await event.reply("Reply must be a photo, sticker, or document.")
                return

            file_path = await reply.download_media()

            file = await client.upload_file(file_path)

            # Detect video profile pic
            if reply.video:
                await client(UploadProfilePhotoRequest(video=file))
            else:
                await client(UploadProfilePhotoRequest(file=file))

            await event.reply("𝗧𝗮𝗿𝗴𝗲𝘁 𝗣𝗙𝗣 𝗛𝗮𝘀 𝗕𝗲𝗲𝗻 𝗦𝗲𝘁.")

        except Exception as e:
            await event.reply(f"Error:\n`{e}`")
            raise

        finally:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass

    setpic_handler._from_userbot_reload = True

    # =========================
    # .delpfp (delete latest)
    # =========================
    @client.on(events.NewMessage(pattern=r"^\.delpfp$"))
    @safe_handler("profile.py", sync_callback)
    async def delpfp_handler(event):

        if event.sender_id != state["owner_id"]:
            return

        try:
            photos = await client.get_profile_photos("me", limit=1)

            if not photos:
                await event.reply("𝗡𝗼 𝗣𝗙𝗣𝘀 𝗙𝗼𝘂𝗻𝗱.")
                return

            await client(DeletePhotosRequest(photos))
            await event.reply("𝗥𝗲𝗰𝗲𝗻𝘁 𝗣𝗙𝗣 𝗛𝗮𝘀 𝗕𝗲𝗲𝗻 𝗗𝗲𝗹𝗲𝘁𝗲𝗱.")

        except Exception as e:
            await event.reply(f"Error:\n`{e}`")
            raise

    delpfp_handler._from_userbot_reload = True

    # =========================
    # Register Docs
    # =========================
    async def register_handler_info():
        await register_handler_doc(
            filename="profile.py",
            command="Profile Tools",
            description="Manage your Telegram profile (Owner only).",
            usage=(
                ".setbio <text> (or reply)\n"
                ".setname <first>//<last> (or reply)\n"
                ".setpic (reply to media)\n"
                ".delpfp"
            ),
        )

    asyncio.create_task(register_handler_info())
