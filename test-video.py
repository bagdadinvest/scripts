import instaloader
import os
import logging
import csv
import time
import random
import sys
import signal

# Initialize logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Instaloader instance
L = instaloader.Instaloader()

# Handle graceful shutdowns
def signal_handler(sig, frame):
    logging.info("Script terminated by user.")
    print("\nExiting gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

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

def download_user_videos(username):
    """Download only video posts from the given Instagram username."""
    logs = []
    try:
        logging.debug(f"Starting download for {username}. Creating directories...")

        # Create a directory for the user to save videos
        base_dir = f"downloads/{username}"
        create_directory(base_dir)

        # Get profile from username
        logging.debug(f"Fetching profile for {username}.")
        profile = instaloader.Profile.from_username(L.context, username)
        logging.debug(f"Profile fetched successfully for {username}.")

        # Download only video posts
        total_files = 0
        posts = profile.get_posts()
        for post in posts:
            # Filter and download only video posts
            if post.typename == 'GraphVideo':  # It's a video post
                logging.debug(f"Downloading video post {post.shortcode} for user {username}.")
                L.download_post(post, target=base_dir)

                # Log the downloaded video file data
                for file in os.listdir(base_dir):
                    if file.startswith(post.shortcode):
                        file_path = os.path.join(base_dir, file)
                        logs.append([username, post.shortcode, file_path, time.strftime('%Y-%m-%d %H:%M:%S')])
                        total_files += 1
                        logging.debug(f"Downloaded and logged video: {file_path}")
            else:
                logging.debug(f"Skipping non-video post {post.shortcode} for user {username}.")

        logging.debug(f"Finished downloading for {username}. Total video files: {total_files}")
    except instaloader.exceptions.TooManyRequestsException as e:
        logging.warning(f"Rate limited for {username}. Retrying in 10 minutes...")
        time.sleep(600)  # Sleep for 10 minutes before retrying
        return None
    except Exception as e:
        logging.error(f"Error downloading posts for {username}: {e}")
        return None

    return logs  # Return the logs for this user to be written to the CSV file

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

def get_user_confirmation(usernames):
    """Ask the user to confirm the list of usernames."""
    while True:
        print("The following usernames were loaded:")
        for username in usernames:
            print(f"- {username}")
        confirmation = input("Do you want to proceed with these usernames? (yes/no): ").lower()
        if confirmation in ['yes', 'no']:
            logging.debug(f"User confirmed: {confirmation}")
            return confirmation == 'yes'
        print("Invalid input. Please enter 'yes' or 'no'.")

def get_scraping_time_range():
    """Ask the user to input a valid time range for random sleep intervals."""
    while True:
        time_range = input("Enter the random scraping interval in minutes (format: min,max): ")
        try:
            min_time, max_time = map(int, time_range.split(","))
            if min_time < max_time:
                logging.debug(f"User provided valid time range: {min_time} to {max_time} minutes.")
                return min_time * 60, max_time * 60  # Convert minutes to seconds
            else:
                print("Error: The first number must be smaller than the second.")
        except ValueError:
            print("Error: Please enter two numbers separated by a comma.")

def countdown(seconds):
    """Display a countdown timer."""
    while seconds:
        mins, secs = divmod(seconds, 60)
        time_format = f'{mins:02d}:{secs:02d}'
        print(f"Next scrape in: {time_format}", end='\r')
        time.sleep(1)
        seconds -= 1
    print("\nScraping next account...")

if __name__ == "__main__":
    # Read usernames from CSV
    csv_file = 'instagram_usernames.csv'  # Replace with your actual file path
    logging.debug(f"Reading usernames from CSV file: {csv_file}")
    usernames = read_usernames_from_csv(csv_file)

    if not usernames:
        print("No usernames found in CSV file.")
    else:
        # Confirm usernames with the user
        if not get_user_confirmation(usernames):
            print("User canceled the operation.")
            exit()

        # Get the time range for random sleep intervals
        min_sleep_time, max_sleep_time = get_scraping_time_range()

        # Randomly shuffle usernames for each run
        random.shuffle(usernames)
        logging.debug(f"Shuffled usernames: {usernames}")
        print(f"Shuffled usernames: {usernames}")

        # Initialize CSV log file
        log_file_path = 'download_log.csv'  # Specify the log file path here
        logging.debug(f"Log file path: {log_file_path}")

        # Loop through each username
        for username in usernames:
            logging.debug(f"Starting scraping for {username}.")
            print(f"Scraping {username}...")
            logs = download_user_videos(username)

            if logs:
                save_logs_to_csv(logs, file_path=log_file_path)  # Save logs to CSV file after scraping the user
            else:
                logging.error(f"Failed to scrape or log for {username}.")

            # Add a random sleep time between each download (human-like behavior)
            sleep_time = random.randint(min_sleep_time, max_sleep_time)  # Random sleep within the user-provided range
            logging.debug(f"Waiting for {sleep_time} seconds before scraping the next account.")
            print(f"Waiting for {sleep_time // 60} minutes before scraping the next account...")

            # Countdown timer
