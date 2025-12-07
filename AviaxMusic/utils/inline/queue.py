import config
from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# ---------------------------------------------------
# MAIN QUEUE BUTTONS (View Queue / Time Info / Close)
# ---------------------------------------------------
def queue_markup(
    _,
    DURATION,
    CPLAY,
    videoid,
    played: Union[bool, int] = None,
    dur: Union[bool, int] = None,
):

    buttons = [
        [
            InlineKeyboardButton(" View Queue", callback_data=f"GetQueued {CPLAY}|{videoid}")
        ],
        [
            InlineKeyboardButton("   Time Info", callback_data="GetTimer")
        ],
        [
            InlineKeyboardButton("   Close Panel", callback_data="close")
        ],
    ]

    return InlineKeyboardMarkup(buttons)


# ---------------------------------------------------
# BACK BUTTON (When user opens Time Info or Queue)
# ---------------------------------------------------
def queue_back_markup(_, CPLAY):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("  Back", callback_data=f"queue_back_timer {CPLAY}"),
                InlineKeyboardButton(" Close", callback_data="close"),
            ]
        ]
    )


# ---------------------------------------------------
# AQ CONTROL PANEL (Unique / Compact / 3D feel)
# ---------------------------------------------------
def aq_markup(_, chat_id):
    buttons = [
        # Row 1: Main controls
        [
            InlineKeyboardButton("⤷ Play/Pause ", callback_data=f"ADMIN PauseResume|{chat_id}"),
            InlineKeyboardButton(" Skip ⤶", callback_data=f"ADMIN Skip|{chat_id}"),
        ],
                [InlineKeyboardButton("⤷ Close ⤶", callback_data="close"),],
        # Row 2: Replay & Stop
        [
            InlineKeyboardButton("⤷ Replay", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton("Stop ⤶", callback_data=f"ADMIN Stop|{chat_id}"),
        ],

        # Row 3: Support & Updates
        [
        ],

        # Row 4: Owner & Close
        [
        ],
    ]
    return buttons
