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
from AnonXMusic.utils.database import is_on_off
from AnonXMusic import app
from AnonXMusic.utils.formatters import time_to_seconds
import random
import logging
import aiohttp
from AnonXMusic import LOGGER
from urllib.parse import urlparse

# ---------------- Configuration ----------------
UPLOAD_CHANNEL = "@NakshuMuiscDB"           # change if needed
CACHE_FILE = "AnonXMusic/yt_cache.json"
YOUR_API_URL = None
DOWNLOAD_DIR = "downloads"
COOKIES_DIR = "AnonXMusic/cookies"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CACHE_FILE) or ".", exist_ok=True)


def cookie_txt_file():
    """Return a random .txt cookie file from COOKIES_DIR or None."""
    cookie_dir = COOKIES_DIR
    if not os.path.exists(cookie_dir):
        return None
    cookies_files = [f for f in os.listdir(cookie_dir) if f.endswith(".txt")]
    if not cookies_files:
        return None
    cookie_file = os.path.join(cookie_dir, random.choice(cookies_files))
    return cookie_file


async def load_api_url():
    """
    Load API URL from environment (best-effort) or fallback to pastebin then hardcoded fallback.
    Returns the selected YOUR_API_URL string.
    """
    global YOUR_API_URL
    logger = LOGGER("AnonXMusic/platforms/Youtube.py")

    # environment variables (preferred)
    env_val = os.getenv("YOUR_API_URL") or os.getenv("MUSIC_API_URL")
    if env_val:
        YOUR_API_URL = env_val.strip()
        logger.info("API URL loaded from environment")
        return YOUR_API_URL

    # try pastebin fallback
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pastebin.com/raw/rLsBhAQa") as response:
                if response.status == 200:
                    content = await response.text()
                    YOUR_API_URL = content.strip()
                    logger.info(f"API URL loaded successfully: {YOUR_API_URL}")
                    return YOUR_API_URL
    except Exception as e:
        logger.debug(f"Error trying pastebin for API URL: {e}")

    # final fallback
    YOUR_API_URL = os.getenv("YOUR_API_URL_FALLBACK", "https://ytdl-api.fly.dev")
    logger.warning(f"Using fallback API URL: {YOUR_API_URL}")
    return YOUR_API_URL


# try to load API URL at import (best-effort, non-blocking if possible)
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except RuntimeError:
    # no running loop; fine to skip
    pass


# ---------------- Cache helpers ----------------
def load_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        LOGGER("AnonXMusic/platforms/Youtube.py").warning(f"Failed loading cache: {e}")
    return {}


def save_cache(cache: dict):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE) or ".", exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        LOGGER("AnonXMusic/platforms/Youtube.py").error(f"Failed saving cache: {e}")


# ---------------- Telegram fetch ----------------
async def upload_to_channel_in_background(file_path: str, video_id: str, file_type: str):
    """
    Placeholder uploader — replace with your actual channel upload logic.
    This runs in background to push downloaded files to UPLOAD_CHANNEL.
    """
    logger = LOGGER("AnonXMusic/platforms/Youtube.py")
    try:
        # If you have an async upload function, call it here. For now we log only.
        logger.info(f"(background) would upload {file_type} for {video_id}: {file_path}")
    except Exception as e:
        logger.error(f"Background upload failed: {e}")


