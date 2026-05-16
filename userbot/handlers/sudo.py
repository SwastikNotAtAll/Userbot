from telethon import events
from telethon.utils import get_display_name
from shared.state import state, register_handler_doc, is_owner_or_super
from .error import safe_handler
from html import escape
import asyncio

SET_HANDLER = True
def init(client, sync_callback):
    if not SET_HANDLER:
        return

    # ----------------------------
    # Add Normal Sudo (Owner Only)
    # ----------------------------
    @client.on(events.NewMessage(pattern=r'\.addsudo(?:\s+(.*))?'))
    @safe_handler("sudo.py", sync_callback)
    async def addsudo(event):
        if event.sender_id != state["owner_id"]:
            return

        arg = event.pattern_match.group(1)
        uid = None
        user = None

        if event.is_reply:
            replied = await event.get_reply_message()
            uid = replied.sender_id
            user = await client.get_entity(uid)
        elif arg:
            try:
                user = await client.get_entity(arg.strip())
                uid = user.id
            except Exception:
                await event.edit("<b>Could not Find User.</b>", parse_mode="html")
                return
        else:
            await event.edit("<b>Reply to a user or provide @username / user ID.</b>", parse_mode="html")
            return

        if uid in state.get("sudo_users", []):
            await event.edit("<b>User is already in Sudo list.</b>", parse_mode="html")
            return

        if uid in state.get("super_sudo_users", []):
            await event.edit("<b>User is already a Super Sudo.</b>", parse_mode="html")
            return

        state.setdefault("sudo_users", []).append(uid)
        await sync_callback()

        name = escape(get_display_name(user) or "Unknown")
        click_name = f'<a href="tg://user?id={uid}">{name}</a>'

        text = (
            f"<b>Successfully added {click_name} to Sudo Users!</b>\n"
            f"<b>├ Name : {click_name}</b>\n"
            f"<b>├ User id:</b> <code>{uid}</code>\n"
        )

        if user.username:
            text += f"<b>├ Username:</b> @{escape(user.username)}\n"

        text += "<b>└ Privilege:</b> Can't Access All Cmd."

        await event.edit(text, parse_mode="html", link_preview=False)

    # ----------------------------
    # Add Super Sudo (Owner Only)
    # ----------------------------
    @client.on(events.NewMessage(pattern=r'\.supersudo(?:\s+(.*))?'))
    @safe_handler("sudo.py", sync_callback)
    async def supersudo(event):
        if event.sender_id != state["owner_id"]:
            return

        arg = event.pattern_match.group(1)
        uid = None
        user = None

        if event.is_reply:
            replied = await event.get_reply_message()
            uid = replied.sender_id
            user = await client.get_entity(uid)
        elif arg:
            try:
                user = await client.get_entity(arg.strip())
                uid = user.id
            except Exception:
                await event.edit("<b>Could not Find User.</b>", parse_mode="html")
                return
        else:
            await event.edit("<b>Reply to a user or provide @username / user ID.</b>", parse_mode="html")
            return

        if uid in state.get("super_sudo_users", []):
            await event.edit("<b>User is already a Super Sudo. </b>", parse_mode="html")
            return

        if uid in state.get("sudo_users", []):
            state["sudo_users"].remove(uid)

        state.setdefault("super_sudo_users", []).append(uid)
        await sync_callback()

        name = escape(get_display_name(user) or "Unknown")
        click_name = f'<a href="tg://user?id={uid}">{name}</a>'

        text = (
            f"<b>Successfully added {click_name} as Super Sudo!</b>\n"
            f"<b>├ Name : {click_name}</b>\n"
            f"<b>├ User id:</b> <code>{uid}</code>\n"
        )

        if user.username:
            text += f"<b>├ Username:</b> @{escape(user.username)}\n"

        text += "<b>└ Privilege:</b> All Cmds Accessible."

        await event.edit(text, parse_mode="html", link_preview=False)

    # ----------------------------
    # Remove Sudo / Super Sudo
    # ----------------------------
    @client.on(events.NewMessage(pattern=r'\.rmsudo(?:\s+(.*))?'))
    @safe_handler("sudo.py", sync_callback)
    async def rmsudo(event):
        if event.sender_id != state["owner_id"]:
            return

        arg = event.pattern_match.group(1)
        uid = None
        user = None

        if event.is_reply:
            replied = await event.get_reply_message()
            uid = replied.sender_id
            user = await client.get_entity(uid)
        elif arg:
            try:
                user = await client.get_entity(arg.strip())
                uid = user.id
            except Exception:
                await event.edit("<b>Could not Find User.</b>", parse_mode="html")
                return
        else:
            await event.edit("<b>Reply to a user or provide @username / user ID.</b>", parse_mode="html")
            return

        removed = False

        if uid in state.get("super_sudo_users", []):
            state["super_sudo_users"].remove(uid)
            removed = True
        elif uid in state.get("sudo_users", []):
            state["sudo_users"].remove(uid)
            removed = True

        if not removed:
            await event.edit("<b>User is not in Sudo List.</b>", parse_mode="html")
            return

        await sync_callback()

        name = escape(get_display_name(user) or "Unknown")
        click_name = f'<a href="tg://user?id={uid}">{name}</a>'

        text = (
            f"<b>Successfully removed {click_name} from Sudo Users!</b>\n"
            "<b>└ They Are No Longer Accessible To Any UB Commands.</b>"
        )

        await event.edit(text, parse_mode="html", link_preview=False)

    # ----------------------------
    # Show Sudo List
    # ----------------------------
    @client.on(events.NewMessage(pattern=r'\.sudolist'))
    @safe_handler("sudo.py", sync_callback)
    async def sudolist(event):
        if not is_owner_or_super(event.sender_id):
            return

        normal_sudos = state.get("sudo_users", [])
        super_sudos = state.get("super_sudo_users", [])

        text = ""

        if normal_sudos:
            text += "<u><b>Sudo Users:-</b></u>\n"
            for i, uid in enumerate(normal_sudos):
                try:
                    user = await client.get_entity(uid)
                    name = escape(get_display_name(user) or "Unknown")
                except Exception:
                    name = "Unknown"

                click_name = f'<a href="tg://user?id={uid}">{name}</a>'

                prefix = "└" if i == len(normal_sudos) - 1 else "├"
                text += f"{prefix} {click_name} | <code>{uid}</code>\n"

            text += "\n"

        if super_sudos:
            text += "<u><b>Super Sudo Users:-</b></u>\n"
            for i, uid in enumerate(super_sudos):
                try:
                    user = await client.get_entity(uid)
                    name = escape(get_display_name(user) or "Unknown")
                except Exception:
                    name = "Unknown"

                click_name = f'<a href="tg://user?id={uid}">{name}</a>'
                prefix = "└" if i == len(super_sudos) - 1 else "├"
                text += f"{prefix} {click_name} | <code>{uid}</code>\n"

        if not normal_sudos and not super_sudos:
            text = "<b>No Sudo Users Found.</b>"

        await event.reply(text.strip(), parse_mode="html", link_preview=False)

    asyncio.create_task(register_handler_doc(
        filename="sudo.py",
        command="Sudo",
        description="Manage sudo and super sudo users.",
        usage=(
            ".addsudo <reply/username/ID>\n"
            ".supersudo <reply/username/ID>\n"
            ".rmsudo <reply/username/ID>\n"
            ".sudolist"
        )
    ))
