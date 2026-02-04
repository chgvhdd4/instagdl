from aiogram import Bot, Dispatcher, executor, types
import logging
from downloader import InstagramVideoDownloader
import shutil
from dotenv import load_dotenv
import os

load_dotenv()

bot = Bot('8470724978:AAH1Z7eHKrbuw1feJ6TS_UwtgtIx3kHVJYE')
dp = Dispatcher(bot)

# ============================
#       MENU BUTTONS
# ============================
menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu.add("📥 Instagram Video", "🖼 Profile Picture")
menu.add("ℹ️ Help")


# ============================
#       START COMMAND
# ============================
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        f"Salom {message.from_user.full_name}\nQuyidagi menyudan tanlang:",
        reply_markup=menu
    )


# ============================
#   PROFILE PIC DOWNLOADER
# ============================
async def download_profile_pic(message, username):
    try:
        user = await bot.get_chat(username)
        photos = await bot.get_user_profile_photos(user.id)

        if photos.total_count == 0:
            await message.answer("Bu foydalanuvchida profil rasmi yo‘q.")
            return

        file_id = photos.photos[0][-1].file_id
        await message.answer_photo(file_id, caption=f"@{username} profil rasmi")

    except Exception:
        await message.answer("Foydalanuvchi topilmadi yoki profil rasmi mavjud emas.")


# ============================
#       MAIN HANDLER
# ============================
@dp.message_handler()
async def mainpart(message: types.Message):
    text = message.text

    # --- Instagram Video Mode ---
    if text == "📥 Instagram Video":
        await message.answer("Instagram linkini yuboring")
        return

    if text.startswith("https://www.instagram.com/") or text.startswith("https://instagram.com/"):
        await message.answer("Video yuklanmoqda...")

        try:
            downloaded = InstagramVideoDownloader(text)

            with open(downloaded[1][0], 'rb') as video:
                with open(downloaded[0], "rb") as comment:
                    await message.answer_video(
                        video,
                        caption=comment.read().decode("utf-8")
                    )

            shutil.rmtree(downloaded[2])

        except Exception as e:
            await message.answer("Video yuklashda xatolik yuz berdi.")
            print(e)

        return

    # --- Profile Picture Mode ---
    if text == "🖼 Profile Picture":
        await message.answer("Foydalanuvchi username kiriting (masalan: @username)")
        return

    if text.startswith("@"):
        await download_profile_pic(message, text[1:])
        return

    # --- Help ---
    if text == "ℹ️ Help":
        await message.answer(
            "Bot funksiyalari:\n"
            "📥 Instagram videolarini yuklab beradi\n"
            "🖼 Telegram profil rasmlarini yuklab beradi\n"
            "Foydalanish juda oson!"
        )
        return

    # Unknown input
    await message.answer("Menyudan birini tanlang.")


# ============================
#       RUN BOT
# ============================
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=False)        with open(downloaded[1][0], 'rb') as video:
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