async def get_telegram_file(telegram_link: str, video_id: str,
fi
l
e
le_type: str) -> Union[str, None]:
    """
    Download media from a Telegram link (https://t.me/channel/message or https://t.me/c/xxxx/123).
    Returns local path or None.
    """
    logger = LOGGER("AnonXMusic/platforms/Youtube.py")
    try:
        extension = ".webm" if file_type == "audio" else ".mkv"
        file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}{extension}")

        # Already present locally
        if os.path.exists(file_path):
            logger.info(f"📂 [LOCAL] File exists: {file_path}")
            return file_path

        # Parse link
        parsed = urlparse(telegram_link)
        parts = parsed.path.strip("/").split("/")
        if len(parts) < 2:
            logger.error(f"❌ Invalid Telegram link format: {telegram_link}")
            return None

        # channel may be like 'channel' or 'c/12345' style; message id usually last part
        channel_name = parts[0]
        message_part = parts[-1]
        try:
            message_id = int(message_part)
        except Exception:
            logger.error(f"❌ Cannot parse message id from link: {telegram_link}")
            return None

        # Fetch message via pyrogram client
        try:
            msg = await app.get_messages(chat_id=channel_name, message_ids=message_id)
        except Exception as e:
            logger.error(f"❌ Failed to fetch message {message_id} from {channel_name}: {e}")
            # sometimes t.me/c/<chat_id>/<msg> uses numeric chat id instead of username
            try:
                # try with numeric chat id if available in path (e.g., c/12345)
                if parts[0] == 'c' and len(parts) >= 3:
                    numeric_chat = int(parts[1])
                    msg = await app.get_messages(chat_id=numeric_chat, message_ids=message_id)
                else:
                    return None
            except Exception as e2:
                logger.error(f"Fallback fetch failed: {e2}")
                return None

        if not msg:
            logger.error(f"❌ Message not found: {telegram_link}")
            return None

        # determine media
        media = getattr(msg, 'audio', None) or getattr(msg, 'video', None) or getattr(msg, 'document', None)
        if not media:
            logger.error("❌ No media found in Telegram message")
            return None

        # download media to file_path (pyrogram provides download methods)
        try:
            await app.download_media(msg, file_path)
            logger.info(f"📥 Downloaded from Telegram: {file_path}")
            # spawn uploader in background
            asyncio.create_task(upload_to_channel_in_background(file_path, video_id, file_type))
            return file_path
        except Exception as e:
            logger.error(f"❌ Telegram download failed: {e}")
            return None

    except Exception as e:
        logger.error(f"[AUDIO] Exception: {e}")
        return None


# ---------------- Core: download_audio (used by original code) ----------------
async def download_song(link: str) -> Union[str, None]:
    """
    Helper to download audio via YOUR_API_URL endpoint; mirrors original pattern used in project.
    """
    global YOUR_API_URL
    logger = LOGGER("AnonXMusic/platforms/Youtube.py")

    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            logger.error("API URL not available")
            return None

    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    cache = load_cache()

    # try cache
    if video_id in cache and cache[video_id].get("audio"):
        tg_link = cache[video_id]["audio"]
        logger.info(f"✅ [CACHE] Found audio link: {tg_link}")
        local = await get_telegram_file(tg_link, video_id, "audio")
        if local:
            return local
        else:
            logger.warning("⚠️ Cache audio link failed; will redownload")

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.webm")
    if os.path.exists(file_path):
        logger.info(f"🎧 [LOCAL] Local file exists: {file_path}")
        return file_path

    # contact
 API
try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "audio"}
            async with session.get(f"{YOUR_API_URL}/download", params=params, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status != 200:
                    logger.error(f"[AUDIO] API error: {response.status}")
                    return None
                data = await response.json()

            # if API returned t.me link directly
            if data.get("link") and "t.me" in str(data.get("link")):
                tg_link = data["link"]
                logger.info(f"🔗 [AUDIO] API provided Telegram link: {tg_link}")
                local = await get_telegram_file(tg_link, video_id, "audio")
                if local:
                    cache.setdefault(video_id, {})["audio"] = tg_link
                    save_cache(cache)
                    return local
                else:
                    logger.warning("⚠️ Failed fetching API-provided Telegram link")

            # if API returned stream_url
            if data.get("status") == "success" and data.get("stream_url"):
                stream_url = data["stream_url"]
                logger.info(f"[AUDIO] Stream URL obtained for {video_id}")

                async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=300)) as file_response:
                    if file_response.status != 200:
                        logger.error(f"[AUDIO] Stream download failed: {file_response.status}")
                        return None
                    with open(file_path, "wb") as f:
                        async for chunk in file_response.content.iter_chunked(16384):
                            f.write(chunk)

                logger.info(f"🎉 [AUDIO] Downloaded: {file_path}")

                # spawn uploader in background
                asyncio.create_task(upload_to_channel_in_background(file_path, video_id, "audio"))

                # return path for immediate playback
                return file_path

            logger.error(f"[AUDIO] Invalid API response: {data}")
            return None

    except asyncio.TimeoutError:
        logger.error(f"[AUDIO] Timeout for {video_id}")
        return None
    except Exception as e:
        logger.error(f"[AUDIO] Exception: {e}")
        return None


