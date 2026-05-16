import asyncio
from telethon import events
from telethon.errors import ChatAdminRequiredError, UserAdminInvalidError, FloodWaitError
from shared.state import state, register_handler_doc, is_authorized, is_owner_or_super

SET_HANDLER = True
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    # --- Command: .zombies ---
    @client.on(events.NewMessage(pattern=r'^\.zombies$', func=lambda e: e.is_group))
    async def find_zombies(event):
        if not is_owner_or_super(event.sender_id):
            return

        try:
            msg = await event.reply("ᴡᴀɪᴛ ᴀ sᴇᴄ.")

            group = await event.get_chat()
            deleted_accounts = []

            async for user in client.iter_participants(group.id):
                if getattr(user, "deleted", False):
                    deleted_accounts.append(user)

            count = len(deleted_accounts)
            if count == 0:
                await msg.edit("ɴᴏ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄs ɪɴ ᴛʜᴇ ᴄʜᴀᴛ.")
            else:
                plural = "s" if count > 1 else ""
                await msg.edit(
                    f"ғᴏᴜɴᴅ **{count}** ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛ{plural}.\nᴜsᴇ .ᴄʟᴇᴀɴ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴛʜᴇᴍ"
                )

        except Exception as e:
            await msg.edit(f"Error: {type(e).__name__}")

    # --- Command: .clean ---
    @client.on(events.NewMessage(pattern=r'^\.clean$', func=lambda e: e.is_group))
    async def clean_zombies(event):
        if event.sender_id != state["owner_id"]:
            return

        try:
            msg = await event.reply("ʀᴇᴍᴏᴠɪɴɢ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs..")
            group = await event.get_chat()

            deleted_accounts = []
            async for user in client.iter_participants(group.id):
                if getattr(user, "deleted", False):
                    deleted_accounts.append(user)

            if not deleted_accounts:
                await msg.edit("ɴᴏ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs ғᴏᴜɴᴅ ʜᴇʀᴇ")
                return

            removed_count = 0
            failed_count = 0

            for user in deleted_accounts:
                try:
                    await client.edit_permissions(group.id, user.id, view_messages=False)
                    removed_count += 1
                    await asyncio.sleep(0.5)
                except (ChatAdminRequiredError, UserAdminInvalidError):
                    failed_count += 1
                except FloodWaitError as fw:
                    await asyncio.sleep(fw.seconds)
                except Exception:
                    failed_count += 1

            # --- Output Formatting ---
            if removed_count == 0 and failed_count > 0:
                await msg.edit(f"ᴜɴᴀʙʟᴇ ᴛᴏ ʀᴇᴍᴏᴠᴇ {failed_count} ᴅᴜᴇ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇᴅ ʙʏ sᴏᴍᴇᴏɴᴇ ᴇʟsᴇ.")

            elif removed_count > 0 and failed_count == 0:
                await msg.edit("ʀᴇᴍᴏᴠᴇᴅ ᴀʟʟ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs!")

            elif removed_count > 0 and failed_count > 0:
                await msg.edit(
                    f"ʀᴇᴍᴏᴠᴇᴅ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs, ʙᴜᴛ {failed_count} ᴄᴏᴜɴᴅɴ'ᴛ ᴅᴜᴇ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇᴅ ʙʏ sᴏᴍᴇᴏɴᴇ ᴇʟsᴇ."
                )

            else:
                await msg.edit("ɴᴏ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs ғᴏᴜɴᴅ ʜᴇʀᴇ.")

        except ChatAdminRequiredError:
            await msg.edit("ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ʙᴇ ᴀᴅᴍɪɴ ʜᴇʀᴇ ғɪʀsᴛ.")

        except Exception as e:
            await msg.edit(f"ᴇʀʀᴏʀ: {type(e).__name__}")

    # --- Mark for dynamic reload ---
    find_zombies._from_userbot_reload = True
    clean_zombies._from_userbot_reload = True
    async def register_handler_info():
        await register_handler_doc(
            filename="zombies.py",
            command="Zombies",
            description="Used to get and remove deleted accounts from groups",
            usage="Send .zombies | .clean in chat"
          )
    asyncio.create_task(register_handler_info())
