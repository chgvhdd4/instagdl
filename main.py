import os
import shutil
import instaloader
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Create Instaloader instance
L = instaloader.Instaloader(
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)

def start(update, context):
    update.message.reply_text("Send me an Instagram link or @username.")

def clean_folder(path):
    if os.path.exists(path):
        shutil.rmtree(path)

def send_instagram_post(update, folder):
    caption_text = ""
    media_files = []

    # Scan folder for media
    for file in sorted(os.listdir(folder)):
        path = os.path.join(folder, file)

        if file.endswith(".txt"):
            caption_text = open(path, "r", encoding="utf-8").read()

        elif file.endswith(".mp4") or file.endswith(".jpg"):
            media_files.append(path)

    # Send carousel items
    first = True
    for media in media_files:
        if media.endswith(".mp4"):
            update.message.reply_video(
                video=open(media, "rb"),
                caption=caption_text[:1024] if first else None
            )
        else:
            update.message.reply_photo(
                photo=open(media, "rb"),
                caption=caption_text[:1024] if first else None
            )

        first = False  # caption only on first item

    if not media_files:
        update.message.reply_text("No media found in this post.")

def handle_message(update, context):
    text = update.message.text.strip()

    # Handle Instagram post/reel URL
    if "instagram.com" in text:
        update.message.reply_text("Downloading…")

        clean_folder("post")

        try:
            shortcode = text.split("/")[-2]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target="post")

            send_instagram_post(update, "post")

        except Exception as e:
            print(e)
            update.message.reply_text("Failed to download post.")

        clean_folder("post")
        return

    # Handle profile download
    if text.startswith("@"):
        username = text[1:]
        update.message.reply_text(f"Downloading profile: {username}")

        clean_folder(username)

        try:
            L.download_profile(username, profile_pic_only=False)

            # Send only profile picture
            for file in os.listdir(username):
                if file.endswith(".jpg"):
                    update.message.reply_photo(open(f"{username}/{file}", "rb"))
                    break

            update.message.reply_text("Profile picture sent.")

        except Exception as e:
            print(e)
            update.message.reply_text("Failed to download profile.")

        clean_folder(username)
        return

def main():
    TOKEN = "8508847587:AAFgHA1RSi7TUlVOQ8gRtr-wiJQaaC04tM8"

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
