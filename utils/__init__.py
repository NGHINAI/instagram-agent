import os
import json
import time
from pathlib import Path
from config.logger import logger
from secret import gemini_api_keys

async def instagram_cookies_exist():
    """Check if Instagram cookies exist and are valid
    
    Returns:
        bool: True if cookies exist and are valid, False otherwise
    """
    try:
        cookies_path = "./cookies/Instagramcookies.json"
        # Check if the file exists
        if not os.path.exists(cookies_path):
            return False
        
        with open(cookies_path, "r") as f:
            cookies = json.load(f)

        # Find the sessionid cookie
        session_id_cookie = next((cookie for cookie in cookies if cookie.get('name') == 'sessionid'), None)

        # If sessionid cookie is not found, return false
        if not session_id_cookie:
            return False

        # Check if the sessionid cookie has expired
        current_timestamp = int(time.time())
        return session_id_cookie.get('expires') > current_timestamp
    except Exception as error:
        if isinstance(error, FileNotFoundError):
            # File does not exist
            logger.warning("Cookies file does not exist.")
            return False
        else:
            logger.error(f"Error checking cookies: {error}")
            return False

async def save_cookies(cookies_path, cookies):
    """Save cookies to a file
    
    Args:
        cookies_path: Path to save cookies to
        cookies: Cookies to save
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(cookies_path), exist_ok=True)
        
        with open(cookies_path, "w") as f:
            json.dump(cookies, f, indent=2)
        logger.info("Cookies saved successfully.")
    except Exception as error:
        logger.error(f"Error saving cookies: {error}")
        raise Exception("Failed to save cookies.")

async def load_cookies(cookies_path):
    """Load cookies from a file
    
    Args:
        cookies_path: Path to load cookies from
        
    Returns:
        list: Loaded cookies or empty list if file doesn't exist
    """
    try:
        # Check if the file exists
        if not os.path.exists(cookies_path):
            return []
        
        # Read and parse the cookies file
        with open(cookies_path, "r") as f:
            cookies = json.load(f)
            
        # Fix expiry format issues - convert to integer if it exists
        for cookie in cookies:
            if 'expires' in cookie and cookie['expires'] is not None:
                try:
                    cookie['expiry'] = int(cookie['expires'])
                    # Remove the original expires field to avoid conflicts
                    del cookie['expires']
                except (ValueError, TypeError):
                    # If conversion fails, remove the expires field
                    if 'expires' in cookie:
                        del cookie['expires']
                        
        return cookies
    except Exception as error:
        logger.error(f"Cookies file does not exist or cannot be read: {error}")
        return []

# Function to get the next API key in the list
def get_next_api_key(current_api_key_index):
    """Get the next API key in the list
    
    Args:
        current_api_key_index: Current API key index
        
    Returns:
        str: Next API key
    """
    current_api_key_index = (current_api_key_index + 1) % len(gemini_api_keys)  # Circular rotation of API keys
    return gemini_api_keys[current_api_key_index]

def setup_handle_error(error, context):
    """Handle setup errors
    
    Args:
        error: Error that occurred
        context: Context where the error occurred
    """
    if isinstance(error, Exception):
        if "net::ERR_ABORTED" in str(error):
            logger.error(f"ABORTION error occurred in {context}: {str(error)}")
        else:
            logger.error(f"Error in {context}: {str(error)}")
    else:
        logger.error(f"An unknown error occurred in {context}: {error}")

# Function to save tweet data to tweetData.json
async def save_tweet_data(tweet_content, image_url, time_tweeted):
    """Save tweet data to a file
    
    Args:
        tweet_content: Content of the tweet
        image_url: URL of the image in the tweet
        time_tweeted: Time the tweet was posted
    """
    tweet_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'tweetData.json')
    tweet_data = {
        'tweetContent': tweet_content,
        'imageUrl': image_url or None,
        'timeTweeted': time_tweeted,
    }

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(tweet_data_path), exist_ok=True)
        
        # Check if the file exists
        if os.path.exists(tweet_data_path):
            # Read the existing data
            with open(tweet_data_path, 'r') as f:
                data = json.load(f)
            # Append the new tweet data
            data.append(tweet_data)
            # Write the updated data back to the file
            with open(tweet_data_path, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # File does not exist, create it with the new tweet data
            with open(tweet_data_path, 'w') as f:
                json.dump([tweet_data], f, indent=2)
    except Exception as error:
        logger.error(f'Error saving tweet data: {error}')
        raise error

# Function to check if the first object's time in tweetData.json is more than 24 hours old and delete the file if necessary
async def check_and_delete_old_tweet_data():
    """Check and delete old tweet data"""
    tweet_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'tweetData.json')

    try:
        # Check if the file exists
        if not os.path.exists(tweet_data_path):
            return
            
        # Read the existing data
        with open(tweet_data_path, 'r') as f:
            data = json.load(f)

        if data and len(data) > 0:
            first_tweet_time = time.mktime(time.strptime(data[0]['timeTweeted'], '%Y-%m-%dT%H:%M:%S.%fZ'))
            current_time = time.time()
            time_difference = current_time - first_tweet_time

            # Check if the time difference is more than 24 hours (86400000 milliseconds)
            if time_difference > 86400:
                os.remove(tweet_data_path)
                logger.info('tweetData.json file deleted because the first tweet is more than 24 hours old.')
    except Exception as error:
        if not isinstance(error, FileNotFoundError):
            logger.error(f'Error checking tweet data: {error}')
            raise error

# Function to check if the tweetData.json file has 17 or more objects
async def can_send_tweet():
    """Check if a tweet can be sent
    
    Returns:
        bool: True if a tweet can be sent, False otherwise
    """
    tweet_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'tweetData.json')

    try:
        # Check if the file exists
        if not os.path.exists(tweet_data_path):
            return True
            
        # Read the existing data
        with open(tweet_data_path, 'r') as f:
            data = json.load(f)

        # Check if the file has 17 or more objects
        if len(data) >= 17:
            return False
        return True
    except Exception as error:
        if isinstance(error, FileNotFoundError):
            # File does not exist, so it's safe to send a tweet
            return True
        else:
            logger.error(f'Error checking tweet data: {error}')
            raise error