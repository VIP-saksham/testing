import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL as FAILED

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

MAX_WIDTH = 1100   # Max width for title text
TITLE_Y = 550       # Vertical position of title
SHADOW_OFFSET = 4   # Shadow depth


def trim_to_width(text, font, max_w):
    """Trim long text with ellipsis based on font.getlength()."""
    ellipsis = "…"
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis


async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_simple.png")
    if os.path.exists(cache_path):
        return cache_path

    # Fetch YouTube video details
    results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
    try:
        data = (await results.next()).get("result", [])[0]
        title = re.sub(r"\W+", " ", data.get("title", "Unsupported Title")).strip()
        title = title.title()
        thumb_url = data.get("thumbnails", [{}])[0].get("url", FAILED)
    except Exception:
        title, thumb_url = "Unsupported Title", FAILED

    # Download thumbnail
    thumb_path = os.path.join(CACHE_DIR, f"thumb_{videoid}.png")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
    except Exception:
        return FAILED

    # Base full-screen image
    base = Image.open(thumb_path).convert("RGBA").resize((1280, 720))

    # Slight dark blur background for clarity
    bg = ImageEnhance.Brightness(base.filter(ImageFilter.BoxBlur(3))).enhance(0.85)

    draw = ImageDraw.Draw(bg)

    # Fonts
    try:
        title_font = ImageFont.truetype("SONALI_MUSIC/assets/font.ttf", 50)
    except:
        title_font = ImageFont.load_default()

    # Trim title to width
    final_title = trim_to_width(title, title_font, MAX_WIDTH)

    # Calculate centered text position using textbbox
    bbox = draw.textbbox((0, 0), final_title, font=title_font)
    text_w = bbox[2] - bbox[0]
    x = (1280 - text_w) // 2

    # 1) SHADOW (black, offset)
    draw.text((x + SHADOW_OFFSET, TITLE_Y + SHADOW_OFFSET),
              final_title, font=title_font, fill="black")

    # 2) MAIN TITLE (white or yellow)
    draw.text((x, TITLE_Y), final_title, font=title_font, fill="white")

    # Add small branding (optional)
    try:
        brand_font = ImageFont.truetype("SONALI_MUSIC/assets/font.ttf", 28)
    except:
        brand_font = ImageFont.load_default()

    brand = "DREAM BOTS"
    b_w, b_h = draw.textbbox((0, 0), brand, font=brand_font)[2:]
    draw.text((1280 - b_w - 25, 25), brand, fill="yellow", font=brand_font)

    # Save output
    bg.save(cache_path)

    try:
        os.remove(thumb_path)
    except:
        pass

    return cache_path

