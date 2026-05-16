# calculator_inline.py
from telethon import events, Button
from shared.state import state, is_authorized
import time, math, asyncio


# ----------------------------
# Storage for sessions
# ----------------------------
calc_sessions = {}       # (initiator_id, chat_id) → expression
last_press_time = {}     # (initiator_id, chat_id) → timestamp
SET_HANDLER = True
# ----------------------------
# Init for bot_client
# ----------------------------
def init(bot_client, sync_callback=None):
    if not SET_HANDLER:
        return

    @bot_client.on(events.InlineQuery)
    async def inline_calc(event):
        query = event.text.strip().lower()
        if query != "calc":
            return

        user_id = event.sender_id

        # Authorization check
        if not is_authorized(user_id):
            await event.answer(
                [],
                switch_pm="Not authorized. Use .calc in chat.",
                switch_pm_param="start",
                cache_time=0,
            )
            return

        text = "**Calculator**\nUse the buttons below to calculate."
        buttons = _build_calc_buttons(user_id, 0)

        await event.answer(
            [
                event.builder.article(
                    title="Open Calculator",
                    description="Tap to open calculator",
                    text=text,
                    buttons=buttons,
                )
            ],
            cache_time=0,
        )

    @bot_client.on(events.CallbackQuery)
    async def callback_handler(event):
        data = event.data.decode()
        sender_id = event.sender_id

        # Expected format: "initiator_id:chat_id:action"
        try:
            initiator_id, chat_id, action = data.split(":", 2)
            initiator_id = int(initiator_id)
            chat_id = int(chat_id)
        except ValueError:
            return

        session_key = (initiator_id, chat_id)

        # Access control: only initiator or authorized users
        if sender_id != initiator_id and not is_authorized(sender_id):
            await event.answer("Not authorized.", alert=True)
            return

        # Anti-spam: 0.3s cooldown
        now = time.time()
        if now - last_press_time.get(session_key, 0) < 0.3:
            await event.answer("Slow down.", alert=False)
            return
        last_press_time[session_key] = now

        expr = calc_sessions.get(session_key, "")

        # Handle button actions
        if action == "C":
            expr = ""
        elif action == "⌫":
            expr = expr[:-1]
        elif action == "√":
            try:
                if expr:
                    val = eval(expr)
                    result = math.sqrt(val)
                    expr = f"√({expr})={result}"
                    calc_sessions[session_key] = str(result)
            except Exception:
                expr = "Error"
        elif action == "=":
            try:
                result = str(eval(expr))
                expr = f"{expr}={result}"
                calc_sessions[session_key] = result
            except Exception:
                expr = "Error"
        else:
            # Avoid duplicate operators
            if expr and expr[-1] in "+-*/.√" and action in "+-*/.√":
                expr = expr[:-1] + action
            else:
                if "=" in expr:
                    expr = ""
                expr += action

        calc_sessions[session_key] = expr

        # Edit safely
        await asyncio.sleep(0.05)
        buttons = _build_calc_buttons(initiator_id, chat_id)
        try:
            await event.edit(f"**Calculator**\n`{expr or '0'}`", buttons=buttons)
        except Exception:
            pass

# ----------------------------
# Build calculator buttons
# ----------------------------
def _build_calc_buttons(initiator_id, chat_id):
    def b(text, data):
        return Button.inline(text, f"{initiator_id}:{chat_id}:{data}")

    return [
        [b("7", "7"), b("8", "8"), b("9", "9"), b("÷", "/")],
        [b("4", "4"), b("5", "5"), b("6", "6"), b("×", "*")],
        [b("1", "1"), b("2", "2"), b("3", "3"), b("-", "-")],
        [b("0", "0"), b(".", "."), b("=", "="), b("+", "+")],
        [b("√", "√"), b("⌫", "⌫"), b("C", "C")],
      ]
