# userbot/handlers/telegraph.py

import os
import asyncio
import aiohttp
import html
from telethon import events
from telegraph import Telegraph, exceptions
from shared.state import register_handler_doc, is_authorized, maybe_warn_spammer
from .error import safe_handler


SET_HANDLER = True


# -----------------------------------
# Upload to Catbox
# -----------------------------------
async def upload_to_catbox(file_path: str) -> str:
    url = "https://catbox.moe/user/api.php"

    async with aiohttp.ClientSession() as session:
        with open(file_path, "rb") as f:
            form = aiohttp.FormData()
            form.add_field("reqtype", "fileupload")
            form.add_field("userhash", "")
            form.add_field(
                "fileToUpload",
                f,
                filename=os.path.basename(file_path),
                content_type="application/octet-stream"
            )

            async with session.post(url, data=form) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Upload failed: HTTP {resp.status}")

                text = await resp.text()
                if text.startswith("http"):
                    return text

                raise RuntimeError(f"Upload failed: {text}")


# -----------------------------------
# Init
# -----------------------------------
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    telegraph = Telegraph()
    telegraph.create_account(short_name="Userbot")

    @client.on(events.NewMessage(pattern=r"^\.telegraph(?:\s|$)|^\.tgh(?:\s|$)"))
    @safe_handler("telegraph.py", sync_callback)
    async def telegraph_handler(event):

        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        reply = await event.get_reply_message()
        if not reply:
            await event.reply("`Reply to text or supported media.`")
            return

        msg = await event.reply("`Processing...`")

        try:
            temp_dir = "./temp"
            os.makedirs(temp_dir, exist_ok=True)

            # ----------------------------
            # TEXT → TELEGRAPH
            # ----------------------------
            if reply.text:

                text_content = reply.text.strip()
                if not text_content:
                    await msg.edit("`Empty text cannot be posted.`")
                    return

                title = text_content.split("\n")[0][:60] or "Telegraph Post"

                # SAFE + SIMPLE (MOST STABLE)
                safe_text = html.escape(text_content)
                safe_text = safe_text.replace("\n", "<br>")
                html_content = f"<p>{safe_text}</p>"

                response = telegraph.create_page(
                    title=title,
                    html_content=html_content
                )

                await msg.edit(
                    f"https://telegra.ph/{response['path']}"
                )
                return

            # ----------------------------
            # MEDIA → CATBOX
            # ----------------------------
            elif reply.media:

                path = await reply.download_media(file=temp_dir)

                # Convert static sticker to PNG
                if reply.sticker and path.endswith(".webp"):
                    try:
                        from PIL import Image
                        im = Image.open(path).convert("RGBA")
                        new_path = path.replace(".webp", ".png")
                        im.save(new_path)
                        os.remove(path)
                        path = new_path
                    except Exception as e:
                        await msg.edit(f"`Sticker conversion failed: {e}`")
                        return

                try:
                    media_url = await upload_to_catbox(path)
                finally:
                    if os.path.exists(path):
                        os.remove(path)

                await msg.edit(f"`Uploaded:`\n{media_url}")
                return

            else:
                await msg.edit("`Unsupported message type.`")

        except exceptions.TelegraphException as e:
            await msg.edit(f"`Telegraph Error:` {e}")

        except Exception as e:
            await msg.edit(f"`Error:` {e}")

    telegraph_handler._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="telegraph.py",
            command="Telegraph",
            description="Uploads text to Telegraph or media to Catbox.",
            usage=".telegraph or .tgh (reply to message)"
        )

    asyncio.create_task(register_handler_info())
