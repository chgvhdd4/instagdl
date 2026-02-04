from aiogram import Bot, Dispatcher, executor, types
import logging
from downloader import InstagramVideoDownloader
import shutil
from dotenv import load_dotenv
import os

load_dotenv()

bot = Bot(8470724978:AAH1Z7eHKrbuw1feJ6TS_UwtgtIx3kHVJYE)
dp = Dispatcher(bot)

# --- MENU KEYBOARD ---
menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu.add("📥 Instagram Video", "🖼 Profile Picture")
menu.add("ℹ️ Help")

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        f"Salom {message.from_user.full_name}\nQuyidagi menyudan tanlang:",
        reply_markup=menu
    )

@dp.message_handler()
async def mainpart(message: types.Message):
    text = message.text

    # --- INSTAGRAM VIDEO ---
    if text == "📥 Instagram Video":
        await message.answer("Instagram linkini yuboring")
        return

    if text.startswith("https://www.instagram.com/") or text.startswith("https://instagram.com/"):
        await message.answer("Video yuklanmoqda...")
        downloaded = InstagramVideoDownloader(text)
        with open(downloaded[1][0], 'rb') as video:
            with open(downloaded[0], "rb") as comment:
                await message.answer_video(video, caption=comment.read().decode("utf-8"))
        shutil.rmtree(downloaded[2])
        return

    # --- PROFILE PHOTO ---
    if text == "🖼 Profile Picture":
        await message.answer("Foydalanuvchi username kiriting ( @sizning_username )")
        return

    if text.startswith("@"):
        await download_profile_pic(message, text[1:])
        return

    # --- HELP ---
    if text == "ℹ️ Help":
        await message.answer("Bot Instagram video va profil rasmlarini yuklab beradi.")
        return
