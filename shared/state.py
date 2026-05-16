import json
import time
import os
from config import OWNER_ID

BOT_DM_ID = OWNER_ID
SPAM_MAX_CMDS = 16
SPAM_WINDOW = 40
SPAM_BLOCK_TIME = 300 # 5 minutes

# ---------------- State ----------------
state = {
    "owner_id": OWNER_ID,
    "sudo_users": [],
    "super_sudo_users": [],
    "handlers": {}
}

bot_start_time = time.time()
_sync_callbacks = []
_last_json_msg_id = None
_spam_tracker = {}


# ---------------- Register callbacks ----------------
def register_sync_callback(cb):
    """Register a function to call whenever state changes."""
    _sync_callbacks.append(cb)


async def trigger_sync():
    for cb in _sync_callbacks:
        await cb()

#--------------Clean stale handlers---------#
def clean_stale_handlers():
    """
    Removes handler entries from state["handlers"]
    that no longer exist in the handlers directory.
    Logs removed stale handlers.
    """
    handlers_dir = "userbot/handlers"  # <-- change path if different

    if not os.path.isdir(handlers_dir):
        print("[STATE] Handlers directory not found.")
        return

    existing_files = set(os.listdir(handlers_dir))
    current_handlers = state.get("handlers", {})

    cleaned_handlers = {}
    removed = []

    for name, status in current_handlers.items():
        if name in existing_files:
            cleaned_handlers[name] = status
        else:
            removed.append(name)

    if removed:
        for r in removed:
            print(f"[STATE] Removed stale handler: {r}")
    else:
        print("[STATE] No stale handlers found.")

    state["handlers"] = cleaned_handlers
# ---------------- Serialization ----------------
def serialize_state() -> str:
    return json.dumps(state, indent=4)


def load_state_from_json(json_str: str):
    """
    Load new state from JSON without replacing the 'state' object reference.
    This keeps references in other modules (like handlers) intact.
    """
    try:
        new_data = json.loads(json_str)
        if not isinstance(new_data, dict):
            print("[STATE] Invalid JSON data ignored.")
            return

        # Clear and update existing state dict
        state.clear()
        state.update(new_data)
        print(f"[STATE] Loaded from JSON (Sudo: {len(state.get('sudo_users', []))}, Super Sudo: {len(state.get('super_sudo_users', []))}) ✅")
    except Exception as e:
        print(f"[STATE] Failed to load JSON: {e}")


# ---------------- Authorization ----------#
def is_authorized(uid: int) -> bool:
    # Owner always allowed
    if uid == state["owner_id"]:
        return True

    # Super sudo → full bypass (no spam limits)
    if uid in state.get("super_sudo_users", []):
        return True

    # Normal sudo required
    if uid not in state.get("sudo_users", []):
        return False

    now = time.time()
    user = _spam_tracker.setdefault(uid, {
        "count": 0,
        "window_start": now,
        "blocked_until": 0,
        "warned": False
    })

    # Blocked?
    if user["blocked_until"] > now:
        return False

    # Reset window
    if now - user["window_start"] > SPAM_WINDOW:
        user["count"] = 0
        user["window_start"] = now
        user["warned"] = False

    user["count"] += 1

    # Spam detected
    if user["count"] > SPAM_MAX_CMDS:
        user["blocked_until"] = now + SPAM_BLOCK_TIME
        user["warned"] = False
        return False

    return True
#------------------#
async def maybe_warn_spammer(event):
    uid = event.sender_id
    user = _spam_tracker.get(uid)

    if not user:
        return

    if user["blocked_until"] > time.time() and not user["warned"]:
        user["warned"] = True
        try:
            await event.reply("`Stop spamming baka! Ignoring you for 5 mins. `")
        except Exception:
            pass
#---------------super#
def is_owner_or_super(uid: int) -> bool:
    """Owner + Super Sudo access (no spam restriction)."""
    if uid == state["owner_id"]:
        return True

    if uid in state.get("super_sudo_users", []):
        return True

    return False
#---------------------------------------------------#
def mark_error(handler_name: str):
    state["handlers"][handler_name] = "error"

#----------------------handlers--------------------#
async def register_handler_doc(filename: str, command: str, description: str, usage: str):
    """Registers handler info for .cmds menu dynamically."""
    if "handler_docs" not in state:
        state["handler_docs"] = {}

    state["handler_docs"][filename] = {
        "command": command,
        "description": description,
        "usage": usage,
    }


# ---------------- JSON Sync ----------------
async def sync_state_to_user_dm(client):
    """Send latest state.json to userbot DM."""
    global _last_json_msg_id

    with open("state.json", "w") as f:
        persistent_state = {k: v for k, v in state.items() if k not in ("uptime_start", "handler_docs")}
        json.dump(persistent_state, f, indent=4)

    try:
        if _last_json_msg_id:
            await client.delete_messages(BOT_DM_ID, _last_json_msg_id)
    except Exception:
        pass

    try:
        sent = await client.send_file(
            BOT_DM_ID,
            "state.json",
            caption="`Updated state.json`",
            force_document=True
        )
        _last_json_msg_id = sent.id
        print("[STATE] Synced to userbot DM ✅")
    except Exception as e:
        print(f"[STATE] Sync failed: {e}")


async def restore_state_from_user_dm(client):
    """Fetch latest state.json from userbot DM and load it in-place."""
    global _last_json_msg_id
    print("[STATE] Checking for remote backup in userbot DM...")

    try:
        async for msg in client.iter_messages(BOT_DM_ID, limit=10):
            if msg.file and msg.file.name == "state.json":
                file_path = await client.download_media(msg, "state_remote.json")
                with open(file_path, "r") as f:
                    json_str = f.read()
                    load_state_from_json(json_str)
                clean_stale_handlers()
                _last_json_msg_id = msg.id
                print("[STATE] State restored successfully ✅")
                return
        print("[STATE] No remote backup found in userbot DM.")
    except Exception as e:
        print(f"[STATE] Restore failed: {e}")
