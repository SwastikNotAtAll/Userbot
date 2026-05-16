import time
import asyncio
from telethon import events, functions
from telethon.tl.types import Channel, User
from telethon.tl.functions.messages import GetCommonChatsRequest
from shared.state import state, register_handler_doc, is_authorized

SET_HANDLER = True
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    # =========================================================
    #                       .mystats
    # =========================================================
    @client.on(events.NewMessage(pattern=r'^\.mystats$'))
    async def mystats_handler(event):
        if event.sender_id != state["owner_id"]:
            return
        start_time = time.time()
        private_chats, bots, groups, broadcast_channels = 0, 0, 0, 0
        unread_mentions, unread = 0, 0
        try:
            async for dialog in client.iter_dialogs():
                entity = dialog.entity
                if isinstance(entity, Channel):
                    if getattr(entity, "broadcast", False):
                        broadcast_channels += 1
                    elif getattr(entity, "megagroup", False):
                        groups += 1
                elif isinstance(entity, User):
                    private_chats += 1
                    if getattr(entity, "bot", False):
                        bots += 1

                unread_mentions += getattr(dialog, "unread_mentions_count", 0)
                unread += getattr(dialog, "unread_count", 0)

            me = await client.get_me()
            mention = f'<a href="tg://user?id={me.id}">{me.first_name}</a>'
            full = await client(functions.users.GetFullUserRequest(me.id))

            photos = await client(functions.photos.GetUserPhotosRequest(
                user_id=me.id,
                offset=0,
                max_id=0,
                limit=0
            ))
            pfp_count = photos.count

            dc_info = await client(functions.help.GetNearestDcRequest())
            dc_id = dc_info.this_dc

            stop_time = time.time() - start_time

            caption = (
                f"✧ 𝐍𝐚𝐦𝐞 - {me.first_name or ''} {me.last_name or ''}\n"
                f"✧ 𝐌𝐞𝐧𝐭𝐢𝐨𝐧 - {mention}\n"
                f"✧ 𝐈𝐝 - {me.id}\n"
                f"✧ 𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞 - @{me.username or 'No Username'}\n"
                f"✧ 𝐁𝐢𝐨 - {full.full_user.about or 'No bio set.'}\n"
                f"✧ 𝐏𝐫𝐨𝐟𝐢𝐥𝐞 𝐏𝐡𝐨𝐭𝐨𝐬 - {pfp_count}\n"
                f"✧ 𝐃𝐂 - {dc_id}\n"
                f"✧ 𝐓𝐨𝐭𝐚𝐥 𝐂𝐡𝐚𝐭𝐬 - {private_chats + groups + broadcast_channels}\n"
                f"  ├𝐔𝐬𝐞𝐫𝐬 - {private_chats - bots}\n"
                f"  ├𝐁𝐨𝐭𝐬 - {bots}\n"
                f"  ├𝐆𝐫𝐨𝐮𝐩𝐬 - {groups}\n"
                f"  └𝐂𝐡𝐚𝐧𝐧𝐞𝐥𝐬 - {broadcast_channels}\n\n"
                f"✧ 𝐔𝐧𝐫𝐞𝐚𝐝 𝐌𝐞𝐬𝐬𝐚𝐠𝐞𝐬 - {unread}\n"
                f"✧ 𝐔𝐧𝐫𝐞𝐚𝐝 𝐌𝐞𝐧𝐭𝐢𝐨𝐧𝐬 - {unread_mentions}\n"
                f"✧ 𝐓𝐢𝐦𝐞 𝐓𝐚𝐤𝐞𝐧 - {stop_time:.2f}s"
            )

            try:
                pfp = await client.download_profile_photo(me.id)
                if pfp:
                    await client.send_file(event.chat_id, pfp, caption=caption, reply_to=event.id, parse_mode="html")
                else:
                    await event.reply(caption, parse_mode="html")
            except:
                await event.reply(caption, parse_mode="html")

        except Exception as e:
            await event.reply(
                f"Error while fetching stats:\n<code>{e}</code>",
                parse_mode="html"
            )

    mystats_handler._from_userbot_reload = True

    # =========================================================
    #                       .info
    # =========================================================
    @client.on(events.NewMessage(pattern=r'^\.info(?:\s+(.+))?$'))
    async def info_handler(event):

        if not is_authorized(event.sender_id):
            return

        try:
            target = None
            arg = event.pattern_match.group(1)

            if event.is_reply:
                reply = await event.get_reply_message()
                target = await client.get_entity(reply.sender_id)
            elif arg:
                target = await client.get_entity(arg)
            else:
                target = await client.get_entity(event.sender_id)

            if not isinstance(target, User):
                await event.reply("This command works only for users.")
                return
            mention = f'<a href="tg://user?id={target.id}">{target.first_name}</a>'
            start_time = time.time()
            full = await client(functions.users.GetFullUserRequest(target.id))
            photos = await client(functions.photos.GetUserPhotosRequest(
                user_id=target.id,
                offset=0,
                max_id=0,
                limit=0
            ))
            pfp_count = getattr(photos, "count", len(photos.photos))

            owner_id = state["owner_id"]
            owner = await client.get_entity(owner_id)
            owner_name = owner.first_name or "Owner"

            result = await client(GetCommonChatsRequest(
                user_id=target.id,
                max_id=0,
                limit=100
            ))
            common_groups = len(result.chats)

            stop_time = time.time() - start_time
            is_bot = "Yes" if target.bot else "No"

            caption = (
                f"✧ 𝐍𝐚𝐦𝐞 - {target.first_name or ''} {target.last_name or ''}\n"
                f"✧ 𝐌𝐞𝐧𝐭𝐢𝐨𝐧 - {mention}\n"
                f"✧ 𝐈𝐃 - {target.id}\n"
                f"✧ 𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞 - @{target.username or 'No Username'}\n"
                f"✧ 𝐁𝐢𝐨 - {full.full_user.about or 'No bio set.'}\n"
                f"✧ 𝐏𝐫𝐨𝐟𝐢𝐥𝐞 𝐏𝐡𝐨𝐭𝐨𝐬 - {pfp_count}\n"
                f"✧ 𝐁𝐨𝐭 - {is_bot}\n"
                f"✧ 𝐂𝐨𝐦𝐦𝐨𝐧 𝐆𝐫𝐨𝐮𝐩𝐬 𝐰𝐢𝐭𝐡 {owner_name} - {common_groups}\n"
                f"✧ 𝐓𝐢𝐦𝐞 𝐓𝐚𝐤𝐞𝐧 - {stop_time:.2f}s"
            )

            # 🔥 Reliable Profile Photo Send
            try:
                photos_obj = await client(functions.photos.GetUserPhotosRequest(
                    user_id=target.id,
                    offset=0,
                    max_id=0,
                    limit=1
                ))

                if photos_obj.photos:
                    file = await client.download_media(photos_obj.photos[0])
                    await client.send_file(
                        event.chat_id,
                        file,
                        caption=caption, 
                        reply_to=event.id, 
                        parse_mode="html"
                    )
                else:
                    await event.reply(caption, parse_mode="html")

            except:
                await event.reply(caption, parse_mode="html")

        except Exception as e:
            await event.reply(
                f"Error:\n<code>{e}</code>",
                parse_mode="html"
            )

    info_handler._from_userbot_reload = True

    # =========================================================
    #                   Register Docs
    # =========================================================
    async def register_docs():
        await register_handler_doc(
            filename="userinfo.py",
            command="Mystats & Info",
            description="Fetch your Account Statistics and User Info.",
            usage=".mystats (for owner) & .info"
        )

    asyncio.create_task(register_docs())
