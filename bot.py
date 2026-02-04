import os
import logging
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import re
import json
# ---------------- تنظیمات لاگ ----------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------- تابع دانلود از اینستاگرام ----------------
def download_instagram(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        # دریافت HTML صفحه
        html = requests.get(url, headers=headers).text

        # پیدا کردن JSON داخلی اینستاگرام
        json_data = re.search(r"window\._sharedData = (.*?);</script>", html)

        if not json_data:
            return None

        data = json.loads(json_data.group(1))

        # مسیر رسیدن به لینک ویدیو/عکس
        media = data["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"]

        # اگر ویدیو بود
        if media.get("is_video"):
            return media["video_url"]

        # اگر عکس بود
        return media["display_url"]

    except Exception as e:
        print("Error:", e)
        return None

# ---------------- هندلر /start ----------------
def start(update, context):
    update.message.reply_text(
        "سلام کیان 👋\nلینک پست، ریل یا عکس اینستاگرام رو بفرست تا برات دانلود کنم."
    )

# ---------------- هندلر پیام‌ها ----------------
def handle_message(update, context):
    text = update.message.text.strip()

    if "instagram.com" not in text:
        update.message.reply_text("یه لینک معتبر اینستاگرام بفرست 🙂")
        return

    update.message.reply_text("در حال پردازش لینک...")

    download_url = download_instagram(text)

    if not download_url:
        update.message.reply_text("نتونستم دانلود کنم. لینک دیگه امتحان کن.")
        return

    try:
        file_resp = requests.get(download_url, stream=True)
        file_resp.raise_for_status()

        content_type = file_resp.headers.get("Content-Type", "")

        # ارسال ویدیو
        if "video" in content_type:
            update.message.reply_video(video=file_resp.content)

        # ارسال عکس
        elif "image" in content_type:
            update.message.reply_photo(photo=file_resp.content)

        # ارسال فایل ناشناخته
        else:
            update.message.reply_document(document=file_resp.content, filename="file")

    except Exception as e:
        logger.error(e)
        update.message.reply_text("خطایی در ارسال فایل رخ داد.")

# ---------------- تابع اصلی ----------------
def main():
    TOKEN = "8218272861:AAH_F2OHTJ-lYAEX9DmOa6Sf3Eq4r7LsV0Y"  # توکن رو از Railway می‌گیره

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
