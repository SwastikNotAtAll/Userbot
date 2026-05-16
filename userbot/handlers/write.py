# userbot/handlers/write.py
import os
import asyncio
from telethon import events
from PIL import Image, ImageDraw, ImageFont
from shared.state import state, register_handler_doc, maybe_warn_spammer, is_authorized
from .error import safe_handler


SET_HANDLER = True
# ----------------------------
# Helper functions
# ----------------------------
def split_text_lines(text, max_chars=50):
    """Split text into multiple lines for writing."""
    words = text.split()
    lines, line = [], ""
    for word in words:
        if len(line + " " + word) <= max_chars:
            line += (" " + word if line else word)
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def ensure_temp_dir():
    """Ensure temp directory exists."""
    if not os.path.exists("./temp"):
        os.makedirs("./temp", exist_ok=True)


# ----------------------------
# Main write command
# ----------------------------
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r"^\.write(?:\s|$)(.*)"))
    @safe_handler("write.py", sync_callback)
    async def write_handler(event):
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        # Determine text input
        text_arg = event.pattern_match.group(1).strip()
        if event.is_reply:
            reply = await event.get_reply_message()
            text = reply.message or ""
        elif text_arg:
            text = text_arg
        else:
            await event.reply("`✘ Please provide text or reply to a message.`")
            return

        # Paths
        template_path = "./resources/template.jpg"
        font_path = "./resources/assfont.ttf"
        output_path = "./temp/write_result.jpg"

        # Ensure temp folder exists
        ensure_temp_dir()

        # Validate resources
        if not os.path.exists(template_path):
            await event.reply("`Template image not found`.")
            return
        if not os.path.exists(font_path):
            await event.reply("`Font not found`.")
            return

        # Render text onto image
        try:
            img = Image.open(template_path)
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(font_path, 30)

            x, y = 150, 140
            line_height = font.getbbox("hg")[3] - font.getbbox("hg")[1]
            for line in split_text_lines(text):
                draw.text((x, y), line, fill=(1, 22, 55), font=font)
                y += line_height - 5

            img.save(output_path)
            await event.reply(file=output_path)

        except Exception as e:
            await event.reply(f"Error: `{e}`")

        finally:
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass

    write_handler._from_userbot_reload = True
    async def register_handler_info():
        await register_handler_doc(
            filename="write.py",
            command="Write",
            description="Writes anything provided by the user in a page.",
            usage=".write <word> | reply to a text with .write"
        )

    # Schedule registration task
    asyncio.create_task(register_handler_info())
