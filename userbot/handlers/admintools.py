# userbot/handlers/admintools.py
import asyncio
from telethon import events
from telethon.errors import ChatAdminRequiredError, UserAdminInvalidError
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from shared.state import state, register_handler_doc
from .error import safe_handler

SET_HANDLER = True


# ----------------------------
# Rights Objects
# ----------------------------

BAN_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=False,
    send_messages=False,
    send_media=False,
    send_stickers=False,
    send_gifs=False,
    send_games=False,
    send_inline=False,
    embed_links=False
)


# ----------------------------
# Init Function
# ----------------------------

def init(client, sync_callback=None):
    if not SET_HANDLER:
        return


    # ============================
    # Command: .gban
    # ============================
    @client.on(events.NewMessage(pattern=r"^\.gban(?:\s+(.*))?$"))
    @safe_handler("admintools.py", sync_callback)
    async def gban_handler(event):

        if event.sender_id != state["owner_id"]:
            return

        user_input = event.pattern_match.group(1)

        # Resolve target
        if event.is_reply:
            reply = await event.get_reply_message()
            target = await reply.get_sender()
        elif user_input:
            try:
                target = await client.get_entity(user_input.strip())
            except Exception:
                await event.reply("**User not found.**", parse_mode="md")
                return
        else:
            await event.reply("**Reply to a user or provide username/userid.**", parse_mode="md")
            return

        first_name = target.first_name or ""

        msg = await event.reply("**Processing Gban...**", parse_mode="md")

        count = 0  # Success counter

        async for dialog in client.iter_dialogs():
            if not dialog.is_group:
                continue

            try:
                perms = await client.get_permissions(dialog.id, 'me')
                if not perms.is_admin or not perms.ban_users:
                    continue

                await client(EditBannedRequest(
                    dialog.id,
                    target.id,
                    BAN_RIGHTS
                ))

                count += 1

            except (ChatAdminRequiredError, UserAdminInvalidError):
                continue
            except Exception:
                continue

        await msg.edit(
            f"**User {first_name} has been Gbanned from {count} Groups!**",
            parse_mode="md"
        )


    # ============================
    # Command: .ungban
    # ============================
    @client.on(events.NewMessage(pattern=r"^\.ungban(?:\s+(.*))?$"))
    @safe_handler("admintools.py", sync_callback)
    async def ungban_handler(event):

        if event.sender_id != state["owner_id"]:
            return

        user_input = event.pattern_match.group(1)

        # Resolve target
        if event.is_reply:
            reply = await event.get_reply_message()
            target = await reply.get_sender()
        elif user_input:
            try:
                target = await client.get_entity(user_input.strip())
            except Exception:
                await event.reply("**User not found.**", parse_mode="md")
                return
        else:
            await event.reply("**Reply to a user or provide username/userid.**", parse_mode="md")
            return

        first_name = target.first_name or ""

        msg = await event.reply("**Processing global unban...**", parse_mode="md")

        count = 0  # Success counter

        async for dialog in client.iter_dialogs():
            if not dialog.is_group:
                continue

            try:
                perms = await client.get_permissions(dialog.id, 'me')
                if not perms.is_admin or not perms.ban_users:
                    continue

                await client(EditBannedRequest(
                    dialog.id,
                    target.id,
                    UNBAN_RIGHTS
                ))

                count += 1

            except (ChatAdminRequiredError, UserAdminInvalidError):
                continue
            except Exception:
                continue

        await msg.edit(
            f"**User {first_name} has been UnGbanned from {count} Groups!**",
            parse_mode="md"
        )


    # Reload support
    gban_handler._from_userbot_reload = True
    ungban_handler._from_userbot_reload = True


    async def register_handler_info():
        await register_handler_doc(
            filename="admintools.py",
            command="Gban / Ungban",
            description="Globally bans or unbans a user from all groups where you are admin.",
            usage=".gban <reply/username/userid>\n.ungban <reply/username/userid>"
        )

    asyncio.create_task(register_handler_info())
