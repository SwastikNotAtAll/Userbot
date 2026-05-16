import asyncio
import shlex
from telethon import events
from shared.state import state, register_handler_doc, maybe_warn_spammer, is_authorized

SET_HANDLER = True
# ----------------------------
# Helper: Split Long Output
# ----------------------------
def split_text(text, max_length=4096):
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]
# ----------------------------
# Main Init
# ----------------------------
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return

    @client.on(events.NewMessage(pattern=r"\.sh(?:@[\w_]+)?(?:\s+(.+))?"))
    async def handle_exec(event):

        if event.sender_id != state["owner_id"]:
            return

        command = event.pattern_match.group(1)

        if not command:
            return await event.reply("**Provide a shell command to execute.\nUsage:** `.sh <command>`")

        try:
            # Run command asynchronously
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
            except asyncio.TimeoutError:
                process.kill()
                return await event.reply("Execution timed out (60 seconds).")

            output = ""

            if stdout:
                output += stdout.decode().strip()

            if stderr:
                if output:
                    output += "\n\n"
                output += stderr.decode().strip()

            if not output:
                output = "Command executed successfully with no output."

            # Send in chunks
            for chunk in split_text(output):
                await event.reply(f"```\n{chunk}\n```")

        except Exception as e:
            await event.reply(f"`{e}`")

    handle_exec._from_userbot_reload = True

    async def register_handler_info():
        await register_handler_doc(
            filename="sh.py",
            command="Shell",
            description="Executes shell commands from the server.",
            usage=".sh <shell command>"
        )
    asyncio.create_task(register_handler_info())
