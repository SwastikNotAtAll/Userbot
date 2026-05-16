import asyncio
import random
from telethon import events
from shared.state import state, register_handler_doc

SET_HANDLER = True
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    OWNER_ID = state["owner_id"]
    owner_username = None  # will fetch later dynamically

    # --- Phrase Lists ---
    CLEAN_PHRASES = [
        "",
        "",
        "",
        "",
        "",
        "kuch bhi add krdo jo man kre",
    ]

    AGGRESSIVE_PHRASES = [
        "nikal mad*rch*d",
        "bhaag b*dk",
        "nikal lav**de",
        "dur ho bho*dike",
        "nikal ch*t*ye",
        "hat r*ndi ka 7vi aul*ad", 
        "4m*r jati ka pai*aish", 
        "bhaag mx",
    ]

    # --- State Storage (permanent memory) ---
    if "reply_raids" not in state:
        state["reply_raids"] = {}

    # --- Utility Function ---
    def pick_phrase(raid_type):
        phrases = CLEAN_PHRASES if raid_type == "replyraid" else AGGRESSIVE_PHRASES
        return random.choice(phrases)

    # --- Command: .replyraid ---
    @client.on(events.NewMessage(pattern=r"^\.replyraid(?:\s+(on|off))?$"))
    async def replyraid_handler(event):
        if event.sender_id != OWNER_ID:
            return
        if not event.is_reply:
            await event.delete()
            return

        reply = await event.get_reply_message()
        target_id = reply.sender_id
        if not target_id:
            await event.delete()
            return

        mode = event.pattern_match.group(1)
        if mode == "on":
            state["reply_raids"][str(target_id)] = {"type": "replyraid"}
        elif mode == "off":
            state["reply_raids"].pop(str(target_id), None)

        await event.delete()  # Silent trigger

    # --- Command: .areplyraid ---
    @client.on(events.NewMessage(pattern=r"^\.areplyraid(?:\s+(on|off))?$"))
    async def areplyraid_handler(event):
        if event.sender_id != OWNER_ID:
            return
        if not event.is_reply:
            await event.delete()
            return

        reply = await event.get_reply_message()
        target_id = reply.sender_id
        if not target_id:
            await event.delete()
            return

        mode = event.pattern_match.group(1)
        if mode == "on":
            state["reply_raids"][str(target_id)] = {"type": "areplyraid"}
        elif mode == "off":
            state["reply_raids"].pop(str(target_id), None)

        await event.delete()  # Silent trigger

    # --- Monitor incoming messages ---
    @client.on(events.NewMessage)
    async def monitor_raid(event):
        nonlocal owner_username

        if event.sender_id == OWNER_ID:
            return

        # Skip if not active target
        target_id = str(event.sender_id)
        if target_id not in state.get("reply_raids", {}):
            return

        raid_type = state["reply_raids"][target_id]["type"]

        # --- Detect mentions or replies ---
        # Reply to owner's message
        is_reply_to_owner = (
            event.is_reply and (await event.get_reply_message()).sender_id == OWNER_ID
        )

        # Fetch owner username if not cached
        if owner_username is None:
            try:
                me = await client.get_me()
                owner_username = me.username.lower() if me.username else None
            except Exception:
                owner_username = None

        # Mention check (true mention OR @username text)
        is_entity_mention = any(
            getattr(ent, "user_id", None) == OWNER_ID
            for ent in event.message.entities or []
        )

        is_text_mention = (
            owner_username
            and f"@{owner_username.lower()}" in event.raw_text.lower()
        )

        if not (is_reply_to_owner or is_entity_mention or is_text_mention):
            return

        # --- Trigger reply ---
        phrase = pick_phrase(raid_type)
        reply_msg = await event.reply(phrase)

        # Delete after 10 minutes
        await asyncio.sleep(300)
        try:
            await reply_msg.delete()
        except Exception:
            pass

    # --- Register handler doc ---
    replyraid_handler._from_userbot_reload = True
    areplyraid_handler._from_userbot_reload = True
    monitor_raid._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="raid.py",
            command="Raid",
            description="Automatically replies to target users who reply or mention you.",
            usage=".replyraid on/off (reply to target)\n.areplyraid on/off (reply to target)",
        )

    asyncio.create_task(register_handler_info())
