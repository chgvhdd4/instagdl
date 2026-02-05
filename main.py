import os
import shutil
import instaloader
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# ---------------- تنظیمات ---------------- #

BOT_TOKEN = "8508847587:AAFgHA1RSi7TUlVOQ8gRtr-wiJQaaC04tM8"
CHANNEL_ID = "@mihab_proje"   # کانالی که کاربر باید عضو باشد

L = instaloader.Instaloader(
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)

# ---------------- چک عضویت اجباری ---------------- #

def is_member(bot, user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def force_join(update):
    keyboard = [[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_ID.replace('@','')}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "برای استفاده از ربات باید عضو کانال بشی ❤️",
        reply_markup=reply_markup
    )

# ---------------- منوی اصلی ---------------- #

def main_menu(update):
    keyboard = [
        [InlineKeyboardButton("📸 دانلود عکس پروفایل", callback_data="profile_pic")],
        [InlineKeyboardButton("📥 دانلود ۱۰ پست آخر", callback_data="last10")],
        [InlineKeyboardButton("🔗 دانلود پست/ریل از لینک", callback_data="post_link")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    chat_id = update.effective_chat.id

    with open("menu.jpg", "rb") as photo:
        update.bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption="یکی از گزینه‌ها رو انتخاب کن:",
            reply_markup=reply_markup
        )

def start(update, context):
    user_id = update.message.from_user.id
    if not is_member(context.bot, user_id):
        force_join(update)
        return

    main_menu(update)

# ---------------- ابزارها ---------------- #

def clean_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)

def send_single_post(update, folder):
    video = None
    image = None
    caption = ""

    for f in os.listdir(folder):
        p = os.path.join(folder, f)

        if f.endswith(".mp4"):
            video = p
        elif f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            image = p
        elif f.endswith(".txt"):
            caption = open(p, "r", encoding="utf-8").read()

    if video:
        update.message.reply_video(open(video, "rb"), caption=caption[:1024])
    elif image:
        update.message.reply_photo(open(image, "rb"), caption=caption[:1024])
    else:
        update.message.reply_text("هیچ مدیایی پیدا نشد!")

# ---------------- دانلود ۱۰ پست آخر ---------------- #

def download_last10(update, username):
    profile = instaloader.Profile.from_username(L.context, username)
    posts = list(profile.get_posts())[:10]

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

    user_id = query.from_user.id
    if not is_member(context.bot, user_id):
        query.message.reply_text("اول باید عضو کانال بشی ❤️")
        return

    context.user_data["mode"] = query.data

    if query.data == "profile_pic":
        query.edit_message_text("یوزرنیم رو به صورت @username بفرست.")

    elif query.data == "last10":
        query.edit_message_text("یوزرنیم رو بفرست تا ۱۰ پست آخرشو دانلود کنم.")

    elif query.data == "post_link":
        query.edit_message_text("لینک پست یا ریل اینستاگرام رو بفرست.")

# ---------------- پیام‌ها ---------------- #

def handle_message(update, context):
    user_id = update.message.from_user.id
    if not is_member(context.bot, user_id):
        force_join(update)
        return

    text = update.message.text.strip()
    mode = context.user_data.get("mode", None)

    # دانلود پست/ریل
    if mode == "post_link" and "instagram.com" in text:
        update.message.reply_text("دارم دانلود می‌کنم...")
        clean_folder("post")

        try:
            shortcode = text.split("/")[-2]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target="post")
            send_single_post(update, "post")
        except:
            update.message.reply_text("نتونستم پست رو دانلود کنم!")

        clean_folder("post")
        return

    # دانلود عکس پروفایل
    if mode == "profile_pic" and text.startswith("@"):
        username = text[1:]
        update.message.reply_text("دارم عکس پروفایل رو دانلود می‌کنم...")

        clean_folder(username)

        try:
            L.download_profile(username, profile_pic_only=True)

            for f in os.listdir(username):
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    update.message.reply_photo(open(os.path.join(username, f), "rb"))
                    break

            update.message.reply_text("عکس پروفایل ارسال شد ✔️")
        except:
            update.message.reply_text("نتونستم عکس پروفایل رو دانلود کنم!")

        clean_folder(username)
        return

    # دانلود ۱۰ پست آخر
    if mode == "last10" and text.startswith("@"):
        username = text[1:]
        download_last10(update, username)
        return

    update.message.reply_text("اول از منو یکی از گزینه‌ها رو انتخاب کن /start")

# ---------------- اجرای ربات ---------------- #

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()- اجرای ربات ---------------- #

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
