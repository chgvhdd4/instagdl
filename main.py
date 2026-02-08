import os
import shutil
import asyncio
import instaloader
from io import BytesIO

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---------------- BOT CONFIG ---------------- #
TOKEN = "8508847587:AAFgHA1RSi7TUlVOQ8gRtr-wiJQaaC04tM8"
CHANNEL_USERNAME = "@hamsterzk11"

# Instaloader instance
L = instaloader.Instaloader(
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)

# ---------------- UTILITIES ---------------- #

def clean_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)

async def send_single_post(update: Update, folder: str):
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
        await update.message.reply_video(open(video_file, "rb"), caption=caption_text[:1024])
    elif image_file:
        await update.message.reply_photo(open(image_file, "rb"), caption=caption_text[:1024])
    else:
        await update.message.reply_text("هیچ مدیایی پیدا نشد!")

# ---------------- CHANNEL CHECK ---------------- #

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return False

# ---------------- MAIN MENU ---------------- #

async def main_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("📸 دانلود عکس پروفایل", callback_data="profile_pic")],
        [InlineKeyboardButton("🔗 دانلود پست/ریل از لینک", callback_data="post_link")],
        [InlineKeyboardButton("📚 دانلود استوری‌ها", callback_data="stories")],
        [InlineKeyboardButton("🖼 دانلود ۱۰ پست آخر", callback_data="last10")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("یکی از گزینه‌ها رو انتخاب کن:", reply_markup=markup)
    else:
        await update.callback_query.message.reply_text("یکی از گزینه‌ها رو انتخاب کن:", reply_markup=markup)

# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_membership(user_id, context):
        invite = await context.bot.create_chat_invite_link(CHANNEL_USERNAME, member_limit=1)
        keyboard = [[InlineKeyboardButton("عضویت در کانال 📢", url=invite.invite_link)]]

        await update.message.reply_text(
            "برای استفاده از ربات **باید عضو کانال بشید** 👇",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    await main_menu(update)

# ---------------- PROFILE PIC (NEW METHOD) ---------------- #

async def download_profile_pic_v2(update: Update, username: str):
    try:
        profile = await asyncio.to_thread(instaloader.Profile.from_username, L.context, username)
        url = profile.profile_pic_url

        response = await asyncio.to_thread(L.context.requests.get, url, True)

        if response.status_code == 200:
            data = BytesIO(response.content)
            data.seek(0)
            await update.message.reply_photo(data, caption=f"عکس پروفایل @{username}")
        else:
            await update.message.reply_text("نتونستم عکس پروفایل رو دانلود کنم!")

    except instaloader.exceptions.ProfileNotExistsException:
        await update.message.reply_text(f"کاربر @{username} وجود ندارد ❌")

    except Exception as e:
        print(e)
        await update.message.reply_text("خطا رخ داد. ممکنه پروفایل پرایوت باشه یا محدودیت وجود داشته باشه.")

# ---------------- STORIES ---------------- #

async def download_stories(update: Update, username: str):
    await update.message.reply_text(f"دارم استوری‌های @{username} رو دانلود می‌کنم...")

    try:
        profile = await asyncio.to_thread(instaloader.Profile.from_username, L.context, username)
        stories = L.get_stories(userids=[profile.userid])

        found = False

        for story in stories:
            for item in story.get_items():
                found = True
                clean_folder("story")

                await asyncio.to_thread(L.download_storyitem, item, "story")

                for file in os.listdir("story"):
                    path = os.path.join("story", file)

                    if file.endswith(".mp4"):
                        await update.message.reply_video(open(path, "rb"))
                    elif file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                        await update.message.reply_photo(open(path, "rb"))

        clean_folder("story")

        if not found:
            await update.message.reply_text("این کاربر هیچ استوری فعالی ندارد ❌")
        else:
            await update.message.reply_text("همه استوری‌ها ارسال شد ✔️")

    except Exception as e:
        print(e)
        await update.message.reply_text("نتونستم استوری‌ها رو دانلود کنم!")

# ---------------- LAST 10 POSTS ---------------- #

async def download_last_10_posts(update: Update, username: str):
    profile = await asyncio.to_thread(instaloader.Profile.from_username, L.context, username)
    posts = list(profile.get_posts())[:10]

    await update.message.reply_text(f"دارم ۱۰ پست آخر @{username} رو دانلود می‌کنم...")

    for post in posts:
        clean_folder("post")
        await asyncio.to_thread(L.download_post, post, "post")
        await send_single_post(update, "post")

    clean_folder("post")
    await update.message.reply_text("۱۰ پست آخر ارسال شد ✔️")

# ---------------- BUTTON HANDLER ---------------- #

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["mode"] = query.data

    if query.data == "profile_pic":
        await query.edit_message_text("یوزرنیم رو به صورت @username بفرست.\n\n⬅️ /back")

    elif query.data == "stories":
        await query.edit_message_text("یوزرنیم رو بفرست تا استوری‌هاشو دانلود کنم.\n\n⬅️ /back")

    elif query.data == "post_link":
        await query.edit_message_text("لینک پست یا ریل رو بفرست.\n\n⬅️ /back")

    elif query.data == "last10":
        await query.edit_message_text("یوزرنیم رو بفرست تا ۱۰ پست آخر رو دانلود کنم.\n\n⬅️ /back")

# ---------------- MESSAGE HANDLER ---------------- #

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode")

    if text == "/back":
        await main_menu(update)
        return

    if mode == "profile_pic" and text.startswith("@"):
        username = text[1:]
        await update.message.reply_text("دارم دانلود می‌کنم...")
        await download_profile_pic_v2(update, username)
        return

    if mode == "stories" and text.startswith("@"):
        username = text[1:]
        await download_stories(update, username)
        return

    if mode == "post_link" and "instagram.com" in text:
        await update.message.reply_text("دارم دانلود می‌کنم...")
        clean_folder("post")

        try:
            shortcode = text.split("/")[-2]
            post = await asyncio.to_thread(instaloader.Post.from_shortcode, L.context, shortcode)
            await asyncio.to_thread(L.download_post, post, "post")
            await send_single_post(update, "post")
        except:
            await update.message.reply_text("نتونستم پست رو دانلود کنم!")

        clean_folder("post")
        return

    if mode == "last10" and text.startswith("@"):
        username = text[1:]
        await download_last_10_posts(update, username)
        return

    await update.message.reply_text("اول از منو یکی از گزینه‌ها رو انتخاب کن /start")

# ---------------- RUN BOT ---------------- #

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
