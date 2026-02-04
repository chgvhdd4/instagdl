import os
import requests
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

API_KEY = "6560428021:5e6VTu2Pw3AHtzS@Api_ManagerRoBot"

def start(update, context):
    update.message.reply_text("سلام کیان 🌟\nلینک اینستاگرام رو بفرست تا دانلود کنم.")

def download_instagram(url):
    api = f"https://api.fast-creat.ir/instagram?apikey={API_KEY}&type=post2&url={url}"

    try:
        r = requests.get(api)
        data = r.json()

        # ساختار API:
        # { "status": true, "result": [ { "url": "..." } ] }

        if data.get("status") and "result" in data:
            return data["result"][0]["url"]

        return None

    except:
        return None

def handle(update, context):
    link = update.message.text.strip()

    if "instagram.com" not in link:
        update.message.reply_text("یه لینک معتبر اینستاگرام بده 🙂")
        return

    update.message.reply_text("در حال دانلود...")

    file_url = download_instagram(link)

    if not file_url:
        update.message.reply_text("نتونستم دانلود کنم 😕")
        return

    try:
        file_data = requests.get(file_url).content

        if file_url.endswith(".mp4"):
            update.message.reply_video(video=file_data)
        else:
            update.message.reply_photo(photo=file_data)

    except:
        update.message.reply_text("خطا در ارسال فایل ❌")

def main():
    TOKEN = "8470724978:AAH1Z7eHKrbuw1feJ6TS_UwtgtIx3kHVJYE"

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, handle))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
