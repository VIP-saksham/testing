from typing import Union
from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from AviaxMusic import app
from AviaxMusic.utils.database import get_lang
from AviaxMusic.utils.decorators.language import LanguageStart, languageCB
from config import BANNED_USERS, START_IMG_URL, SUPPORT_GROUP
from strings import get_string, helpers


# ---------------- MAIN HELP PANEL ----------------
def help_pannel(_, back=False):
    buttons = [
        [
            InlineKeyboardButton("👑 Admins", callback_data="help_callback adm"),
            InlineKeyboardButton("🌐 Public", callback_data="help_callback pub"),
        ],
        [
            InlineKeyboardButton("🛡️ Sudo", callback_data="help_callback sudo"),
            InlineKeyboardButton("🎮 Game", callback_data="help_callback game"),
        ]
    ]

    if back:
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="help_main_menu")])

    return InlineKeyboardMarkup(buttons)


def private_help_panel(_):
    return [
        [InlineKeyboardButton("👑 Admins", callback_data="help_callback adm")],
        [InlineKeyboardButton("🌐 Public", callback_data="help_callback pub")],
        [InlineKeyboardButton("🛡️ Sudo", callback_data="help_callback sudo")],
        [InlineKeyboardButton("🎮 Game", callback_data="help_callback game")],
    ]


def help_back_markup(_):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 Back", callback_data="help_main_menu")]]
    )


# ---------------- MAIN MENU RELOADER ----------------
@app.on_callback_query(filters.regex("help_main_menu") & ~BANNED_USERS)
async def help_main_menu(client, CallbackQuery: CallbackQuery):
    lang = await get_lang(CallbackQuery.message.chat.id)
    _ = get_string(lang)

    await CallbackQuery.answer()
    await CallbackQuery.edit_message_text(
        _["help_1"].format(SUPPORT_GROUP),
        reply_markup=help_pannel(_, True)
    )


# ---------------- PRIVATE HELP ----------------
@app.on_message(filters.command("help") & filters.private & ~BANNED_USERS)
async def helper_private(client, message: Message):
    lang = await get_lang(message.chat.id)
    _ = get_string(lang)

    await message.reply_photo(
        photo=START_IMG_URL,
        caption=_["help_1"].format(SUPPORT_GROUP),
        reply_markup=help_pannel(_, True),
    )


# ---------------- GROUP HELP ----------------
@app.on_message(filters.command("help") & filters.group & ~BANNED_USERS)
@LanguageStart
async def help_com_group(client, message: Message, _):
    await message.reply_text(
        _["help_2"],
        reply_markup=InlineKeyboardMarkup(private_help_panel(_))
    )


# ---------------- HELP CALLBACK HANDLER ----------------
@app.on_callback_query(filters.regex("help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery: CallbackQuery, _):
    cb = CallbackQuery.data.split()[1]  # adm / pub / sudo / game

    text = getattr(helpers, f"HELP_{cb.upper()}", "No Information Found!")

    await CallbackQuery.answer()
    await CallbackQuery.edit_message_text(
        text,
        reply_markup=help_back_markup(_)
    )
