import os
import instaloader

L = instaloader.Instaloader(
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)

def clean_folder(path):
    if os.path.exists(path):
        import shutil
        shutil.rmtree(path)

def download_profile_pic(username, user_id):
    folder = f"profile_{user_id}"
    clean_folder(folder)
    os.makedirs(folder, exist_ok=True)

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        file_path = os.path.join(folder, "profile.jpg")

        # Use Instaloader's internal downloader (stable)
        L.context.get_and_write_raw(profile.profile_pic_url, file_path)

        return file_path

    except Exception as e:
        print("Profile download error:", e)
        return None

    finally:
        pass  # folder cleanup will be done in main bot
