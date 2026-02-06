import os
import shutil
import instaloader
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# Instaloader instance
L = instaloader.Instaloader(
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)

# ---------------- منوی اصلی ---------------- #
def main_menu(update):
    keyboard = [
        [InlineKeyboardButton("📸 دانلود عکس پروفایل", callback_data="profile_pic")],
        [InlineKeyboardButton("📥 دانلود ۱۰ پست آخر", callback_data="last10")],
        [InlineKeyboardButton("🔗 دانلود پست/ریل از لینک", callback_data="post_link")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Works for both message and callback_query
    if update.message:
        update.message.reply_text("یکی از گزینه‌ها رو انتخاب کن:", reply_markup=reply_markup)
    else:
        update.callback_query.message.reply_text("یکی از گزینه‌ها رو انتخاب کن:", reply_markup=reply_markup)
def start(update, context):
    main_menu(update)

# ---------------- ابزارها ---------------- #

def clean_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)

def send_single_post(update, folder):
    video_file = None
    image_file = None
    caption_text = ""

    for file in os.listdir(folder):
        path = os.path.join(folder, file)

        if file.endswith(".mp4"):
            video_file = path

        elif file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            image_file = path

        elif file.endswith(".txt"):
            caption_text = open(path, "r", encoding="utf-8").read()

    if video_file:
        update.message.reply_video(open(video_file, "rb"), caption=caption_text[:1024])
    elif image_file:
        update.message.reply_photo(open(image_file, "rb"), caption=caption_text[:1024])
    else:
        update.message.reply_text("هیچ مدیایی پیدا نشد!")

# ---------------- دانلود ۱۰ پست آخر ---------------- #

def download_last_10_posts(update, username):
    profile = instaloader.Profile.from_username(L.context, username)
    posts = list(profile.get_posts())[:10]  # فقط ۱۰ پست آخر

    update.message.reply_text(f"دارم ۱۰ پست آخر @{username} رو دانلود می‌کنم...")

    for post in posts:
        clean_folder("post")
        L.download_post(post, target="post")
        send_single_post(update, "post")

    clean_folder("post")
    update.message.reply_text("۱۰ پست آخر ارسال شد ✔️")

# ---------------- دکمه‌ها ---------------- #

def button_handler(update, context):
    query = update.callback_query
    query.answer()

    context.user_data["mode"] = query.data

    if query.data == "back":
        query.edit_message_text("برگشتیم به منو.")
        main_menu(update)
        return

    if query.data == "profile_pic":
        query.edit_message_text("یوزرنیم رو به صورت @username بفرست.\n\n⬅️ برای برگشت /back رو بفرست")

    elif query.data == "last10":
        query.edit_message_text("یوزرنیم رو بفرست تا ۱۰ پست آخرشو دانلود کنم.\n\n⬅️ برای برگشت /back رو بفرست")

    elif query.data == "post_link":
        query.edit_message_text("لینک پست یا ریل اینستاگرام رو بفرست.\n\n⬅️ برای برگشت /back رو بفرست")
# ---------------- پیام‌ها ---------------- #

def handle_message(update, context):
    text = update.message.text.strip()
    mode = context.user_data.get("mode", None)

    if text == "/back":
        main_menu(update)
        return

    # دانلود پست/ریل از لینک
    if mode == "post_link" and "instagram.com" in text:
        update.message.reply_text("دارم دانلود می‌کنم، یه لحظه صبر کن...")
        clean_folder("post")

        try:
            shortcode = text.split("/")[-2]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target="post")
            send_single_post(update, "post")
        except Exception as e:
            print(e)
            update.message.reply_text("نتونستم پست رو دانلود کنم!")

        clean_folder("post")
        return

    # دانلود عکس پروفایل
# دانلود عکس پروفایل
    if mode == "profile_pic" and text.startswith("@"):
        username = text[1:]
        update.message.reply_text(f"دارم عکس پروفایل @{username} رو دانلود می‌کنم...")

        user_id = update.effective_user.id
        folder = f"profile_{user_id}"
        clean_folder(folder)

        try:
            profile = instaloader.Profile.from_username(L.context, username)

            # Direct URL to profile picture
            pic_url = profile.profile_pic_url

            # Download manually
            import requests
            img_data = requests.get(pic_url).content

            file_path = os.path.join(folder, "profile.jpg")
            with open(file_path, "wb") as f:
                f.write(img_data)

            update.message.reply_photo(open(file_path, "rb"))
            update.message.reply_text("عکس پروفایل ارسال شد ✔️")

        except Exception as e:
            print(e)
            update.message.reply_text("نتونستم عکس پروفایل رو دانلود کنم!")

        clean_folder(folder)
        return
    # دانلود ۱۰ پست آخر
    if mode == "last10" and text.startswith("@"):
        username = text[1:]
        try:
            download_last_10_posts(update, username)
        except Exception as e:
            print(e)
            update.message.reply_text("نتونستم پست‌ها رو دانلود کنم!")
        return

    update.message.reply_text("اول از منو یکی از گزینه‌ها رو انتخاب کن /start")

# ---------------- اجرای ربات ---------------- #

def main():
    TOKEN = "8508847587:AAFgHA1RSi7TUlVOQ8gRtr-wiJQaaC04tM8"

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
