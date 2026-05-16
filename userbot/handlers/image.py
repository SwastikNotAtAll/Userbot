import os
import aiohttp
from telethon import events
from shared.state import state, register_handler_doc, is_authorized, is_owner_or_super
from .error import safe_handler
import asyncio
from config import HUGGINGFACE_TOKEN

SET_HANDLER = True
# --- Model and API Endpoint ---
PRIMARY_MODEL = "black-forest-labs/FLUX.1-dev"
FALLBACK_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"

# --- Generate Image Function with fallback ---
async def generate_image(prompt: str):
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_TOKEN}",
        "accept": "image/png",
    }

    for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
        api_url = f"https://router.huggingface.co/hf-inference/models/{model}"
        payload = {"inputs": prompt}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        err_text = await response.text()
                        print(f"[{model}] Failed: {response.status} | {err_text}")
        except Exception as e:
            print(f"Error using {model}: {e}")

    raise Exception("`Failed to generate image.`")


# --- Init Function for Telethon Integration ---
def init(client, sync_callback=None):
    if not SET_HANDLER:
        return
    @client.on(events.NewMessage(pattern=r"^\.img(?: |$)(.*)"))
    @safe_handler("img.py", sync_callback)
    async def img_handler(event):
        if not is_owner_or_super(event.sender_id):
            return

        query = event.pattern_match.group(1).strip()
        if not query:
            await event.reply("`Please provide a prompt to generate image.`\nExample: `.img cyberpunk city at night`")
            return

        msg = await event.reply("`Generating image... please wait.`")

        try:
            image_data = await generate_image(query)
            os.makedirs("./temp", exist_ok=True)
            temp_file = "./temp/generated_image.png"
            with open(temp_file, "wb") as f:
                f.write(image_data)

            await event.reply(file=temp_file, message=f"𝗣𝗿𝗼𝗺𝗽𝘁: {query}")
            await msg.delete()
            os.remove(temp_file)

        except Exception as e:
            await msg.edit(f"Failed to generate image.\nError: {e}")

    async def register_handler_info():
        await register_handler_doc(
            filename="img.py",
            command="Img",
            description="Generates AI images from text prompts.",
            usage=".img <prompt>"
        )
    asyncio.create_task(register_handler_info())
