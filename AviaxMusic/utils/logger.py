from pyrogram.enums import ParseMode

from AviaxMusic import app
from AviaxMusic.utils.database import is_on_off
from config import LOG_GROUP_ID


async def play_logs(message, streamtype):
    if await is_on_off(2):
        logger_text = f"""
<b>🤣 {app.mention} — New Play Log Drop Ho Gaya!</b>

<b>📍 Chat Ka Pata:</b>
• <b>ID:</b> <code>{message.chat.id}</code>
• <b>Name:</b> {message.chat.title}
• <b>Username:</b> @{message.chat.username if message.chat.username else "🤡 No Username"}

<b>🕺 User Ka Scene:</b>
• <b>User ID:</b> <code>{message.from_user.id}</code>
• <b>Name:</b> {message.from_user.mention}
• <b>Username:</b> @{message.from_user.username if message.from_user.username else "😎 Secret User"}

<b>🔍 Query Dekh Zara:</b> {message.text.split(None, 1)[1]}
<b>🎶 Stream Type:</b> {streamtype}

<b>📢 Note:</b>  
User ne gaana lagaya hai,  
bot bol raha: “Chal bhai, bajate hain!” 🎧🔥
        """
        if message.chat.id != LOG_GROUP_ID:
            try:
                await app.send_message(
                    chat_id=LOG_GROUP_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except:
                pass
        return
