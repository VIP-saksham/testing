import math
from pyrogram.types import InlineKeyboardButton
import config
from AviaxMusic import app
from AviaxMusic.utils.formatters import time_to_seconds

OWNER_ID = config.OWNER_ID


# -----------------------------
# Track buttons (Audio / Video)
# -----------------------------
def track_markup(_, videoid, user_id, channel, fplay):
    return [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}"
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}"
            )
        ],
    ]
    


# -----------------------------
# SHIP TIMELINE MAKER (SAFE WIDTH)
# -----------------------------
def make_ship_timeline(played_sec, dur_sec):
    # avoid division error
    if dur_sec <= 0:
        percent = 0
    else:
        percent = (played_sec / dur_sec) * 100

    bar_len = 12  # PERFECT thumbnail width
    filled_len = int((percent / 100) * bar_len)

    ship = "𓊝"
    water = "﹏"

    # avoid out of range
    if filled_len >= bar_len:
        filled_len = bar_len - 1

    # build bar
    bar = (
        water * filled_len
        + ship
        + water * (bar_len - filled_len - 1)
    )

    return bar


# -----------------------------
# Stream buttons (with timer)
# -----------------------------
def stream_markup_timer(_, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    dur_sec = time_to_seconds(dur)

    # Build safe-width ship timeline
    bar = make_ship_timeline(played_sec, dur_sec)

    buttons = [
        [
            InlineKeyboardButton(text="⏮ ", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="⏸ ", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="▶️", callback_data=f"ADMIN Resume|{chat_id}"),
        ],

        # SHIP BAR WITH TIME
        [
            InlineKeyboardButton(
                text=f"{played}  {bar}  {dur}",
                callback_data="GetTimer"
            )
        ],

        [
            InlineKeyboardButton(text="⏪ 20s", callback_data=f"ADMIN Back|{chat_id}"),
            InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close"),
            InlineKeyboardButton(text="⏩ 20s", callback_data=f"ADMIN Forward|{chat_id}"),
        ],
    ]

    return buttons


# -----------------------------
# Stream controls (no timer)
# -----------------------------
def stream_markup(_, chat_id):
    return [
        [
            InlineKeyboardButton(text="⏮ ", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="⏸ ", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="▶️", callback_data=f"ADMIN Resume|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="⏪ 20s", callback_data=f"ADMIN Back|{chat_id}"),
            InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close"),
            InlineKeyboardButton(text="⏩ 20s", callback_data=f"ADMIN Forward|{chat_id}"),
        ],
    ]


# -----------------------------
# Playlist buttons
# -----------------------------
def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    return [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"AlonePlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}"
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"AlonePlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}"
            )
        ],
    ]


# -----------------------------
# Livestream play buttons
# -----------------------------
def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    return [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}"
            )
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}"
            )
        ],
    ]


# -----------------------------
# Slider buttons
# -----------------------------
def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    short_query = query[:20]

    return [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}"
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="Prev",
                callback_data=f"slider B|{query_type}|{short_query}|{user_id}|{channel}|{fplay}"
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {short_query}|{user_id}"
            ),
            InlineKeyboardButton(
                text="Next",
                callback_data=f"slider F|{query_type}|{short_query}|{user_id}|{channel}|{fplay}"
            ),
        ],
    ]

