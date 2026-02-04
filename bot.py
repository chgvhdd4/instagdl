import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

API_KEY = "6560428021:5e6VTu2Pw3AHtzS@Api_ManagerRoBot"
API_URL = "https://api.fast-creat.ir/instagram"

BOT_TOKEN = "8218272861:AAH_F2OHTJ-lYAEX9DmOa6Sf3Eq4r7LsV0Y"   # ← put your bot token here


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me an Instagram post URL and I’ll download it for you.")


async def download_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "instagram.com" not in url:
        await update.message.reply_text("Please send a valid Instagram post URL.")
        return

    await update.message.reply_text("Downloading...")

    api_link = f"{API_URL}?apikey={API_KEY}&type=post2&url={url}"

    try:
        response = requests.get(api_link).json()

        if response.get("status") != "ok":
            await update.message.reply_text("Error downloading the post.")
            return

        media_list = response.get("result", [])

        for media in media_list:
            media_url = media.get("url")

            if media_url.endswith(".mp4"):
                await update.message.reply_video(media_url)
            else:
                await update.message.reply_photo(media_url)

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram))

    app.run_polling()


if __name__ == "__main__":
    main()
