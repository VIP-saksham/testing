import os
import aiofiles
import aiohttp
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL as FAILED  # Fallback image

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

RES_W, RES_H = 1920, 1080  # Full HD

async def gen_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_full.png")
    if os.path.exists(cache_path):
        return cache_path

    # Fetch video details
    results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
    try:
        data = (await results.next()).get("result", [])[0]
        thumb_url = data["thumbnails"][-1]["url"]
    except:
        thumb_url = FAILED

    # Download thumbnail
    thumb_path = os.path.join(CACHE_DIR, f"{videoid}_raw.png")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
    except:
        return FAILED

    # Open and resize to full HD
    from PIL import Image
    thumb = Image.open(thumb_path).convert("RGBA")
    thumb = thumb.resize((RES_W, RES_H))
    thumb.save(cache_path, quality=95)

    try:
        os.remove(thumb_path)
    except:
        pass

    return cache_path
