from typing import Union
from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from AviaxMusic import app
from AviaxMusic.utils.database import get_lang
from AviaxMusic.utils.decorators.language import LanguageStart, languageCB
from config import BANNED_USERS, START_IMG_URL, SUPPORT_GROUP
from strings import get_string, helpers


# ---------------- MAIN HELP PANEL ----------------
def help_pannel(_, main_menu=False):
    buttons = [
        [
            InlineKeyboardButton("👑 Admins", callback_data="help_callback:adm"),
            InlineKeyboardButton("🌐 Public", callback_data="help_callback:pub"),
        ],
        [
            InlineKeyboardButton("🛡️ Sudo", callback_data="help_callback:sudo"),
            InlineKeyboardButton("🎮 Game", callback_data="help_callback:game"),
        ]
    ]

    # CLOSE BUTTON ONLY ON MAIN MENU
    if main_menu:
        buttons.append([
            InlineKeyboardButton("❌ Close", callback_data="go_start")
        ])

    return InlineKeyboardMarkup(buttons)


# ---------------- ONLY BACK IN SUB-MENUS ----------------
def help_back_markup(_):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅ Back", callback_data="help_main_menu")]
    ])


# ---------------- SAFE EDIT FUNCTION ----------------
async def safe_edit(callback: CallbackQuery, text: str, markup=None):
    try:
        await callback.edit_message_text(text, reply_markup=markup)
    except Exception as e:
        if "MESSAGE_NOT_MODIFIED" not in str(e):
            print("Edit error:", e)


# ---------------- MAIN MENU ----------------
@app.on_callback_query(filters.regex("^help_main_menu$") & ~BANNED_USERS)
async def help_main_menu(client, CallbackQuery: CallbackQuery):
    lang = await get_lang(CallbackQuery.message.chat.id)
    _ = get_string(lang)

    await CallbackQuery.answer()
    text = _["help_1"].format(SUPPORT_GROUP)

    markup = help_pannel(_, main_menu=True)
    await safe_edit(CallbackQuery, text, markup)


# ---------------- PRIVATE HELP ----------------
@app.on_message(filters.command("help") & filters.private & ~BANNED_USERS)
async def helper_private(client, message: Message):
    lang = await get_lang(message.chat.id)
    _ = get_string(lang)

    await message.reply_photo(
        photo=START_IMG_URL,
        caption=_["help_1"].format(SUPPORT_GROUP),
        reply_markup=help_pannel(_, main_menu=True)
    )


# ---------------- GROUP HELP ----------------
@app.on_message(filters.command("help") & filters.group & ~BANNED_USERS)
@LanguageStart
async def help_com_group(client, message: Message, _):
    await message.reply_text(
        _["help_2"],
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 Admins", callback_data="help_callback:adm")],
            [InlineKeyboardButton("🌐 Public", callback_data="help_callback:pub")],
            [InlineKeyboardButton("🛡️ Sudo", callback_data="help_callback:sudo")],
            [InlineKeyboardButton("🎮 Game", callback_data="help_callback:game")],
        ])
    )


# ---------------- HELP SUB MENU ----------------
@app.on_callback_query(filters.regex("^help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery: CallbackQuery, _):
    cb = CallbackQuery.data.split(":")[1]
    text = getattr(helpers, f"HELP_{cb.upper()}", "No Information Found!")

    await CallbackQuery.answer()
    await safe_edit(CallbackQuery, text, help_back_markup(_))


# ---------------- GO TO /START PANEL ----------------
@app.on_callback_query(filters.regex("^go_start$") & ~BANNED_USERS)
async def go_start_callback(client, CallbackQuery: CallbackQuery):

    await CallbackQuery.answer()

    lang = await get_lang(CallbackQuery.from_user.id)
    _ = get_string(lang)

    from AviaxMusic.utils.inline import private_panel
    import config
    from AviaxMusic.utils import bot_sys_stats

    UP, CPU, RAM, DISK = await bot_sys_stats()

    await CallbackQuery.message.reply_photo(
        photo=config.START_IMG_URL,
        caption=_["start_2"].format(
            CallbackQuery.from_user.mention,
            client.mention,
            UP, DISK, CPU, RAM
        ),
        reply_markup=InlineKeyboardMarkup(private_panel(_)),
    )
