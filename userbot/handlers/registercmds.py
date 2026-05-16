import os
import json
import base64
import asyncio
from telethon import events
from shared.state import state, register_handler_doc, is_authorized, is_owner_or_super, maybe_warn_spammer
from .error import safe_handler

# --------------------------
# IN-MEMORY STORAGE
# --------------------------
REGISTERED_CMDS = {}       # {cmd: {...}}
BACKUP_FILE = "registered_cmds.json"
SET_HANDLER = True

# --------------------------
# BACKUP / RESTORE HELPERS
# --------------------------
async def save_to_file():
    with open(BACKUP_FILE, "w") as f:
        json.dump(REGISTERED_CMDS, f, indent=4)


async def load_from_file(path: str):
    global REGISTERED_CMDS
    with open(path, "r") as f:
        REGISTERED_CMDS = json.load(f)


# --------------------------
# USERBOT INIT HOOK
# --------------------------
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    # --------------------------
    # REGISTER COMMAND
    # --------------------------
    @client.on(events.NewMessage(pattern=r"\.register(?:\s+(\S+))?"))
    @safe_handler("registercmds.py", sync_callback)
    async def register_cmd(event):
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        args = event.pattern_match.group(1)

        if not args:
            return await event.reply(
                "Usage: `.register <cmd>`\nReply with text/media or type text."
            )

        cmd = args.lower()
        reply = await event.get_reply_message()

        # --------------------------
        # REPLY TEXT
        # --------------------------
        if reply and reply.text:
            REGISTERED_CMDS[cmd] = {
                "type": "text",
                "content": reply.text
            }
            return await event.reply(f"Registered `.{cmd}`.")

        # --------------------------
        # REPLY MEDIA
        # --------------------------
        if reply and reply.media:
            raw = await reply.download_media(bytes)
            if not raw:
                return await event.reply("Failed to download media.")

            file_name = reply.file.name if reply.file else "file"
            mime = reply.file.mime_type if reply.file else "application/octet-stream"

            REGISTERED_CMDS[cmd] = {
                "type": "media",
                "file_name": file_name,
                "mime": mime,
                "content": base64.b64encode(raw).decode("utf-8")
            }

            return await event.reply(f"Registered `.{cmd}`.")

        # --------------------------
        # DIRECT TEXT INPUT
        # --------------------------
        raw = event.raw_text.split(" ", 1)
        if len(raw) > 1:
            text = raw[1]
            REGISTERED_CMDS[cmd] = {
                "type": "text",
                "content": text
            }
            return await event.reply(f"Registered `.{cmd}` successfully.")

        return await event.reply("Reply to content or provide text to register.")


    # --------------------------
    # EXECUTE CUSTOM COMMANDS
    # --------------------------
    @client.on(events.NewMessage(pattern=r"^\.(\w+)$"))
    @safe_handler("registercmds.py", sync_callback)
    async def execute_custom(event):
        cmd = event.pattern_match.group(1).lower()

        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        if cmd not in REGISTERED_CMDS:
            return

        data = REGISTERED_CMDS[cmd]

        # TEXT RESPONSE
        if data["type"] == "text":
            return await event.reply(data["content"])

        # MEDIA RESPONSE
        if data["type"] == "media":
            raw = base64.b64decode(data["content"])
            return await client.send_file(
                event.chat_id,
                raw,
                caption=f".{cmd}",
                force_document=True,
                file_name=data["file_name"],
            )

    # --------------------------
    # UNREGISTER COMMAND
    # --------------------------
    @client.on(events.NewMessage(pattern=r"\.unregister(?:\s+(\S+))?"))
    @safe_handler("registercmds.py", sync_callback)
    async def unregister_cmd(event):
        if not is_owner_or_super(event.sender_id):
            return

        cmd = event.pattern_match.group(1)
        if not cmd:
            return await event.reply("Usage: `.unregister <cmd>`")

        cmd = cmd.lower()

        if cmd not in REGISTERED_CMDS:
            return await event.reply(f"No such command `.{cmd}` exists.")

        del REGISTERED_CMDS[cmd]
        return await event.reply(f"Unregistered `.{cmd}` successfully.")
    # --------------------------
    # LIST REGISTERED COMMANDS
    # --------------------------
    @client.on(events.NewMessage(pattern=r"\.cmdsregistered$"))
    @safe_handler("registercmds.py", sync_callback)
    async def list_cmds(event):
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        if not REGISTERED_CMDS:
            return await event.reply("No registered commands found.")

        msg = "**Registered Commands:**\n\n"
        for c in REGISTERED_CMDS.keys():
            msg += f"✧ `.{c}`\n"

        return await event.reply(msg)


    # --------------------------
    # BACKUP COMMANDS (OWNER ONLY)
    # --------------------------
    @client.on(events.NewMessage(pattern=r"\.backupcmds$"))
    @safe_handler("registercmds.py", sync_callback)
    async def backup_cmds(event):
        if not is_owner_or_super(event.sender_id):
            return

        await save_to_file()
        await event.reply("Backup created.", file=BACKUP_FILE)


    # --------------------------
    # RESTORE COMMANDS (OWNER ONLY)
    # --------------------------
    @client.on(events.NewMessage(pattern=r"\.restorecmds$"))
    @safe_handler("registercmds.py", sync_callback)
    async def restore_cmds(event):
        if not is_owner_or_super(event.sender_id):
            return

        reply = await event.get_reply_message()
        if not reply or not reply.media:
            return await event.reply("Reply to the JSON backup file.")

        try:
            path = await reply.download_media()
            await load_from_file(path)
            os.remove(path)
            return await event.reply("Commands restored successfully.")
        except Exception as e:
            return await event.reply(f"Restore failed: {e}")


    # --------------------------
    # REGISTER DOCUMENTATION
    # --------------------------
    async def register_handler_info():
        await register_handler_doc(
            filename="registercmds.py",
            command="Register",
            description="Creates memory-based custom commands.",
            usage=".register <cmd>\n.cmdsregistered\n.backupcmds\n.restorecmds"
        )

    asyncio.create_task(register_handler_info())
