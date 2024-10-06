import os
import csv
import time
import logging
import requests
from playwright.sync_api import sync_playwright

# Initialize logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
}

def create_directory(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        logging.debug(f"Creating directory: {path}")
        os.makedirs(path)
    else:
        logging.debug(f"Directory already exists: {path}")

def save_logs_to_csv(logs, file_path='download_log.csv'):
    """Save the logs to a CSV file."""
    try:
        logging.debug(f"Saving logs to CSV file: {file_path}")
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if csvfile.tell() == 0:
                # Write headers only if the file is empty
                writer.writerow(["Username", "Shortcode", "File Path", "Timestamp"])
            for log in logs:
                writer.writerow(log)
        logging.debug("Logs successfully saved to CSV.")
    except Exception as e:
        logging.error(f"Failed to save logs to CSV: {e}")

def download_video(video_url, save_dir, filename):
    """Download the video from the provided URL and save it to the specified directory."""
    try:
        logging.debug(f"Downloading video from {video_url}...")
        response = requests.get(video_url, headers=HEADERS, stream=True)
        if response.status_code == 200:
            file_path = os.path.join(save_dir, filename)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logging.debug(f"Video saved as {file_path}")
            return file_path
        else:
            logging.error(f"Failed to download video. Status code: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return None

def extract_video_url_from_page(page):
    """Extract the video URL from the current Instagram post page using Playwright."""
    logging.debug("Extracting video URL from page...")
    try:
        video_url = page.locator("meta[property='og:video']").get_attribute('content')
        if video_url:
            logging.debug(f"Video URL found: {video_url}")
            return video_url
        else:
            logging.error("Video URL not found on the post page.")
            return None
    except Exception as e:
        logging.error(f"Error extracting video URL: {e}")
        return None

def read_usernames_from_csv(file_path):
    """Read Instagram usernames from a CSV file."""
    usernames = []
    if not os.path.isfile(file_path):
        logging.error(f"CSV file does not exist: {file_path}")
        print(f"CSV file not found: {file_path}")
        return usernames

    try:
        logging.debug(f"Reading usernames from CSV file: {file_path}")
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:  # Ignore empty rows
                    usernames.append(row[0])
        logging.debug(f"Loaded usernames from CSV: {usernames}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        print(f"Error reading CSV file: {e}")
    return usernames

def download_user_videos(username, base_url="https://www.instagram.com"):
    """Download all videos from the given Instagram username using Playwright without login."""
    logs = []
    try:
        # Create a directory for the user to save videos
        base_dir = f"downloads/{username}"
        create_directory(base_dir)

        # Start Playwright and open browser
        with sync_playwright() as p:
            logging.debug(f"Launching browser for {username}...")
            browser = p.chromium.launch(headless=False)  # Change to headless=True if you want it to run headless
            context = browser.new_context()
            page = context.new_page()

            # Navigate to the user's profile page
            profile_url = f"{base_url}/{username}/"
            logging.debug(f"Navigating to profile page: {profile_url}")
            page.goto(profile_url)
            page.wait_for_timeout(5000)  # Wait for the page to fully load

            # Check if the profile page is accessible without login
            if "login" in page.url:
                logging.error(f"Profile page requires login for {username}. Skipping this user.")
                return []  # Skip this user if login is required

            # Scroll to load more posts (simulate user scroll)
            logging.debug(f"Scrolling to load more posts for {username}...")
            for _ in range(5):  # Adjust range for more/less posts
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(3000)

            # Find all post links on the page
            logging.debug("Extracting post links from the profile page...")
            post_links = page.locator('a[href*="/p/"]').evaluate_all('elements => elements.map(e => e.href)')
            logging.debug(f"Found {len(post_links)} post links for user {username}.")

            # Iterate over each post link and download video if available
            for post_url in post_links:
                logging.debug(f"Visiting post URL: {post_url}")
                page.goto(post_url)
                page.wait_for_timeout(3000)

                video_url = extract_video_url_from_page(page)
                if video_url:
                    # Use the shortcode from the URL as filename
                    shortcode = post_url.split('/')[-2]
                    filename = f"{shortcode}.mp4"
                    file_path = download_video(video_url, base_dir, filename)
                    if file_path:
                        logs.append([username, shortcode, file_path, time.strftime('%Y-%m-%d %H:%M:%S')])

            # Close the browser
            context.close()
            browser.close()
            logging.debug(f"Finished downloading videos for {username}. Total files: {len(logs)}")
    except Exception as e:
        logging.error(f"Error downloading videos for {username}: {e}")
        return []

    return logs  # Return the logs for this user to be written to the CSV file

if __name__ == "__main__":
    # CSV file containing the list of usernames
    csv_file = 'instagram_usernames.csv'

    # Read the target usernames from the CSV file
    usernames = read_usernames_from_csv(csv_file)

    if not usernames:
        print("No usernames found in CSV file.")
    else:
        # Initialize CSV log file
        log_file_path = 'download_log.csv'
        logging.debug(f"Log file path: {log_file_path}")

        # Loop through each username in the CSV file and download videos
        for username in usernames:
            logging.debug(f"Starting scraping for {username}.")
            print(f"Scraping {username}...")
            logs = download_user_videos(username)

            if logs:
                save_logs_to_csv(logs, file_path=log_file_path)  # Save logs to CSV file after scraping the user
            else:
                logging.error(f"Failed to scrape or log for {username}.")
