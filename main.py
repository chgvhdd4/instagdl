import os
import shutil
import instaloader
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from profile_downloader import download_profile_pic, clean_folder

# ---------------- BOT CONFIG ---------------- #
TOKEN = "8508847587:AAFgHA1RSi7TUlVOQ8gRtr-wiJQaaC04tM8"
CHANNEL_USERNAME = "@hamsterzk11"

# Instaloader instance
L = instaloader.Instaloader(
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)

# ---------------- CHANNEL CHECK ---------------- #

def check_membership(user_id, bot):
    """Synchronous membership check for PTB v13."""
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
        return False
    except Exception as e:
        print("Membership check error:", e)
        return False

# ---------------- MAIN MENU ---------------- #

def main_menu(update):
    keyboard = [
        [InlineKeyboardButton("📸 دانلود عکس پروفایل", callback_data="profile_pic")],
        [InlineKeyboardButton("🔗 دانلود پست/ریل از لینک", callback_data="post_link")],
        [InlineKeyboardButton("📚 دانلود استوری‌ها", callback_data="stories")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        update.message.reply_text("یکی از گزینه‌ها رو انتخاب کن:", reply_markup=reply_markup)
    else:
        update.callback_query.message.reply_text("یکی از گزینه‌ها رو انتخاب کن:", reply_markup=reply_markup)

# ---------------- START COMMAND ---------------- #

def start(update, context):
    user_id = update.effective_user.id
    bot = context.bot

    # Check membership
    if not check_membership(user_id, bot):
        # Create invite link
        invite = bot.create_chat_invite_link(CHANNEL_USERNAME, member_limit=1)
        invite_link = invite.invite_link

        # Button for joining
        keyboard = [
            [InlineKeyboardButton("عضویت در کانال 📢", url=invite_link)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(
            "برای استفاده از ربات **باید عضو کانال بشید** 👇",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # If member → show menu
    main_menu(update)

# ---------------- TOOLS ---------------- #
def download_profile_pic_v2(update, username):
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        profile_pic_url = profile.profile_pic_url

        # Download image bytes
        response = L.context.requests.get(profile_pic_url, stream=True)

        if response.status_code == 200:
            from io import BytesIO
            pic_data = BytesIO(response.content)
            pic_data.seek(0)

            update.message.reply_photo(pic_data, caption=f"عکس پروفایل @{username}")
        else:
            update.message.reply_text("نتونستم عکس پروفایل رو دانلود کنم!")

    except instaloader.exceptions.ProfileNotExistsException:
        update.message.reply_text(f"کاربر @{username} وجود ندارد ❌")

    except Exception as e:
        print(e)
        update.message.reply_text("خطا رخ داد. ممکنه پروفایل پرایوت باشه یا محدودیت وجود داشته باشه.")
        
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

# ---------------- DOWNLOAD LAST 10 POSTS ---------------- #

def download_last_10_posts(update, username):
    profile = instaloader.Profile.from_username(L.context, username)
    posts = list(profile.get_posts())[:10]

    update.message.reply_text(f"دارم ۱۰ پست آخر @{username} رو دانلود می‌کنم...")

    for post in posts:
        clean_folder("post")
        L.download_post(post, target="post")
        send_single_post(update, "post")

    clean_folder("post")
    update.message.reply_text("۱۰ پست آخر ارسال شد ✔️")

# ---------------- BUTTON HANDLER ---------------- #

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

    elif query.data == "stories":
        query.edit_message_text("یوزرنیم رو به صورت @usernameبفرست تا استوری‌هاشو دانلود کنم.\n\n⬅️ برای برگشت /back رو بفرست")
    
    elif query.data == "post_link":
        query.edit_message_text("لینک پست یا ریل اینستاگرام رو بفرست.\n\n⬅️ برای برگشت /back رو بفرست")

# ---------------- MESSAGE HANDLER ---------------- #
def download_stories(update, username):
    update.message.reply_text(f"دارم استوری‌های @{username} رو دانلود می‌کنم...")

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        stories = L.get_stories(userids=[profile.userid])

        found = False

        for story in stories:
            for item in story.get_items():
                found = True
                clean_folder("story")
                L.download_storyitem(item, target="story")

                # Send story media
                for file in os.listdir("story"):
                    path = os.path.join("story", file)

                    if file.endswith(".mp4"):
                        update.message.reply_video(open(path, "rb"))
                    elif file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                        update.message.reply_photo(open(path, "rb"))

        clean_folder("story")

        if not found:
            update.message.reply_text("این کاربر هیچ استوری فعالی ندارد ❌")
        else:
            update.message.reply_text("همه استوری‌ها ارسال شد ✔️")

    except Exception as e:
        print(e)
        update.message.reply_text("نتونستم استوری‌ها رو دانلود کنم!")
        
def handle_message(update, context):
    text = update.message.text.strip()
    mode = context.user_data.get("mode", None)

    # Back to menu
    if text == "/back":
        main_menu(update)
        return

    # Download post from link
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
    # Download stories
    if mode == "stories" and text.startswith("@"):
        username = text[1:]
        try:
            download_stories(update, username)
        except Exception as e:
            print(e)
            update.message.reply_text("نتونستم استوری‌ها رو دانلود کنم!")
        return

    # Download profile picture
    if mode == "profile_pic" and text.startswith("@"):
        username = text[1:]
        update.message.reply_text(f"دارم عکس پروفایل @{username} رو دانلود می‌کنم...")
        download_profile_pic_v2(update, username)
        return

    # Download last 10 posts
    if mode == "last10" and text.startswith("@"):
        username = text[1:]
        try:
            download_last_10_posts(update, username)
        except Exception as e:
            print(e)
            update.message.reply_text("نتونستم پست‌ها رو دانلود کنم!")
        return
    

    update.message.reply_text("اول از منو یکی از گزینه‌ها رو انتخاب کن /start")
# ---------------- RUN BOT ---------------- #

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
    
