import pandas as pd
import instaloader
import os
from pathlib import Path

# Debugging helper function
def debug(message):
    print(f"[DEBUG] {message}")

# Function to create necessary directories for storing scraped content
def setup_directories():
    debug("Setting up directories for scraped content")
    base_folder = "scraped_content"
    instagram_folder = os.path.join(base_folder, "Instagram")
    facebook_folder = os.path.join(base_folder, "Facebook")

    Path(instagram_folder).mkdir(parents=True, exist_ok=True)
    Path(facebook_folder).mkdir(parents=True, exist_ok=True)
    
    return instagram_folder, facebook_folder

# Function to read the input Excel file
def read_input_file(file_path):
    debug(f"Reading input file: {file_path}")
    df = pd.read_excel(file_path)
    return df

# Function to write output data to Excel
def write_output_file(output_path, data):
    debug(f"Writing output file: {output_path}")
    df = pd.DataFrame(data, columns=['URL', 'Image Path', 'Video Path', 'Caption'])
    df.to_excel(output_path, index=False)

# Function to download Instagram post using Instaloader
def download_instagram_post(url, username, password, session_cookie, instagram_folder):
    debug(f"Downloading Instagram post: {url}")
    L = instaloader.Instaloader()
    # Load session from cookie file
    try:
        L.load_session_from_file(username, session_cookie)
        debug(f"Loaded session for Instagram user: {username}")
    except Exception as e:
        debug(f"Failed to load session, logging in: {e}")
        L.login(username, password)
        L.save_session_to_file(session_cookie)
        debug("Session saved")

    # Process the Instagram URL (extract post content)
    try:
        post_shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, post_shortcode)
        image_path, video_path, caption = None, None, None

        if post.is_video:
            video_path = os.path.join(instagram_folder, f"{post_shortcode}.mp4")
            L.download_post(post, target=instagram_folder)
            debug(f"Video downloaded: {video_path}")
        else:
            image_path = os.path.join(instagram_folder, f"{post_shortcode}.jpg")
            L.download_post(post, target=instagram_folder)
            debug(f"Image downloaded: {image_path}")
        
        caption = post.caption if post.caption else "No caption"
        debug(f"Caption: {caption}")

        return image_path, video_path, caption

    except Exception as e:
        debug(f"Failed to download Instagram post: {e}")
        return None, None, None

# Placeholder function for Facebook post scraping
def download_facebook_post(url, username, password, session_cookie, facebook_folder):
    debug(f"Downloading Facebook post: {url}")
    # Facebook scraping logic would go here (possibly using cookies, user session, etc.)
    # For now, returning dummy data
    return None, None, "Facebook scraping not implemented"

# Main function to process URLs from Excel file
def process_urls(input_file, output_file, instagram_username, instagram_password, instagram_cookie, facebook_username, facebook_password, facebook_cookie):
    instagram_folder, facebook_folder = setup_directories()
    df = read_input_file(input_file)
    output_data = []

    for index, row in df.iterrows():
        url = row['URL']
        debug(f"Processing URL: {url}")
        image_path, video_path, caption = None, None, None
        
        if "instagram.com" in url:
            image_path, video_path, caption = download_instagram_post(url, instagram_username, instagram_password, instagram_cookie, instagram_folder)
        elif "facebook.com" in url:
            image_path, video_path, caption = download_facebook_post(url, facebook_username, facebook_password, facebook_cookie, facebook_folder)
        else:
            debug(f"Unknown URL type: {url}")

        output_data.append([url, image_path, video_path, caption])

    write_output_file(output_file, output_data)
    debug("Processing complete")

# Example of calling the main function (these values would be provided in practice)
# process_urls("input.xlsx", "output.xlsx", "instagram_user", "instagram_pass", "instagram_session", "facebook_user", "facebook_pass", "facebook_session")