# ---------------- Core: download_video ----------------
async def download_video(link: str) -> Union[str, None]:
    """
    Video workflow identical to audio but for video (.mkv)
    """
    global YOUR_API_URL
    logger = LOGGER("AnonXMusic/platforms/Youtube.py")

    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            logger.error("API URL not available")
            return None

    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    logger.info(f"🎥 [VIDEO] Requested: {video_id}")

    if not video_id or len(video_id) < 3:
        logger.error("Invalid video id")
        return None

    cache = load_cache()
    if video_id in cache and cache[video_id].get("video"):
        tg_link = cache[video_id]["video"]
        logger.info(f"✅ [CACHE] Found video link: {tg_link}")
        local = await get_telegram_file(tg_link, video_id, "video")
        if local:
            return local
        else:
            logger.warning("⚠️ Cache video link failed; will redownload")

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mkv")
    if os.path.exists(file_path):
        logger.info(f"🎥 [LOCAL] Local file exists: {file_path}")
        return file_path

    # contact API
    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "video"}
            async with session.get(f"{YOUR_API_URL}/download", params=params, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status != 200:
                    logger.error(f"[VIDEO] API error: {response.status}")
                    return None
                data = await response.json()

            if data.get("link") and
"t.me
me" in str(data.get("link")):
                tg_link = data["link"]
                logger.info(f"🔗 [VIDEO] API provided Telegram link: {tg_link}")
                local = await get_telegram_file(tg_link, video_id, "video")
                if local:
                    cache.setdefault(video_id, {})["video"] = tg_link
                    save_cache(cache)
                    return local
                else:
                    logger.warning("⚠️ Failed fetching API-provided Telegram link")

            if data.get("status") == "success" and data.get("stream_url"):
                stream_url = data["stream_url"]
                logger.info(f"[VIDEO] Stream URL obtained for {video_id}")

                async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=600)) as file_response:
                    if file_response.status != 200:
                        logger.error(f"[VIDEO] Stream download failed: {file_response.status}")
                        return None
                    with open(file_path, "wb") as f:
                        async for chunk in file_response.content.iter_chunked(16384):
                            f.write(chunk)

                logger.info(f"🎉 [VIDEO] Downloaded: {file_path}")

                # spawn uploader in background
                asyncio.create_task(upload_to_channel_in_background(file_path, video_id, "video"))

                return file_path

            logger.error(f"[VIDEO] Invalid API response: {data}")
            return None

    except asyncio.TimeoutError:
        logger.error(f"[VIDEO] Timeout for {video_id}")
        return None
    except Exception as e:
        logger.error(f"[VIDEO] Exception: {e}")
        return None


# ---------------- yt-dlp formats helper ----------------
async def check_file_size(link):
    async def get_format_info(link):
        cookie_file = cookie_txt_file()
        if not cookie_file:
            print("No cookies found. Cannot check file size.")
            return None

        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies",
            cookie_file,
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f'Error:\n{stderr.decode()}')
            return None
        return json.loads(stdout.decode())

    def parse_size(formats):
        total_size = 0
        for fmt in formats:
            if 'filesize' in fmt and fmt['filesize']:
                total_size += fmt['filesize']
        return total_size

    info = await get_format_info(link)
    if info is None:
        return None

    formats = info.get('formats', [])
    if not formats:
        print("No formats found.")
        return None

    total_size = parse_size(formats)
    return total_size


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


# ---------------- YouTubeAPI compatibility class ----------------
class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_mes
sage:
messages.append(message_1.reply_to_message)
        for message in messages:
            if getattr(message, "entities", None):
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption or ""
                        return text[entity.offset: entity.offset + entity.length]
            if getattr(message, "caption_entities", None):
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        # fallback: regex search
        text = message_1.text or message_1.caption or ""
        if not text:
            return None
        match = re.search(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/[^\s]+", text)
        if match:
            return match.group(0)
        # maybe it's just an id
        txt = text.strip().split()[0]
        if len(txt) in (11, 12):
            return txt
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            else:
                return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return []
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_file} --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = [key for key in playlist.split("\n") if key]
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return [], link
        ytdl_opts = {"quiet": True, "cookiefile": cookie_file}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    if "dash" not in str(format["format"]).lower():
                        formats_available.append(
                            {
                                "format": format["format"],
                                "filesize": format.get("filesize"),
                                "format_id": format["format_id"],
                                "ext": format["ext"],
                                "format_note": format.get("format_note"),
                                "yturl": link,
                            }
                        )
                except:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        try:
            if songvideo or songaudio:
                downloaded_file = await download_song(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
            elif video:
                downloaded_file = await download_video(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
            else:
                downloaded_file = await download_song(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
        except Exception as e:
            print(f"Download failed: {e}")
            return None, False
