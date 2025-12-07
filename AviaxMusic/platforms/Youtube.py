import asyncio
import os
import re
import json
from typing import Union
import requests
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from AviaxMusic.utils.database import is_on_off
from AviaxMusic import app
from AviaxMusic.utils.formatters import time_to_seconds
import random
import logging
import aiohttp
from AviaxMusic import LOGGER
from urllib.parse import urlparse

# ---------------- Configuration ----------------
UPLOAD_CHANNEL = "@NakshuMuiscDB"
CACHE_FILE = "AviaxMusic/yt_cache.json"
YOUR_API_URL = None
DOWNLOAD_DIR = "downloads"
COOKIES_DIR = "AviaxMusic/cookies"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CACHE_FILE) or ".", exist_ok=True)


# ---------------- Cookies ----------------
def cookie_txt_file():
    cookie_dir = COOKIES_DIR
    if not os.path.exists(cookie_dir):
        return None
    files = [f for f in os.listdir(cookie_dir) if f.endswith(".txt")]
    if not files:
        return None
    return os.path.join(cookie_dir, random.choice(files))


# ---------------- Load API URL ----------------
async def load_api_url():
    global YOUR_API_URL
    logger = LOGGER("AviaxMusic/platforms/Youtube.py")

    env = os.getenv("YOUR_API_URL") or os.getenv("MUSIC_API_URL")
    if env:
        YOUR_API_URL = env.strip()
        return YOUR_API_URL

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pastebin.com/raw/rLsBhAQa") as r:
                if r.status == 200:
                    YOUR_API_URL = (await r.text()).strip()
                    return YOUR_API_URL
    except:
        pass

    YOUR_API_URL = os.getenv("YOUR_API_URL_FALLBACK", "https://ytdl-api.fly.dev")
    return YOUR_API_URL


try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except:
    pass


# ---------------- Cache ----------------
def load_cache():
    try:
        if os.path.exists(CACHE_FILE):
            return json.load(open(CACHE_FILE))
    except:
        pass
    return {}


def save_cache(cache):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except:
        pass


# ---------------- Telegram fetch ----------------
async def upload_to_channel_in_background(path, video_id, ftype):
    LOGGER("AviaxMusic").info(f"[UPLOAD] Background upload: {path}")


async def get_telegram_file(tg_link, video_id, ftype):
    logger = LOGGER("AviaxMusic/Youtube")

    ext = ".webm" if ftype == "audio" else ".mkv"
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}{ext}")

    if os.path.exists(file_path):
        return file_path

    parsed = urlparse(tg_link)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        return None

    channel = parts[0]
    try:
        msg_id = int(parts[-1])
    except:
        return None

    try:
        msg = await app.get_messages(channel, msg_id)
    except:
        try:
            if parts[0] == "c":
                msg = await app.get_messages(int(parts[1]), msg_id)
            else:
                return None
        except:
            return None

    media = msg.audio or msg.video or msg.document
    if not media:
        return None

    try:
        await app.download_media(msg, file_path)
        return file_path
    except:
        return None


# ---------------- Audio ----------------
async def download_song(link):
    global YOUR_API_URL
    logger = LOGGER("AviaxMusic/Audio")

    if not YOUR_API_URL:
        await load_api_url()

    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link

    cache = load_cache()
    if video_id in cache and cache[video_id].get("audio"):
        tg = cache[video_id]["audio"]
        loc = await get_telegram_file(tg, video_id, "audio")
        if loc:
            return loc

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.webm")
    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as s:
            params = {"url": video_id, "type": "audio"}
            async with s.get(f"{YOUR_API_URL}/download", params=params) as r:
                if r.status != 200:
                    return None
                data = await r.json()

        if data.get("link") and "t.me" in data["link"]:
            loc = await get_telegram_file(data["link"], video_id, "audio")
            if loc:
                cache.setdefault(video_id, {})["audio"] = data["link"]
                save_cache(cache)
                return loc

        if data.get("status") == "success" and data.get("stream_url"):
            async with aiohttp.ClientSession() as s:
                async with s.get(data["stream_url"]) as f:
                    with open(file_path, "wb") as w:
                        async for c in f.content.iter_chunked(16384):
                            w.write(c)

            return file_path

        return None

    except Exception as e:
        logger.error(str(e))
        return None


