# userbot/handlers/memify.py
import os
from telethon import events
from PIL import Image, ImageDraw, ImageFont
from shared.state import state, register_handler_doc, is_authorized, maybe_warn_spammer
from .error import safe_handler
import asyncio

SET_HANDLER = True
# path relative to repo root / bot working directory
FONT_PATH = "./resources/style.ttf"
TEMP_DIR = "./temp"

def ensure_temp_dir():
    os.makedirs(TEMP_DIR, exist_ok=True)


def get_font(size: int):
    """Try to load Impact; fallback to a scaled default font."""
    try:
        return ImageFont.truetype(FONT_PATH, size=size)
    except Exception:
        fallback = ImageFont.load_default()

        class ScaledFont:
            def __init__(self, base_font, scale):
                self.font = base_font
                self.scale = scale

            def getmask(self, text, *args, **kwargs):
                return self.font.getmask(text, *args, **kwargs)

            def getsize(self, text, *args, **kwargs):
                w, h = self.font.getsize(text, *args, **kwargs)
                return int(w * self.scale), int(h * self.scale)

            def getbbox(self, text, *args, **kwargs):
                bbox = self.font.getbbox(text, *args, **kwargs)
                return (
                    bbox[0],
                    bbox[1],
                    int(bbox[2] * self.scale),
                    int(bbox[3] * self.scale),
                )

        return ScaledFont(fallback, scale=3)


def add_meme_text(img, top_text: str = "", bottom_text: str = ""):
    draw = ImageDraw.Draw(img)
    font_size = max(12, int(img.height / 10))
    font = get_font(font_size)
    stroke_width = max(1, int(font_size / 12))

    def get_text_width(text):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    def draw_multiline(text, y, anchor):
        if not text:
            return
        max_width = img.width - 40
        words = text.split()
        lines, line = [], ""
        for word in words:
            test_line = line + " " + word if line else word
            if get_text_width(test_line) <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)

        for i, ln in enumerate(lines):
            line_y = y + i * (font_size + 5)
            draw.text(
                (img.width / 2, line_y),
                ln,
                font=font,
                anchor=anchor,
                fill="white",
                stroke_width=stroke_width,
                stroke_fill="black",
            )

    # Top
    draw_multiline(top_text, 15, "ma")
    # Bottom
    if bottom_text:
        n_lines = max(1, bottom_text.count(" ") // 3 + 1)
        y_start = img.height - (font_size + 5) * n_lines - 20
        draw_multiline(bottom_text, y_start, "ma")
    return img


def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    """
    Register handlers on provided `client`. This matches your other handlers' pattern so
    reload_handlers/test_handlers work properly.
    """

    @client.on(events.NewMessage(pattern=r"^\.mmf(?:\s|$)(.*)"))
    @safe_handler("memify.py", sync_callback)
    async def memify_photo(event):
        # permission check (owner + sudo)
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        args = event.pattern_match.group(1) or ""
        reply = await event.get_reply_message()
        if not reply or not reply.media:
            return await event.reply("`Reply to a photo with .mmf top ; bottom`")

        # parse texts
        if ";" in args:
            top_text, bottom_text = [x.strip() for x in args.split(";", 1)]
        else:
            top_text, bottom_text = args.strip(), ""

        ensure_temp_dir()
        dl_path = os.path.join(TEMP_DIR, "meme_input.jpg")
        out_path = os.path.join(TEMP_DIR, "meme_output.jpg")

        try:
            await reply.download_media(file=dl_path)
            img = Image.open(dl_path).convert("RGB")
            img = add_meme_text(img, top_text, bottom_text)
            img.save(out_path, "JPEG")
            await event.reply(file=out_path)
        except Exception as exc:
            # safe_handler will capture exceptions too, but return a friendly message
            await event.reply(f"Error creating meme: {exc}")
        finally:
            for p in (dl_path, out_path):
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass

    # mark for reload tracking (your reload logic looks for this)
    memify_photo._from_userbot_reload = True

    @client.on(events.NewMessage(pattern=r"^\.mms(?:\s|$)(.*)"))
    @safe_handler("memify.py", sync_callback)
    async def memify_sticker(event):
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        args = event.pattern_match.group(1) or ""
        reply = await event.get_reply_message()
        if not reply or not reply.media:
            return await event.reply("`Reply to a sticker with .mms top ; bottom`")

        if ";" in args:
            top_text, bottom_text = [x.strip() for x in args.split(";", 1)]
        else:
            top_text, bottom_text = args.strip(), ""

        ensure_temp_dir()
        dl_path = os.path.join(TEMP_DIR, "meme_input.webp")
        out_path = os.path.join(TEMP_DIR, "meme_output.webp")

        try:
            await reply.download_media(file=dl_path)
            img = Image.open(dl_path).convert("RGBA")
            img = add_meme_text(img, top_text, bottom_text)
            img.save(out_path, "WEBP")
            await event.reply(file=out_path)
        except Exception as exc:
            await event.reply(f"Error creating meme: {exc}")
        finally:
            for p in (dl_path, out_path):
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass

    memify_sticker._from_userbot_reload = True
    async def register_handler_info():
        await register_handler_doc(
            filename="memify.py",
            command="Memify",
            description="Memify a pic (.mmf) or a sticker (.mms)",
            usage=".mmf | . mms (replied to msg)"
        )

    # Schedule registration task
    asyncio.create_task(register_handler_info())

    # optional basic test function for test_handlers — no heavy ops
    async def test(event):
        # simple sanity: does font load and temp dir exist?
        try:
            ensure_temp_dir()
            _ = get_font(24)
            return True
        except Exception:
            raise

    # expose test() if your test_handlers expects it
    init.test = test
