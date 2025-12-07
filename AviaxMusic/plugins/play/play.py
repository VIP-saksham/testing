import os
import json
import asyncio
import random
import string
from pathlib import Path
from typing import Tuple, Optional

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InputMediaPhoto, Message
from pytgcalls.exceptions import NoActiveGroupCall

import config
from AviaxMusic import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app
from AviaxMusic.core.call import Aviax
from AviaxMusic.utils import seconds_to_min, time_to_seconds
from AviaxMusic.utils.channelplay import get_channeplayCB
from AviaxMusic.utils.decorators.language import languageCB
from AviaxMusic.utils.decorators.play import PlayWrapper
from AviaxMusic.utils.formatters import formats
from AviaxMusic.utils.inline import (
    botplaylist_markup,
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
from AviaxMusic.utils.logger import play_logs
from AviaxMusic.utils.stream.stream import stream
from config import BANNED_USERS, lyrical

# local cache file mapping video_id -> t.me link (or message id + channel)
CACHE_FILE = Path("channel_cache.json")
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
_channel_cache_lock = asyncio.Lock()

# Upload channel (set this in config.py)
UPLOAD_CHANNEL = getattr(config, "UPLOAD_CHANNEL", None)  # e.g. "@NakshuMuiscDB" or numeric

# Helper: load/save cache
def load_channel_cache() -> dict:
    try:
        if CACHE_FILE.exists():
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

async def save_channel_cache(cache: dict):
    async with _channel_cache_lock:
        try:
            CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
        except Exception:
            pass

# Helper: check if the cache has valid t.me link and if file exists (try to fetch)
async def get_cached_telegram_file(video_id: str, file_type: str) -> Optional[str]:
    """
    If cached, try to download the file from the cached telegram link and return local path.
    file_type: "audio" or "video" (extension used)
    """
    cache = load_channel_cache()
    entry = cache.get(video_id)
    if not entry:
        return None
    tg_link = entry.get("link")
    if not tg_link:
        return None
    try:
        # try to download via Telegram helper (Telegram.get_messages / download)
        local = await Telegram.get_filepath_from_tg_link(tg_link, video_id, file_type)
        # fallback: if Telegram helper isn't present, try Telegram.get_messages + download
        if not local:
            # parse t.me link -> message id might be last part
            # Telegram.get_messages expects chat id or username and message id
            from urllib.parse import urlparse
            parsed = urlparse(tg_link)
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2:
                chat = parts[0]
                msg_id = int(parts[-1])
                msg = await app.get_messages(chat_id=chat, message_ids=msg_id)
                if msg:
                    ext = ".webm" if file_type == "audio" else ".mkv"
                    dest = Path("downloads") / f"{video_id}{ext}"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    await app.download_media(msg, str(dest))
                    return str(dest)
        else:
            return local
    except Exception:
        return None
    return None

# Helper: upload local file to your channel and return t.me link
async def upload_file_to_channel(local_path: str, video_id: str, file_type: str) -> Optional[str]:
    """
    Uploads the given local file to UPLOAD_CHANNEL and returns the telegram link (t.me/...)
    """
    if not UPLOAD_CHANNEL:
        return None
    try:
        # choose send method based on type: audio for .webm/.mp3 (.audio), video for .mkv/.mp4 (.video)
        file_obj = open(local_path, "rb")
        if file_type == "audio":
            sent = await app.send_audio(chat_id=UPLOAD_CHANNEL, audio=file_obj, caption=video_id)
        else:
            sent = await app.send_document(chat_id=UPLOAD_CHANNEL, document=file_obj, caption=video_id)
        file_obj.close()

        # build t.me link if channel is username-based
        # if UPLOAD_CHANNEL is @username -> t.me/username/<message_id>
        if isinstance(UPLOAD_CHANNEL, str) and UPLOAD_CHANNEL.startswith("@"):
            username = UPLOAD_CHANNEL.lstrip("@")
            link = f"https://t.me/{username}/{sent.message_id}"
        else:
            # unknown; return a tg:// or channel/chat/message tuple in cache
            link = f"tg://openmessage?chat_id={UPLOAD_CHANNEL}&message_id={sent.message_id}"
        # store in cache
        cache = load_channel_cache()
        cache.setdefault(video_id, {})["link"] = link
        await save_channel_cache(cache)
        return link
    except Exception as e:
        try:
            file_obj.close()
        except:
            pass
        return None

# Small helper to generate random hash (used for playlist keys)
def random_hash(n=10):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


# ---------- MAIN PLAY HANDLER ----------
@app.on_message(
    filters.command(
        [
            "play",
            "vplay",
            "cplay",
            "cvplay",
            "playforce",
            "vplayforce",
            "cplayforce",
            "cvplayforce",
        ]
    )
    & filters.group
    & ~BANNED_USERS
)
@PlayWrapper
async def play_commnd(
    client,
    message: Message,
    _,
    chat_id,
    video,
    channel,
    playmode,
    url,
    fplay,
):
    """Play command integrated with channel upload/cache for fast availability."""
    mystic = await message.reply_text(_["play_2"].format(channel) if channel else _["play_1"])
    plist_id = None
    slider = None
    plist_type = None
    spotify = None
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Handle replied Telegram audio/video first (as before)
    audio_telegram = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    video_telegram = (
        (message.reply_to_message.video or message.reply_to_message.document)
        if message.reply_to_message
        else None
    )

    if audio_telegram:
        # identical flow: validate and stream local Telegram file
        if audio_telegram.file_size > 104857600:
            return await mystic.edit_text(_["play_5"])
        duration_min = seconds_to_min(audio_telegram.duration) if getattr(audio_telegram, "duration", None) else "0:00"
        if (audio_telegram.duration) > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
            )
        file_path = await Telegram.get_filepath(audio=audio_telegram)
        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(audio_telegram, audio=True)
            dur = await Telegram.get_duration(audio_telegram, file_path)
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()
        return

    if video_telegram:
        # identical flow for video replies
        if message.reply_to_message.document:
            try:
                ext = video_telegram.file_name.split(".")[-1]
                if ext.lower() not in formats:
                    return await mystic.edit_text(
                        _["play_7"].format(f"{' | '.join(formats)}")
                    )
            except:
                return await mystic.edit_text(
                    _["play_7"].format(f"{' | '.join(formats)}")
                )
        if video_telegram.file_size > config.TG_VIDEO_FILESIZE_LIMIT:
            return await mystic.edit_text(_["play_8"])
        file_path = await Telegram.get_filepath(video=video_telegram)
        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(video_telegram)
            dur = await Telegram.get_duration(video_telegram, file_path)
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    video=True,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()
        return

    # If URL provided (youtube/spotify/apple/soundcloud/resso etc.)
    if url:
        # YOUTUBE playlist or track
        if await YouTube.exists(url):
            if "playlist" in url:
                try:
                    details = await YouTube.playlist(
                        url,
                        config.PLAYLIST_FETCH_LIMIT,
                        message.from_user.id,
                    )
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "yt"
                if "&" in url:
                    plist_id = (url.split("=")[1]).split("&")[0]
                else:
                    plist_id = url.split("=")[1]
                img = config.PLAYLIST_IMG_URL
                cap = _["play_9"]
            else:
                # TRACK: here we implement channel-cache logic for faster access
                try:
                    details, track_id = await YouTube.track(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details.get("thumb")
                cap = _["play_10"].format(details.get("title"), details.get("duration_min"))

                # Try: 1) cached channel link 2) else download -> upload to channel -> then stream
                video_id = details.get("vidid") or track_id or details.get("link") or url.split("v=")[-1].split("&")[0]

                # 1) try cached t.me link
                cached_local = await get_cached_telegram_file(video_id, "audio")
                if cached_local:
                    # use cached_local path for immediate stream
                    details["path"] = cached_local
                    details["link"] = details.get("link") or cached_local
                    try:
                        await stream(
                            _,
                            mystic,
                            user_id,
                            details,
                            chat_id,
                            user_name,
                            message.chat.id,
                            streamtype="youtube",
                            forceplay=fplay,
                        )
                        await mystic.delete()
                        return await play_logs(message, streamtype="youtube")
                    except Exception as e:
                        # fallback to redownload
                        pass

                # 2) otherwise download fresh audio (Telegram friendly format)
                # Use YouTube.download / youtube module's download_song or fallback to Telegram.download helpers
                try:
                    # Try library download: expecting a path returned (function name depends on your module)
                    downloaded_file = None
                    # Try YouTube.download or YouTube.download_song if available
                    if hasattr(YouTube, "download"):
                        # some implementations return (path, True)
                        res = await YouTube.download(url, mystic, video=False, videoid=False, songaudio=True)
                        if isinstance(res, tuple):
                            downloaded_file = res[0] if res[1] else None
                        else:
                            downloaded_file = res
                    elif hasattr(YouTube, "download_song"):
                        downloaded_file = await YouTube.download_song(url)
                    else:
                        # fallback: use Telegram helper to get filepath + download (if YouTube.track returned direct url)
                        # Not ideal, but attempt to download via built-in download helper (if any)
                        downloaded_file = None
                except Exception:
                    downloaded_file = None

                # If download succeeded
                if downloaded_file and os.path.exists(downloaded_file):
                    # upload to channel async (spawn) to speed immediate streaming
                    asyncio.create_task(upload_file_to_channel(downloaded_file, video_id, "audio"))
                    details["path"] = downloaded_file
                    details["link"] = downloaded_file
                    try:
                        await stream(
                            _,
                            mystic,
                            user_id,
                            details,
                            chat_id,
                            user_name,
                            message.chat.id,
                            streamtype="youtube",
                            forceplay=fplay,
                        )
                        await mystic.delete()
                        return await play_logs(message, streamtype="youtube")
                    except Exception as e:
                        ex_type = type(e).__name__
                        err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                        return await mystic.edit_text(err)

                # If download failed, fall back to original immediate streaming method (if available)
                try:
                    await stream(
                        _,
                        mystic,
                        user_id,
                        details,
                        chat_id,
                        user_name,
                        message.chat.id,
                        streamtype="youtube",
                        forceplay=fplay,
                    )
                    await mystic.delete()
                    return await play_logs(message, streamtype="youtube")
                except Exception as e:
                    return await mystic.edit_text(_["play_3"])

        # Other providers (Spotify / Apple / Resso / SoundCloud) follow previous behavior
        elif await Spotify.valid(url):
            spotify = True
            if not config.SPOTIFY_CLIENT_ID and not config.SPOTIFY_CLIENT_SECRET:
                return await mystic.edit_text(
                    "» sᴘᴏᴛɪғʏ ɪs ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ ʏᴇᴛ.\n\nᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
                )
            if "track" in url:
                try:
                    details, track_id = await Spotify.track(url)
                except Exception as e:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_10"].format(details["title"], details["duration_min"])
            elif "playlist" in url:
                try:
                    details, plist_id = await Spotify.playlist(url)
                except Exception as e:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spplay"
                img = config.SPOTIFY_PLAYLIST_IMG_URL
                cap = _["play_11"].format(app.mention, message.from_user.mention)
            elif "album" in url:
                try:
                    details, plist_id = await Spotify.album(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spalbum"
                img = config.SPOTIFY_ALBUM_IMG_URL
                cap = _["play_11"].format(app.mention, message.from_user.mention)
            elif "artist" in url:
                try:
                    details, plist_id = await Spotify.artist(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spartist"
                img = config.SPOTIFY_ARTIST_IMG_URL
                cap = _["play_11"].format(message.from_user.first_name)
            else:
                return await mystic.edit_text(_["play_15"])

        elif await Apple.valid(url):
            if "album" in url:
                try:
                    details, track_id = await Apple.track(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_10"].format(details["title"], details["duration_min"])
            elif "playlist" in url:
                spotify = True
                try:
                    details, plist_id = await Apple.playlist(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "apple"
                cap = _["play_12"].format(app.mention, message.from_user.mention)
                img = url
            else:
                return await mystic.edit_text(_["play_3"])

        elif await Resso.valid(url):
            try:
                details, track_id = await Resso.track(url)
            except:
                return await mystic.edit_text(_["play_3"])
            streamtype = "youtube"
            img = details["thumb"]
            cap = _["play_10"].format(details["title"], details["duration_min"])

        elif await SoundCloud.valid(url):
            try:
                details, track_path = await SoundCloud.download(url)
            except:
                return await mystic.edit_text(_["play_3"])
            duration_sec = details["duration_sec"]
            if duration_sec > config.DURATION_LIMIT:
                return await mystic.edit_text(
                    _["play_6"].format(
                        config.DURATION_LIMIT_MIN,
                        app.mention,
                    )
                )
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="soundcloud",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()

        else:
            # other urls => try index/m3u8 stream fallback (keeps original behaviour)
            try:
                await Aviax.stream_call(url)
            except NoActiveGroupCall:
                await mystic.edit_text(_["black_9"])
                return await app.send_message(
                    chat_id=config.LOG_GROUP_ID,
                    text=_["play_17"],
                )
            except Exception as e:
                return await mystic.edit_text(_["general_2"].format(type(e).__name__))
            await mystic.edit_text(_["str_2"])
            try:
                await stream(
                    _,
                    mystic,
                    message.from_user.id,
                    url,
                    chat_id,
                    message.from_user.first_name,
                    message.chat.id,
                    video=video,
                    streamtype="index",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await play_logs(message, streamtype="M3u8 or Index Link")

    else:
        # No URL, do search (existing behavior)
        if len(message.command) < 2:
            buttons = botplaylist_markup(_)
            return await mystic.edit_text(
                _["play_18"],
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        slider = True
        query = message.text.split(None, 1)[1]
        if "-v" in query:
            query = query.replace("-v", "")
        try:
            details, track_id = await YouTube.track(query)
        except:
            return await mystic.edit_text(_["play_3"])
        streamtype = "youtube"

    # Now final play / direct or inline flows (same as original)
    if str(playmode) == "Direct":
        if not plist_type:
            if details.get("duration_min"):
                duration_sec = time_to_seconds(details["duration_min"])
                if duration_sec > config.DURATION_LIMIT:
                    return await mystic.edit_text(
                        _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
                    )
            else:
                buttons = livestream_markup(
                    _,
                    track_id,
                    user_id,
                    "v" if video else "a",
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                return await mystic.edit_text(
                    _["play_13"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        try:
            await stream(
                _,
                mystic,
                user_id,
                details,
                chat_id,
                user_name,
                message.chat.id,
                video=video,
                streamtype=streamtype,
                spotify=spotify,
                forceplay=fplay,
            )
        except Exception as e:
            ex_type = type(e).__name__
            err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
            return await mystic.edit_text(err)
        await mystic.delete()
        return await play_logs(message, streamtype=streamtype)

    else:
        # Inline / slider / playlist responses (same as original)
        if plist_type:
            ran_hash = random_hash()
            lyrical[ran_hash] = plist_id
            buttons = playlist_markup(
                _,
                ran_hash,
                message.from_user.id,
                plist_type,
                "c" if channel else "g",
                "f" if fplay else "d",
            )
            await mystic.delete()
            await message.reply_photo(
                photo=img,
                caption=cap,
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            return await play_logs(message, streamtype=f"Playlist : {plist_type}")
        else:
            if slider:
                buttons = slider_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    query,
                    0,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                await mystic.delete()
                await message.reply_photo(
                    photo=details.get("thumb"),
                    caption=_["play_10"].format(
                        details.get("title", "").title(),
                        details.get("duration_min", "0:00"),
                    ),
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
                return await play_logs(message, streamtype=f"Searched on Youtube")
            else:
                buttons = track_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                await mystic.delete()
                await message.reply_photo(
                    photo=img,
                    caption=cap,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
                return await play_logs(message, streamtype=f"URL Searched Inline")
