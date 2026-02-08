import os
import shutil
import threading
import instaloader
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

TOKEN = "8508847587:AAFgHA1RSi7TUlVOQ8gRtr-wiJQaaC04tM8"
CHANNEL_USERNAME = "@hamsterzk11"

# ---------------- INSTALOADER INSTANCE ---------------- #
L = instaloader.Instaloader(
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)

try:
    L.load_session_from_file("session")
    print("Session loaded successfully.")
except:
    print("⚠ No session found. Story download may fail.")

# ---------------- UTILITIES ---------------- #
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

# ---------------- CHANNEL CHECK ---------------- #
def check_membership(user_id, bot):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return False

# ---------------- MAIN MENU ---------------- #
def main_menu(update):
    keyboard = [
        [InlineKeyboardButton("📸 دانلود عکس پروفایل", callback_data="profile_pic")],
        [InlineKeyboardButton("🔗 دانلود پست/ریل از لینک", callback_data="post_link")],
        [InlineKeyboardButton("📚 دانلود استوری‌ها", callback_data="stories")],
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

    if not check_membership(user_id, bot):
        invite = bot.create_chat_invite_link(CHANNEL_USERNAME, member_limit=1)
        keyboard = [[InlineKeyboardButton("عضویت در کانال 📢", url=invite.invite_link)]]
        update.message.reply_text(
            "برای استفاده از ربات **باید عضو کانال بشید** 👇",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    main_menu(update)

# ---------------- NEW PROFILE PIC FUNCTION (NO INSTALOADER) ---------------- #
def download_profile_pic(username, user_id):
    try:
        folder = f"profile_{user_id}"

        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder)

        url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
        headers = {"User-Agent": "Mozilla/5.0"}

        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return None

        data = r.json()
        pic_url = data["graphql"]["user"]["profile_pic_url_hd"]

        img_data = requests.get(pic_url, headers=headers).content
        file_path = f"{folder}/{username}.jpg"

        with open(file_path, "wb") as f:
            f.write(img_data)

        return file_path

    except Exception as e:
        print("Profile picture error:", e)
        return None

# ---------------- STORY DOWNLOADER (unchanged) ---------------- #
def download_stories(update, username):
    update.message.reply_text(f"دارم استوری‌های @{username} رو چک می‌کنم...")

    result = {"done": False}

    def run_story_download():
        try:
            profile = instaloader.Profile.from_username(L.context, username)
            user_id = profile.userid

            stories = L.get_stories(userids=[user_id])
            found = False

            for story in stories:
                for item in story.get_items():
                    found = True
                    clean_folder("story")
                    L.download_storyitem(item, target="story")

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
            print("Story error:", e)
            update.message.reply_text("نتونستم استوری‌ها رو دانلود کنم ❌")

        result["done"] = True

    threading.Thread(target=run_story_download).start()

# ---------------- LAST 10 POSTS (unchanged) ---------------- #
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

    if query.data == "profile_pic":
        query.edit_message_text("یوزرنیم رو به صورت @username بفرست.\n\n⬅️ /back")

    elif query.data == "stories":
        query.edit_message_text("یوزرنیم رو به صورت @username بفرست تا استوری‌هاشو دانلود کنم.\n\n⬅️ /back")

    elif query.data == "post_link":
        query.edit_message_text("لینک پست یا ریل اینستاگرام رو بفرست.\n\n⬅️ /back")

    elif query.data == "last10":
        query.edit_message_text("یوزرنیم رو به صورت @username بفرست تا ۱۰ پست آخر رو دانلود کنم.\n\n⬅️ /back")

# ---------------- MESSAGE HANDLER ---------------- #
def handle_message(update, context):
    text = update.message.text.strip()
    mode = context.user_data.get("mode", None)

    if text == "/back":
        main_menu(update)
        return

    # PROFILE PIC
    if mode == "profile_pic" and text.startswith("@"):
        username = text[1:]
        update.message.reply_text(f"دارم عکس پروفایل @{username} رو دانلود می‌کنم...")

        file_path = download_profile_pic(username, update.effective_user.id)

        if file_path:
            update.message.reply_photo(open(file_path, "rb"))
            update.message.reply_text("عکس پروفایل ارسال شد ✔️")
        else:
            update.message.reply_text("نتونستم عکس پروفایل رو دانلود کنم ❌")

        clean_folder(f"profile_{update.effective_user.id}")
        return

    # STORIES
    if mode == "stories" and text.startswith("@"):
        username = text[1:]
        download_stories(update, username)
        return

    # POST FROM LINK
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

    # LAST 10 POSTS
    if mode == "last10" and text.startswith("@"):
        username = text[1:]
        download_last_10_posts(update, username)
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
