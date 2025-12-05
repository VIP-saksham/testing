import math
from config import OWNER_ID, SUPPORT_CHAT
from pyrogram.types import InlineKeyboardButton
import config
from AviaxMusic import app
from AviaxMusic.utils.formatters import time_to_seconds


def track_markup(_, videoid, user_id, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]
    return buttons


def stream_markup_timer(_, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100
    umm = math.floor(percentage)
    if 0 < umm <= 10:
        bar = " ^|^d ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^`"
    elif 10 < umm < 20:
        bar = "- ^k ^o ^|^d ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^`"
    elif 20 <= umm < 30:
        bar = "- ^k ^o- ^k ^o ^|^d ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^`"
    elif 30 <= umm < 40:
        bar = "- ^k ^o- ^k ^o- ^k ^o ^|^d ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^`"
    elif 40 <= umm < 50:
        bar = "- ^k ^o- ^k ^o- ^k ^o- ^k ^o ^|^d ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^`"
    elif 50 <= umm < 60:
        bar = "- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o ^|^d ^g ^t^` ^g ^t^` ^g ^t^` ^g ^t^`"
    elif 60 <= umm < 70:
        bar = "- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o ^|^d ^g ^t^` ^g ^t^` ^g ^t^`"
    elif 70 <= umm < 80:
        bar = "- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o ^|^d ^g ^t^` ^g ^t^`"
    elif 80 <= umm < 95:
        bar = "- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o ^|^d ^g ^t^`"
    else:
        bar = "- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o- ^k ^o ^|^d ^g"
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{played} {bar} {dur}",
                callback_data="GetTimer",
            )
        ],
                [
         InlineKeyboardButton(text=_["S_B_3"], url=f"https://t.me/{app.username}?startgroup=true",)
        ],
        [
            InlineKeyboardButton(text=" ^}^z ^}^z", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text=" ^v ", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text=" ^f ", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text=" ^v ", callback_data=f"ADMIN Stop|{chat_id}"),
            InlineKeyboardButton(text=" ^`  ^` I", callback_data=f"ADMIN Skip|{chat_id}"),
        ],
        [
            InlineKeyboardButton(
                text="[ ^=^g  ^=^g ]  ^}^p^n       ^g ^`  ^` ", user_id=config.OWNER_ID,
            ),
            InlineKeyboardButton(
                text=" ^`   ^}^p^t  ^x  ^e  ^`  ^{  ^gs  ^` ", url=config.SUPPORT_CHANNEL
            ),
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close")],
    ]
    return buttons


def stream_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text=" ^}^z ^}^z", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text=" ^v ", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text=" ^f ", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text=" ^v ", callback_data=f"ADMIN Stop|{chat_id}"),
            InlineKeyboardButton(text=" ^`  ^` I", callback_data=f"ADMIN Skip|{chat_id}"),
        ],
        [
            InlineKeyboardButton(
                text="[ ^=^g  ^=^g ]  ^}^p^n       ^g ^`  ^` ", user_id=config.OWNER_ID,
            ),
            InlineKeyboardButton(
                text=" ^`   ^}^p^t  ^x  ^e  ^`  ^{  ^gs  ^` ", url=config.SUPPORT_CHANNEL
            ),
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close")],
    ]
    return buttons


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"AlonePlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"AlonePlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = f"{query[:20]}"
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=" ^w^a",
                callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {query}|{user_id}",
            ),
            InlineKeyboardButton(
                text=" ^v ",
                callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
        ],
    ]
    return buttons
































