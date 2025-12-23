import logging
from os import getenv
from pyrogram import Client
from pyromod import listen
from pyrogram import filters
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import CallbackQuery, Message
from pyrogram.handlers import MessageHandler
from utilsdf.db import Database
from utilsdf.vars import PREFIXES
import os, sys, importlib


API_ID = '20033023'
API_HASH = '0258926fae81f21016d153465e2cbe64'
BOT_TOKEN = '7793614035:AAEmnWNGt6wvs6ebEzTH8pBToxjqkEnFPOI'


CHANNEL_LOGS = -1003680818677

app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),
    parse_mode=ParseMode.HTML,
)

# ================== START ==================
async def start(client, message: Message):
    if message.chat.id != CHANNEL_LOGS:
        return

    await message.reply("Bot started! Use /help for commands.")

app.add_handler(
    MessageHandler(
        start,
        filters.command("start") & filters.group
    )
)

# ================== CALLBACK GUARD ==================
@app.on_callback_query()
async def warn_user(client: Client, callback_query: CallbackQuery):

    # 🔒 group lock
    if callback_query.message.chat.id != CHANNEL_LOGS:
        await callback_query.answer("Not allowed here", show_alert=True)
        return

    # menu ownership check
    if callback_query.message.reply_to_message:
        ru = callback_query.message.reply_to_message.from_user
        if ru and callback_query.from_user.id != ru.id:
            await callback_query.answer("Use your own menu! ⚠️", show_alert=True)
            return

    await callback_query.continue_propagation()

# ================== TEXT / BAN HANDLER ==================
@app.on_message(filters.text & filters.group)
async def user_ban(client: Client, m: Message):

    # 🔒 HARD GROUP LOCK
    if m.chat.id != CHANNEL_LOGS:
        return

    if not m.from_user or not m.text:
        return

    # ❗ commands ko plugins handle karenge
    if m.text.startswith("/"):
        await m.continue_propagation()
        return

    user_id = m.from_user.id
    username = m.from_user.username or "unknown"

    with Database() as db:
        db.remove_expireds_users()

        if db.is_ban(user_id):
            return

        # ---- YOUR ORIGINAL LOGIC ----
        async for member in m.chat.get_members():
            if not member.user:
                continue
            if member.status == ChatMemberStatus.ADMINISTRATOR:
                continue

            uid = member.user.id

            if db.is_seller_or_admin(uid):
                continue
            if db.is_premium(uid):
                continue
            if db.user_has_credits(uid):
                continue

            await m.chat.ban_member(uid)

            info = db.get_info_user(uid)
            await client.send_message(
                CHANNEL_LOGS,
                f"<b>User eliminado: @{info['USERNAME']}</b>"
            )

        db.register_user(user_id, username)

    await m.continue_propagation()

# ================== RUN ==================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    app.run()