# ---------------- Video ----------------
async def download_video(link):
    global YOUR_API_URL
    logger = LOGGER("AviaxMusic/Video")

    if not YOUR_API_URL:
        await load_api_url()

    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link

    cache = load_cache()
    if video_id in cache and cache[video_id].get("video"):
        tg = cache[video_id]["video"]
        loc = await get_telegram_file(tg, video_id, "video")
        if loc:
            return loc

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mkv")
    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as s:
            params = {"url": video_id, "type": "video"}
            async with s.get(f"{YOUR_API_URL}/download", params=params) as r:
                if r.status != 200:
                    return None
                data = await r.json()

        if data.get("link") and "t.me" in data["link"]:
            loc = await get_telegram_file(data["link"], video_id, "video")
            if loc:
                cache.setdefault(video_id, {})["video"] = data["link"]
                save_cache(cache)
                return loc

        if data.get("status") == "success" and data.get("stream_url"):
            async with aiohttp.ClientSession() as s:
                async with s.get(data["stream_url"]) as f:
                    with open(file_path, "wb") as w:
                        async for c in f.content.iter_chunked(16384):
                            w.write(c)

            return file_path

        return None

    except Exception as e:
        logger.error(str(e))
        return None


# ---------------- yt-dlp size ----------------
async def check_file_size(link):
    async def get_info(link):
        cookie = cookie_txt_file()
        if not cookie:
            return None

        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "--cookies", cookie, "-J", link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        out, err = await proc.communicate()
        if proc.returncode != 0:
            return None
        return json.loads(out.decode())

    info = await get_info(link)
    if not info:
        return None

    size = 0
    for f in info.get("formats", []):
        if f.get("filesize"):
            size += f["filesize"]
    return size


# ---------------- Command helper ----------------
async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    return out.decode() if out else err.decode()


# ---------------- Main YouTubeAPI class ----------------
class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"

    async def exists(self, link, videoid=False):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message: Message):
        msgs = [message]
        if message.reply_to_message:
            msgs.append(message.reply_to_message)

        for m in msgs:
            if getattr(m, "entities", None):
                for e in m.entities:
                    if e.type == MessageEntityType.URL:
                        t = m.text or m.caption or ""
                        return t[e.offset:e.offset + e.length]

            if getattr(m, "caption_entities", None):
                for e in m.caption_entities:
                    if e.type == MessageEntityType.TEXT_LINK:
                        return e.url

        txt = (message.text or message.caption or "").strip()
        if not txt:
            return None

        rg = re.search(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/\S+", txt)
        if rg:
            return rg.group(0)

        if len(txt) in (11, 12):
            return txt

        return None

    async def details(self, link, videoid=False):
        if videoid:
            link = self.base + link

        if "&" in link:
            link = link.split("&")[0]

        rs = VideosSearch(link, limit=1)
        res = (await rs.next())["result"][0]

        title = res["title"]
        duration = res["duration"]
        seconds = int(time_to_seconds(duration)) if duration else 0
        thumb = res["thumbnails"][0]["url"].split("?")[0]
        vid = res["id"]

        return title, duration, seconds, thumb, vid

    async def title(self, link, videoid=False):
        return (await self.details(link, videoid))[0]

    async def duration(self, link, videoid=False):
        return (await self.details(link, videoid))[1]

    async def thumbnail(self, link, videoid=False):
        return (await self.details(link, videoid))[3]

    async def video(self, link, videoid=False):
        if videoid:
            link = self.base + link
        try:
            f = await download_video(link)
            return (1, f) if f else (0, "Video download failed")
        except Exception as e:
            return (0, str(e))

    async def playlist(self, link, limit, user_id, videoid=False):
        if videoid:
            link = "https://youtube.com/playlist?list=" + link

        cookie = cookie_txt_file()
        if not cookie:
            return []

        pl = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --cookies {cookie} --playlist-end {limit} {link}"
        )
        return [x for x in pl.split("\n") if x]

    async def track(self, link, videoid=False):
        if videoid:
            link = self.base + link
        try:
            f = await download_song(link)
            return (1, f) if f else (0, "Audio download failed")
        except Exception as e:
            return (0, str(e))
