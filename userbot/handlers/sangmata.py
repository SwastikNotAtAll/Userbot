import asyncio
from telethon import events, functions
from telethon.errors import YouBlockedUserError, FloodWaitError
from shared.state import state, register_handler_doc, is_authorized, maybe_warn_spammer
from .error import safe_handler

SET_HANDLER = True
SANGMATA_BOT = "SangMata_beta_bot"

def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r"^\.sg(?:\s|$)(.*)"))
    @safe_handler("sangmata.py", sync_callback)
    async def sangmata_handler(event):

        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        input_arg = event.pattern_match.group(1).strip()
        reply = await event.get_reply_message()

        target_id = None
        target_first_name = "User"

        try:
            # If command used on reply
            if reply:
                target_id = reply.sender_id
                sender = await reply.get_sender()
                if sender and sender.first_name:
                    target_first_name = sender.first_name

            # If numeric ID provided
            elif input_arg.isdigit():
                target_id = int(input_arg)

            # If username provided
            elif input_arg:
                user = await client.get_entity(input_arg)
                target_id = user.id
                target_first_name = user.first_name or "User"

            else:
                await event.reply("**Usage:** `.sg <username | user_id>` or reply with `.sg`")
                return

        except Exception:
            await event.reply("**Invalid user specified.**")
            return

        msg = await event.reply("`Fetching history...`")

        try:
            async with client.conversation(SANGMATA_BOT, timeout=15) as conv:

                try:
                    await conv.send_message(str(target_id))

                except YouBlockedUserError:
                    # Auto unblock SangMata
                    await client(functions.contacts.UnblockRequest(SANGMATA_BOT))
                    await asyncio.sleep(1)
                    await conv.send_message(str(target_id))

                response = await conv.get_response()
                text = response.text.strip()

                # Formatting
                if "No data available" in text or "No records found" in text:
                    formatted = "**𝐍𝐨 𝐇𝐢𝐬𝐭𝐨𝐫𝐲 𝐅𝐨𝐮𝐧𝐝.**"

                elif text.startswith("👤 History for"):
                    parts = text.split("\n")
                    formatted = f"✧ **History of {target_first_name}**\n\n"

                    name_section = []
                    username_section = []
                    current_section = None

                    for line in parts:
                        line_strip = line.strip().lower()

                        if line_strip.startswith("names"):
                            current_section = "names"
                            continue

                        elif line_strip.startswith("usernames"):
                            current_section = "usernames"
                            continue

                        elif line.startswith("👤"):
                            continue

                        if current_section == "names" and line.strip():
                            name_section.append(line)

                        elif current_section == "usernames" and line.strip():
                            username_section.append(line)

                    if name_section:
                        formatted += "➤ **𝐍𝐚𝐦𝐞𝐬-**\n" + "\n".join(name_section) + "\n\n"

                    if username_section:
                        formatted += "➤ **𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞𝐬-**\n" + "\n".join(username_section)

                else:
                    formatted = text

                await msg.edit(formatted)

        except FloodWaitError as e:
            await msg.edit(f"ƒℓσσ∂ αωαιт: тяу αgαιη αƒтя {e.seconds} ѕє¢ση∂ѕ.")

        except asyncio.TimeoutError:
            await msg.edit("υηαвℓє тσ ƒєтƈн")

        except Exception as e:
            await msg.edit(f"**Error:** `{str(e)}`")


    async def register_handler_info():
        await register_handler_doc(
            filename="sangmata.py",
            command="Sangmata",
            description="Fetches old names and usernames of a user.",
            usage=".sg <username | user_id> | reply with .sg"
        )

    asyncio.create_task(register_handler_info())
