import praw
import time
import os
import threading  # Import the threading module

# --- Configuration ---
SUBREDDIT_TO_MONITOR = "brighton"
TRIGGER_WORDS = ["laines", "south lanes", "north lanes"]
REPLY_MESSAGE = """
Hello! It looks like you may have confused North Laine and The Lanes.

The two areas are distinct and though similar sounding, bear no relation beyond their proximity.

The Lanes is the area between North Street and the seafront and North Laine is the area the other side of North Street, going back to Trafalgar Street. 

No disrespect meant. I am a pedantic bot.
***
^(I am a bot. Beep boop) 
"""
REPLIED_TO_FILE = "replied_to.txt"
# --- End Configuration ---

def load_replied_to():
    """Loads the set of already replied-to IDs from the file."""
    if not os.path.exists(REPLIED_TO_FILE):
        return set()
    with open(REPLIED_TO_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_replied_to(replied_to_set, item_id):
    """Adds a new ID to the set and saves it to the file."""
    replied_to_set.add(item_id)
    with open(REPLIED_TO_FILE, "a") as f:
        f.write(item_id + "\n")

def process_submissions(reddit, subreddit, replied_to):
    """Monitors and processes new submissions."""
    try:
        for submission in subreddit.stream.submissions(skip_existing=True):
            print(f"\nFound new submission: {submission.id} - {submission.title}")

            if submission.id in replied_to:
                print(f"Already replied to submission {submission.id}. Skipping.")
                continue

            text_to_check = submission.title + " " + (submission.selftext if submission.selftext else "")
            text_to_check_lower = text_to_check.lower()

            triggered = False
            for trigger in TRIGGER_WORDS:
                if trigger in text_to_check_lower:
                    print(f"  -> Trigger word '{trigger}' found in submission {submission.id}!")
                    triggered = True
                    break

            if triggered:
                try:
                    print(f"  Replying to submission {submission.id}...")
                    submission.reply(REPLY_MESSAGE)
                    print("  Reply successful!")
                    save_replied_to(replied_to, submission.id)
                    # time.sleep(10)
                except praw.exceptions.RedditAPIException as e:
                    print(f"  Reddit API Exception while replying to {submission.id}: {e}")
                    if "RATELIMIT" in str(e):
                        print("  Rate limit hit. Sleeping...")
                        time.sleep(60)
                except Exception as e:
                    print(f"  An unexpected error occurred while replying to {submission.id}: {e}")
            else:
                print(f"  No trigger words found in submission {submission.id}.")

    except praw.exceptions.PRAWException as e:
        print(f"PRAW Exception while monitoring submissions: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while monitoring submissions: {e}")

def process_comments(reddit, subreddit, replied_to):
    """Monitors and processes new comments."""

    try:
        for comment in subreddit.stream.comments(skip_existing=True):
            print(f"\nFound new comment: {comment.id} by u/{comment.author}")

            if comment.id in replied_to or comment.submission.id in replied_to or comment.author == reddit.user.me():
                if comment.author == reddit.user.me():
                    print(f"Comment {comment.id} is by myself. Skipping.")
                else:
                    print(f"Already replied to comment {comment.id} or its submission. Skipping.")
                continue

            text_to_check_lower = comment.body.lower()

            triggered = False
            for trigger in TRIGGER_WORDS:
                if trigger in text_to_check_lower:
                    print(f"  -> Trigger word '{trigger}' found in comment {comment.id}!")
                    triggered = True
                    break

            if triggered:
                try:
                    print(f"  Replying to comment {comment.id}...")
                    comment.reply(REPLY_MESSAGE)
                    print("  Reply successful!")
                    save_replied_to(replied_to, comment.id)
                    # time.sleep(10)
                except praw.exceptions.RedditAPIException as e:
                    print(f"  Reddit API Exception while replying to {comment.id}: {e}")
                    if "RATELIMIT" in str(e):
                        print("  Rate limit hit. Sleeping...")
                        time.sleep(60)
                except Exception as e:
                    print(f"  An unexpected error occurred while replying to {comment.id}: {e}")
            else:
                print(f"  No trigger words found in comment {comment.id}.")

    except praw.exceptions.PRAWException as e:
        print(f"PRAW Exception while monitoring comments: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while monitoring comments: {e}")

def main():
    print("Connecting to Reddit...")
    try:
        reddit = praw.Reddit("bot1")
        print(f"Successfully connected as user: {reddit.user.me()}")
    except Exception as e:
        print(f"Error connecting to Reddit: {e}")
        print("Please check your praw.ini file and internet connection.")
        time.sleep(60)  # Wait before the main loop tries again
        return

    subreddit = reddit.subreddit(SUBREDDIT_TO_MONITOR)
    replied_to = load_replied_to()
    print(f"Loaded {len(replied_to)} previously replied-to IDs.")
    print(f"Monitoring r/{SUBREDDIT_TO_MONITOR} for trigger words: {TRIGGER_WORDS}")

    # Create and start threads for submissions and comments
    submission_thread = threading.Thread(target=process_submissions, args=(reddit, subreddit, replied_to))
    comment_thread = threading.Thread(target=process_comments, args=(reddit, subreddit, replied_to))

    submission_thread.start()
    comment_thread.start()

    # Keep the main thread alive to handle exceptions and keep the program running
    while True:
        time.sleep(60)  # Check every minute (or adjust as needed)
        if not submission_thread.is_alive():
            print("Submission thread has died. Restarting...")
            submission_thread = threading.Thread(target=process_submissions, args=(reddit, subreddit, replied_to))
            submission_thread.start()
        if not comment_thread.is_alive():
            print("Comment thread has died. Restarting...")
            comment_thread = threading.Thread(target=process_comments, args=(reddit, subreddit, replied_to))
            comment_thread.start()

if __name__ == "__main__":
    while True:
        try:
            main()
        except KeyboardInterrupt:
            print("\nBot stopped manually.")
            break
        except Exception as e:
            print(f"\nCRITICAL ERROR in main loop: {e}. Restarting in 60 seconds...")
            time.sleep(60)