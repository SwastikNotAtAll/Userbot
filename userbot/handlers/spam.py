import os
import asyncio
from telethon import events
from telethon.errors import FloodWaitError, ChatWriteForbiddenError, ChatAdminRequiredError
from shared.state import state, register_handler_doc, is_authorized
from .error import safe_handler

SET_HANDLER = True
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    active_spams = {}

    @client.on(events.NewMessage(pattern=r"^\.spam(?:\s|$)(.*)"))
    @safe_handler("spam.py", sync_callback)
    async def spam_handler(event):
        if event.sender_id != state["owner_id"]:
            return

        args = event.pattern_match.group(1).strip().split(" ", 1)
        reply = await event.get_reply_message()
        chat = event.chat_id

        # --- Parse amount and text ---
        if reply and len(args) == 1 and args[0].isdigit():
            amount = int(args[0])
            text = None
        elif len(args) == 2 and args[0].isdigit():
            amount = int(args[0])
            text = args[1]
        else:
            await event.reply("**Usage:** `.spam <amount> <text>` or reply with `.spam <amount>` to media.")
            return

        # Delete trigger
        try:
            await event.delete()
        except Exception:
            pass

        # Skip if already active
        if chat in active_spams:
            return

        active_spams[chat] = True
        sent_messages = []

        try:
            # --- Case 1: Replied media ---
            if reply and not text:
                try:
                    mime = (reply.document.mime_type if reply.document else "").lower()
                except Exception:
                    mime = ""
                file_name = reply.file.name if reply.file else ""

                # --- Stickers (static / animated / video) ---
                if reply.sticker:
                    file_path = await client.download_media(reply)
                    for i in range(amount):
                        if chat not in active_spams:
                            break
                        try:
                            # Static sticker (.webp)
                            if "webp" in mime or file_name.endswith(".webp"):
                                msg = await client.send_file(
                                    chat, file_path,
                                    force_document=False, supports_streaming=False
                                )

                            # Animated sticker (.tgs)
                            elif "tgs" in mime or file_name.endswith(".tgs"):
                                msg = await client.send_file(
                                    chat, file_path,
                                    mime_type="application/x-tgsticker",
                                    force_document=False
                                )

                            # Video sticker (.webm / .mp4.webm)
                            elif "webm" in mime or file_name.endswith((".webm", ".mp4.webm")):
                                msg = await client.send_file(
                                    chat, file_path,
                                    mime_type="video/webm",
                                    attributes=reply.document.attributes if reply.document else None,
                                    force_document=False
                                )

                            else:
                                msg = await client.send_file(chat, file_path, force_document=False)

                            sent_messages.append(msg.id)

                        except (FloodWaitError, ChatWriteForbiddenError, ChatAdminRequiredError):
                            break
                        await asyncio.sleep(0.15)
                    if os.path.exists(file_path):
                        os.remove(file_path)

                # --- GIF / Video ---
                elif reply.gif or "video/mp4" in mime:
                    file_path = await client.download_media(reply, file="temp_gif.mp4")
                    for i in range(amount):
                        if chat not in active_spams:
                            break
                        try:
                            msg = await client.send_file(chat, file_path, force_document=False)
                            sent_messages.append(msg.id)
                        except (FloodWaitError, ChatWriteForbiddenError, ChatAdminRequiredError):
                            break
                        await asyncio.sleep(0.15)
                    if os.path.exists(file_path):
                        os.remove(file_path)

                # --- Other media (photo / doc / audio etc.) ---
                else:
                    file_path = await client.download_media(reply, file="temp_media")
                    for i in range(amount):
                        if chat not in active_spams:
                            break
                        try:
                            msg = await client.send_file(chat, file_path, force_document=False)
                            sent_messages.append(msg.id)
                        except (FloodWaitError, ChatWriteForbiddenError, ChatAdminRequiredError):
                            break
                        await asyncio.sleep(0.15)
                    if os.path.exists(file_path):
                        os.remove(file_path)

            # --- Case 2: Text spam ---
            elif text:
                for i in range(amount):
                    if chat not in active_spams:
                        break
                    try:
                        msg = await event.respond(text)
                        sent_messages.append(msg.id)
                    except (FloodWaitError, ChatWriteForbiddenError, ChatAdminRequiredError):
                        break
                    await asyncio.sleep(0.15)

        except Exception:
            pass
        finally:
            # Cleanup after 5 min
            async def cleanup():
                await asyncio.sleep(300)
                for msg_id in sent_messages:
                    try:
                        await client.delete_messages(chat, msg_id)
                    except Exception:
                        continue
            asyncio.create_task(cleanup())
            active_spams.pop(chat, None)

    # --- Manual stop ---
    @client.on(events.NewMessage(pattern=r"^\.stopspam$"))
    @safe_handler("spam.py", sync_callback)
    async def stop_spam_handler(event):
        if event.sender_id != state["owner_id"]:
            return

        chat = event.chat_id
        if chat in active_spams:
            active_spams.pop(chat, None)
            await event.reply("ѕтσρρє∂ ѕραммιηg!")
        else:
            await event.reply("ησ σηgσιηg ѕραмѕ ƒσυη∂.")

    spam_handler._from_userbot_reload = True
    stop_spam_handler._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="spam.py",
            command="Spam",
            description="Spams text, stickers, GIFs, or replied media multiple times. Supports static, animated (.tgs), and video (.webm) stickers.",
            usage=".spam <amount> <text> | reply with .spam <amount>\n.stopspam to stop ongoing spam"
        )

    asyncio.create_task(register_handler_info())
