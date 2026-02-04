import os
import logging
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

API_KEY = "6560428021:5e6VTu2Pw3AHtzS@Api_ManagerRoBot"

def download_instagram(url: str):
    api_url = f"https://api.fast-creat.ir/instagram?apikey={API_KEY}&type=post2&url={url}"

    try:
        resp = requests.get(api_url)
        data = resp.json()

        # ساختار API:
        # { "status": true, "result": [ { "url": "..." } ] }

        if "result" in data and len(data["result"]) > 0:
            return data["result"][0]["url"]

        return None

    except Exception as e:
        print("Error:", e)
        return None


def start(update, context):
    update.message.reply_text(
        "سلام کیان 👋\nلینک پست یا ریل اینستاگرام رو بفرست تا برات دانلود کنم."
    )


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

        if "video" in content_type:
            update.message.reply_video(video=file_resp.content)
        elif "image" in content_type:
            update.message.reply_photo(photo=file_resp.content)
        else:
            update.message.reply_document(document=file_resp.content, filename="file")

    except Exception as e:
        logger.error(e)
        update.message.reply_text("خطایی در ارسال فایل رخ داد.")


def main():
    TOKEN = "8218272861:AAH_F2OHTJ-lYAEX9DmOa6Sf3Eq4r7LsV0Y" # از Railway می‌گیرد

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
