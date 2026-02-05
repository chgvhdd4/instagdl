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

def main_menu(update):
    keyboard = [
        [InlineKeyboardButton("دانلود عکس پروفایل", callback_data="profile_pic")],
        [InlineKeyboardButton("دانلود ۱۰ تا پست آخر پروفایل", callback_data="all_posts")],
        [InlineKeyboardButton("دانلود پست و ریل با لینک", callback_data="post_link")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("سلام 👋 چی میخوای؟", reply_markup=reply_markup)

def start(update, context):
    main_menu(update)

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
        elif file.endswith(".jpg"):
            image_file = path
        elif file.endswith(".txt"):
            caption_text = open(path, "r", encoding="utf-8").read()

    if video_file:
        update.message.reply_video(open(video_file, "rb"), caption=caption_text[:1024])
    elif image_file:
        update.message.reply_photo(open(image_file, "rb"), caption=caption_text[:1024])
    else:
        update.message.reply_text("No media found.")

def download_last_10_posts(update, username):
    profile = instaloader.Profile.from_username(L.context, username)
    posts = list(profile.get_posts())[:10]  # LIMIT TO LAST 10 POSTS

    update.message.reply_text(f"...{username}دانلود ۱۰ تا پست آخر")

    for post in posts:
        clean_folder("post")
        L.download_post(post, target="post")
        send_single_post(update, "post")

    clean_folder("post")
    update.message.reply_text("!انجام شد")

def button_handler(update, context):
    query = update.callback_query
    query.answer()

    context.user_data["mode"] = query.data

    # Back button
    if query.data == "back":
        query.edit_message_text("بازگشت به منو")
        main_menu(query)
        return

    # Normal menu options
    if query.data == "profile_pic":
        query.edit_message_text(".نام کاربری مورد نظر را ارسال کنید\n\n⬅️ /back")
    elif query.data == "all_posts":
        query.edit_message_text(".نام کاربری مورد نظر را ارسال کنید\n\n⬅️ /back")
    elif query.data == "post_link":
        query.edit_message_text(".لینک را ارسال کنید\n\n⬅️ /back")

def handle_message(update, context):
    text = update.message.text.strip()
    mode = context.user_data.get("mode", None)

    # Back command
    if text == "/back":
        main_menu(update)
        return

    # Download post/reel from link
    if mode == "post_link" and "instagram.com" in text:
        update.message.reply_text("...درحال دانلود")
        clean_folder("post")

        try:
            shortcode = text.split("/")[-2]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target="post")
            send_single_post(update, "post")
        except Exception as e:
            print(e)
            update.message.reply_text(".پست دانلود نشد")

        clean_folder("post")
        return

    # Download profile picture
    if mode == "profile_pic" and text.startswith("@"):
        username = text[1:]
        update.message.reply_text(f"{username}در حال دانلود عکس پروفایل")

        clean_folder(username)

        try:
            L.download_profile(username, profile_pic_only=True)

            for file in os.listdir(username):
                if file.endswith(".jpg"):
                    update.message.reply_photo(open(f"{username}/{file}", "rb"))
                    break

            update.message.reply_text(".عکس پروفایل ارسال شد")
        except Exception as e:
            print(e)
            update.message.reply_text(".عکس پروفایل دانلود نشد")

        clean_folder(username)
        return

    # Download last 10 posts
    if mode == "all_posts" and text.startswith("@"):
        username = text[1:]
        try:
            download_last_10_posts(update, username)
        except Exception as e:
            print(e)
            update.message.reply_text(".پست دانلود نشد")
        return

    update.message.reply_text(".بفرست/startبرای انتخاب آپشن")

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
