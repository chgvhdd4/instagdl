import instaloader
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os

L = instaloader.Instaloader()

def start(update, context):
    update.message.reply_text("Send me an Instagram link or username.")

def download_profile(username):
    try:
        L.download_profile(username, profile_pic_only=False)
        return True
    except Exception as e:
        print(e)
        return False

def handle_message(update, context):
    text = update.message.text.strip()

    # If user sends a username
    if text.startswith("@"):
        username = text[1:]
        update.message.reply_text(f"Downloading profile: {username}")

        if download_profile(username):
            folder = username
            for file in os.listdir(folder):
                update.message.reply_document(open(f"{folder}/{file}", "rb"))
            update.message.reply_text("Done.")
        else:
            update.message.reply_text("Failed to download profile.")

    # If user sends a post/reel URL
    elif "instagram.com" in text:
        update.message.reply_text("Downloading post…")
        try:
            post = instaloader.Post.from_shortcode(L.context, text.split("/")[-2])
            L.download_post(post, target="post")

            for file in os.listdir("post"):
                update.message.reply_document(open(f"post/{file}", "rb"))

            update.message.reply_text("Done.")
        except Exception as e:
            print(e)
            update.message.reply_text("Failed to download post.")

def main():
    TOKEN = "8470724978:AAH1Z7eHKrbuw1feJ6TS_UwtgtIx3kHVJYE"

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
