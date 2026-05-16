import asyncio
import re
from telethon import events
from shared.state import state, register_handler_doc, is_authorized, maybe_warn_spammer

# The bot that provides time info
TIME_BOT_USERNAME = "calsibot"
SET_HANDLER = True

def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r'^\.when$'))
    async def when_handler(event):
        # Allow only owner or sudo users
        if not is_authorized(event.sender_id):
            await maybe_warn_spammer(event)
            return

        if not event.is_reply:
            await event.reply("Please reply to a message with `.when`.")
            return

        original_when_msg = event
        reply_msg = await event.get_reply_message()

        try:
            # Step 1: Resolve the bot entity
            time_bot = await client.get_entity(TIME_BOT_USERNAME)

            # Step 2: Forward the replied message to @calsibot
            fwd_msg = await client.forward_messages(time_bot, reply_msg)

            # Step 3: Send /when as a reply to that forwarded message
            await client.send_message(time_bot, "/when", reply_to=fwd_msg.id)

            # Step 4: Wait for @calsibot's response
            response = None

            async def response_handler(resp_event):
                nonlocal response
                if resp_event.sender_id == time_bot.id:
                    response = resp_event

            # Attach temporary listener
            client.add_event_handler(
                response_handler,
                events.NewMessage(from_users=time_bot.id, chats=time_bot.id)
            )

            # Wait up to 10 seconds for response
            for _ in range(20):
                if response:
                    break
                await asyncio.sleep(0.5)

            # Remove temporary listener
            client.remove_event_handler(response_handler)

            if not response:
                await original_when_msg.reply("Timeout while waiting for response.")
                return

            # Step 5: Extract the "That’s ..." phrase
            match = re.search(r"That'?s (.+?)\.", response.raw_text)
            if match:
                time_ago = match.group(1)
                await original_when_msg.reply(f"`It was sent {time_ago}`")
            else:
                await original_when_msg.reply("Couldn't parse time information from response.")

        except Exception as e:
            await original_when_msg.reply(f"Error: {str(e)}")

    when_handler._from_userbot_reload = True

    # ----------------------------
    # Async registration for cmds.py
    # ----------------------------
    async def register_handler_info():
        await register_handler_doc(
            filename="when.py",
            command="When",
            description="Fetches the sent time of a replied message.",
            usage=".when (reply to a message)"
        )

    # Schedule registration task
    asyncio.create_task(register_handler_info())
