from telethon import events, Button
from shared.state import state, is_authorized
import time, asyncio


# ----------------------------
# Session & anti-spam trackers
# ----------------------------
last_click_time = {}  # (initiator_id, chat_id) → timestamp
SET_HANDLER = True

# ----------------------------
# Init
# ----------------------------
def init(bot_client, sync_callback=None):
    if not SET_HANDLER:
        return

    # Inline query trigger (isolated)
    @bot_client.on(events.InlineQuery(pattern="^help_menu$"))
    async def inline_help(event):
        user_id = event.sender_id

        # Authorization check
        if not is_authorized(user_id):
            await event.answer(
                [],
                switch_pm="Unauthorized. Use .help in chat.",
                switch_pm_param="start",
                cache_time=0,
            )
            return

        handler_docs = state.get("handler_docs", {})
        if not handler_docs:
            await event.answer(
                [
                    event.builder.article(
                        title="No Commands Found",
                        description="No userbot commands registered yet.",
                        text="**No commands registered.**",
                    )
                ],
                cache_time=0,
            )
            return

        # Build first page
        items = list(handler_docs.items())
        page = 0
        buttons = _build_page_buttons(user_id, event.chat_id or 0, items, page, 6)
        total_cmds = len(items)
        text = f"**Userbot Help Menu**\n\nTap a command to view details.\n_Total commands: {total_cmds}_"

        await event.answer(
            [
                event.builder.article(
                    title="Userbot Help",
                    description="Tap to view available commands",
                    text=text,
                    buttons=buttons,
                )
            ],
            cache_time=0,
        )

    # ----------------------------
    # Callback handler (only for help)
    # ----------------------------
    @bot_client.on(events.CallbackQuery(pattern=r"^help:\d+:\d+:(?:page_|handler_)"))
    async def callback_handler(event):
        data = event.data.decode()
        try:
            _, initiator_id, chat_id, action = data.split(":", 3)
            initiator_id = int(initiator_id)
            chat_id = int(chat_id)
        except ValueError:
            return

        sender_id = event.sender_id

        # Only initiator or authorized users can interact
        if sender_id != initiator_id and not is_authorized(sender_id):
            await event.answer("Not authorized.", alert=True)
            return

        # Anti-spam: 0.5s cooldown
        now = time.time()
        key = (initiator_id, chat_id)
        if now - last_click_time.get(key, 0) < 0.5:
            await event.answer("Slow down.", alert=False)
            return
        last_click_time[key] = now

        handler_docs = state.get("handler_docs", {})
        items = list(handler_docs.items())

        # Pagination
        if action.startswith("page_"):
            try:
                page = int(action.split("_")[1])
            except Exception:
                return

            total_cmds = len(items)
            text = f"**Userbot Help Menu**\n\nTap a command to view details.\n_Total commands: {total_cmds}_"
            buttons = _build_page_buttons(initiator_id, chat_id, items, page, 6)
            await asyncio.sleep(0.05)
            try:
                await event.edit(text, buttons=buttons)
            except Exception:
                pass
            return

        # Show command details
        if action.startswith("handler_"):
            filename = action.split("_", 1)[1]
            info = handler_docs.get(filename)
            if not info:
                await event.answer("Command not found.", alert=False)
                return

            # Find page it belongs to
            page = 0
            for idx, (fn, _) in enumerate(items):
                if fn == filename:
                    page = idx // 6
                    break

            text = (
                f"**Command:** `{info.get('command', 'N/A')}`\n\n"
                f"**Description:** {info.get('description', 'N/A')}\n\n"
                f"**Usage:** `{info.get('usage', 'N/A')}`"
            )
            buttons = [[Button.inline("Back", f"help:{initiator_id}:{chat_id}:page_{page}")]]
            await asyncio.sleep(0.05)
            try:
                await event.edit(text, buttons=buttons)
            except Exception:
                pass
            return


# ----------------------------
# Helper: Build pagination
# ----------------------------
def _build_page_buttons(initiator_id, chat_id, handlers_list, page, per_page):
    total_pages = max(1, (len(handlers_list) - 1) // per_page + 1)
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    end = start + per_page
    visible = handlers_list[start:end]

    buttons = []
    for filename, info in visible:
        label = info.get("command", "Unknown")
        buttons.append(
            [Button.inline(label, f"help:{initiator_id}:{chat_id}:handler_{filename}")]
        )

    # Navigation
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(Button.inline("←", f"help:{initiator_id}:{chat_id}:page_{page-1}"))
        nav.append(Button.inline(f"{page+1}/{total_pages}", "noop"))
        if page < total_pages - 1:
            nav.append(Button.inline("→", f"help:{initiator_id}:{chat_id}:page_{page+1}"))
        buttons.append(nav)

    return buttons
