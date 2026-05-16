# For Cricket game bot of telegram #

import asyncio
import random
from datetime import datetime, time as dt_time, timedelta, timezone
from telethon import events
from shared.state import state, register_handler_doc

SET_HANDLER = True

def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    # --- Configurable Settings ---
    BOT_IDS = [7676704098]  # Default bot ID
    active_bot_ids = BOT_IDS.copy()  # Runtime editable bot IDs
    # Default bot username for /joingame
    active_bot_username = "@CricketPCGBot"
    YOUR_NAME = "𝘚ᴡᴀѕᴛɪᴋ 🍷"
    batting_droprates = {
        2: 0.2,
        3: 0.2,
        4: 0.2,
        5: 0.2,
        6: 0.2
    }
    bowling_droprates = {
        4: 0.15,
        3: 0.15,
        5: 0.2,
        6: 0.5
    }
    delay_range = (5, 8)
    max_age = 30
    # --- State ---
    autopilot_enabled = False
    last_batting_time = None
    last_warning_time = None
    last_bowling_time = None
    batting_responded = False
    bowling_responded = False
    joined_current_game = False
    join_blocked = False
    last_join_msg_time = None
    # --- TIME RANGE (IST) ---
    RESTRICT_START = dt_time(0, 30)
    RESTRICT_END = dt_time(8, 30)
    IST = timezone(timedelta(hours=5, minutes=30))

    def is_restricted_time():
        now_ist = datetime.now(IST).time()
        return RESTRICT_START <= now_ist <= RESTRICT_END

    def is_recent(message_time):
        now_utc = datetime.now(timezone.utc)
        delta = (now_utc - message_time).total_seconds()
        return 0 <= delta <= max_age

    def choose_with_droprates(dropdict):
        items = list(dropdict.keys())
        weights = list(dropdict.values())
        return random.choices(items, weights=weights, k=1)[0]

    # --- Batting ---
    async def handle_batting(event):
        nonlocal last_batting_time, batting_responded
        if batting_responded or not autopilot_enabled:
            return
        if not is_recent(event.date):
            return
        entities = getattr(event.message, "entities", None)
        if not entities:
            return
        for entity in entities:
            if hasattr(entity, "user_id") and entity.user_id == state["owner_id"]:
                last_batting_time = datetime.now(timezone.utc)
                delay = random.randint(*delay_range)
                await asyncio.sleep(delay)
                num = str(choose_with_droprates(batting_droprates))
                try:
                    await event.respond(num)
                    batting_responded = True
                except:
                    pass
                break

    # --- Warning ---
    async def handle_warning(event):
        nonlocal last_warning_time, last_batting_time, batting_responded
        if not autopilot_enabled:
            return
        if not is_recent(event.date):
            return
        last_warning_time = datetime.now(timezone.utc)
        if last_batting_time and not batting_responded:
            num = str(choose_with_droprates(batting_droprates))
            try:
                await event.respond(num)
                batting_responded = True
            except:
                pass

    # --- Bowling ---
    async def handle_bowling(event):
        nonlocal last_bowling_time, bowling_responded
        if bowling_responded or not autopilot_enabled:
            return
        if not is_recent(event.date):
            return
        text = event.raw_text or ""
        if "Send Your number:" in text or "OVER BALLS" in text:
            last_bowling_time = datetime.now(timezone.utc)
            delay = random.randint(*delay_range)
            await asyncio.sleep(delay)
            num = str(choose_with_droprates(bowling_droprates))
            try:
                await event.respond(num)
                bowling_responded = True
            except:
                pass

    # --- Auto Join ---
    async def handle_auto_join(event):
        nonlocal joined_current_game, join_blocked, last_join_msg_time

        if not autopilot_enabled or join_blocked:
            return
        if is_restricted_time():
            return
        if not is_recent(event.date):
            return

        last_join_msg_time = datetime.now(timezone.utc)
        delay = random.randint(8, 12)
        await asyncio.sleep(delay)

        try:
            command = "/joingame"
            if active_bot_username:
                command += active_bot_username
            await event.respond(command)
            joined_current_game = True
        except:
            pass

    # --- Toggle Command ---
    @client.on(events.NewMessage(pattern=r'^\.cricketmode'))
    async def autopilot_toggle(event):
        nonlocal autopilot_enabled
        if event.sender_id != state["owner_id"]:
            return
        args = event.raw_text.split()
        if len(args) == 1:
            status = "`Currently Activated.`" if autopilot_enabled else "`Currently Deactivated.`"
            await event.edit(status)
            await asyncio.sleep(3)
            try:
                await event.delete()
            except:
                pass
            return
        arg = args[1].lower()
        if arg in ["on", "off"]:
            autopilot_enabled = arg == "on"
            try:
                await event.delete()
            except:
                pass

    # --- Change Bot ID Command ---
    @client.on(events.NewMessage(pattern=r'^\.changebot (.+)$'))
    async def change_bot(event):
        nonlocal active_bot_ids, active_bot_username
        if event.sender_id != state["owner_id"]:
            return
        arg = event.pattern_match.group(1).strip()
        try:
            if arg.isdigit():
                new_id = int(arg)
            else:
                if arg.startswith("@"):
                    arg = arg[1:]
                entity = await client.get_entity(arg)
                new_id = entity.id
            bot_name = entity.first_name
            active_bot_ids = [new_id]

            # --- Update bot username dynamically ---
            active_bot_username = f"@{entity.username}" if hasattr(entity, "username") else None

            await event.reply(
                f'𝗕𝗼𝘁 𝗜𝗗 𝗖𝗵𝗮𝗻𝗴𝗲𝗱 𝗧𝗼 <a href="tg://user?id={new_id}">{bot_name}</a>',
                parse_mode="html"
            )
        except Exception as e:
            await event.reply("`Invalid username or ID.`")

    # --- Main Handler ---
    @client.on(events.NewMessage)
    async def autopilot_handler(event):
        nonlocal batting_responded, bowling_responded, joined_current_game, join_blocked

        try:
            text = event.raw_text or ""
            sender_id = event.sender_id

            # --- Batting ---
            if sender_id in active_bot_ids and "Now Batter:" in text and YOUR_NAME in text:
                batting_responded = False
                await handle_batting(event)
                return

            # --- Warning ---
            if sender_id in active_bot_ids and f"Warning: {YOUR_NAME}" in text:
                await handle_warning(event)
                return

            # --- Bowling ---
            if event.is_private and sender_id in active_bot_ids and ("Send Your number:" in text or "OVER BALLS" in text):
                bowling_responded = False
                await handle_bowling(event)
                return

            # --- Auto Join ---
            if sender_id in active_bot_ids:
                if "🎉 Game created! Join the game using /joingame" in text:
                    joined_current_game = False
                    join_blocked = False
                    await handle_auto_join(event)
                    return

                if f"🎉 {YOUR_NAME}, you've joined the game!" in text:
                    joined_current_game = True
                    return

                if f"🚫 {YOUR_NAME}, you're already active in these games:" in text:
                    join_blocked = True
                    return
        except:
            pass

    # --- Registration ---
    autopilot_handler._from_userbot_reload = True
    autopilot_toggle._from_userbot_reload = True
    change_bot._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="cricket.py",
            command="Cricket",
            description="Automated Number Sending in Cricket Matches During Batting/Bowling.",
            usage="kya pta."
        )
    asyncio.create_task(register_handler_info())
