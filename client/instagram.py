import os
import time
import random
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from user_agents import parse as user_agent_parse
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from config.logger import logger
from secret import IGusername, IGpassword
from utils import instagram_cookies_exist, load_cookies, save_cookies
from agent import run_agent
from agent.schema import get_instagram_comment_schema

async def run_instagram():
    """Main function to run the Instagram bot"""
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
    
    # Set up proxy if needed
    # chrome_options.add_argument(f'--proxy-server=http://localhost:8000')
    
    # Create a new Chrome browser instance
    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Check if cookies exist and load them
        if await instagram_cookies_exist():
            logger.info("Loading cookies...:🚧")
            cookies = await load_cookies("./cookies/Instagramcookies.json")
            
            # Navigate to Instagram domain first (required to set cookies)
            browser.get("https://www.instagram.com")
            
            # Add cookies to browser
            for cookie in cookies:
                # Some cookie attributes might cause issues, so we only set the essential ones
                cookie_dict = {
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie['domain'],
                    'path': cookie['path']
                }
                # Add expiry if it exists
                if 'expires' in cookie:
                    cookie_dict['expiry'] = cookie['expires']
                    
                browser.add_cookie(cookie_dict)
        
        # Set a random PC user-agent
        user_agent = random.choice(["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                                   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"])
        logger.info(f"Using user-agent: {user_agent}")
        
        # Check if cookies are valid
        if await instagram_cookies_exist():
            logger.info("Cookies loaded, skipping login...")
            browser.get("https://www.instagram.com")
            
            # Check if login was successful by verifying page content
            try:
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/direct/inbox/')]")))                
                logger.info("Login verified with cookies.")
            except TimeoutException:
                logger.warning("Cookies invalid or expired. Logging in again...")
                await login_with_credentials(browser)
        else:
            # If no cookies are available, perform login with credentials
            await login_with_credentials(browser)
        
        # Take a screenshot after loading the page (with error handling)
        try:
            browser.save_screenshot("logged_in.png")
            logger.info("Screenshot saved successfully.")
        except Exception as screenshot_error:
            logger.warning(f"Could not save screenshot: {str(screenshot_error)}. Continuing anyway...")
            # Continue with the rest of the functionality
        
        # Navigate to the Instagram homepage
        browser.get("https://www.instagram.com/")
        
        # Interact with posts
        await interact_with_posts(browser)
        
    except Exception as e:
        logger.error(f"Error in Instagram automation: {str(e)}")
    finally:
        # Close the browser
        browser.quit()

async def login_with_credentials(browser):
    """Login to Instagram with credentials
    
    Args:
        browser: Selenium WebDriver instance
    """
    try:
        browser.get("https://www.instagram.com/accounts/login/")
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.NAME, "username")))
        
        # Fill out the login form
        username_input = browser.find_element(By.NAME, "username")
        password_input = browser.find_element(By.NAME, "password")
        
        username_input.send_keys(IGusername)
        password_input.send_keys(IGpassword)
        
        # Click login button
        login_button = browser.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        try:
            # Wait for potential 2FA challenge
            verification_code_input = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.NAME, "verificationCode")))
            
            logger.info("2FA code required. Please enter the code sent to your device:")
            
            # Get 2FA code from user input
            verification_code = input('Enter 2FA code: ').strip()
            
            if not verification_code:
                raise Exception("No 2FA code entered.")
            
            verification_code_input.send_keys(verification_code)
            confirm_button = browser.find_element(By.XPATH, "//button[contains(text(), 'Confirm')]")
            confirm_button.click()
            
            # Wait for navigation after submitting 2FA code
            WebDriverWait(browser, 15).until(
                EC.url_contains("instagram.com/"))
            logger.info("2FA code submitted successfully.")
            
        except TimeoutException:
            # If 2FA selector is not found within timeout, assume direct login
            logger.info("No 2FA prompt detected within timeout.")
            
            # Wait for navigation after login
            try:
                WebDriverWait(browser, 15).until(
                    EC.url_contains("instagram.com/"))
                logger.info("Navigation successful after login attempt.")
            except TimeoutException:
                logger.warning("Navigation after login attempt failed or timed out.")
                
                # Check if login actually succeeded despite navigation issues
                try:
                    inbox_link = browser.find_element(By.XPATH, "//a[contains(@href, '/direct/inbox/')]")
                    if not inbox_link:
                        logger.error("Login failed. Please check credentials or account status.")
                        raise Exception("Instagram login failed.")
                    logger.info("Login seems successful despite navigation timeout.")
                except NoSuchElementException:
                    logger.error("Login failed. Please check credentials or account status.")
                    raise Exception("Instagram login failed.")
        
        # Save cookies after successful login
        logger.info("Saving cookies...")
        cookies = browser.get_cookies()
        await save_cookies("./cookies/Instagramcookies.json", cookies)
        logger.info("Cookies saved successfully.")
        
    except Exception as error:
        logger.error(f"Error during login process: {str(error)}")
        raise error

async def interact_with_posts(browser):
    """Interact with Instagram posts
    
    Args:
        browser: Selenium WebDriver instance
    """
    post_index = 1  # Start with the first post
    max_posts = 50  # Limit to prevent infinite scrolling
    
    while post_index <= max_posts:
        try:
            # Wait for posts to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article")))
            
            # Get all posts
            posts = browser.find_elements(By.TAG_NAME, "article")
            
            # Check if we've reached the end of posts
            if post_index > len(posts):
                logger.info("No more posts found. Exiting loop...")
                break
            
            # Get the current post
            post = posts[post_index - 1]
            
            # --- Like Button Logic ---
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Find the like button within the post
                    like_button = post.find_element(By.XPATH, ".//div[contains(@class, '_aamw')]/button[.//*[name()='svg'][@aria-label='Like' or @aria-label='Unlike']]")
                    like_svg = like_button.find_element(By.XPATH, ".//svg[@aria-label='Like' or @aria-label='Unlike']")
                    
                    aria_label = like_svg.get_attribute("aria-label")
                    
                    if aria_label == "Like":
                        logger.info(f"Liking post {post_index} (attempt {retry_count + 1}/{max_retries})...")
                        like_button.click()
                        logger.info(f"Post {post_index} liked successfully.")
                        break
                    elif aria_label == "Unlike":
                        logger.info(f"Post {post_index} is already liked.")
                        break
                    else:
                        logger.warning(f"Like button SVG found but label is unexpected for post {post_index}: {aria_label}")
                        break
                except NoSuchElementException as error:
                    retry_count += 1
                    logger.warning(f"Like button not found for post {post_index} (attempt {retry_count}/{max_retries}): {str(error)}")
                    if retry_count < max_retries:
                        time.sleep(random.uniform(2, 5))
                        browser.execute_script("window.scrollBy(0, 100);")  # Small scroll to potentially reveal button
                    else:
                        logger.error(f"Failed to find like button for post {post_index} after {max_retries} attempts")
                        continue
                except Exception as error:
                    retry_count += 1
                    logger.warning(f"Attempt {retry_count}/{max_retries} failed for post {post_index}: {str(error)}")
                    if retry_count < max_retries:
                        time.sleep(random.uniform(2, 5))
                    else:
                        logger.error(f"Failed to like post {post_index} after {max_retries} attempts: {str(error)}")
                        continue
            
            # --- Comment Logic ---
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Find the comment button
                    comment_button = post.find_element(By.XPATH, ".//div[contains(@class, '_aamx')]/button[.//*[name()='svg'][@aria-label='Comment']]")
                    comment_button.click()
                    
                    # Wait for comment box to appear
                    WebDriverWait(browser, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@role, 'textbox')][@aria-label='Add a comment…']")))
                    
                    # Get post content for context
                    try:
                        post_text = post.find_element(By.XPATH, ".//div[contains(@class, '_a9zs')]")
                        post_content = post_text.text
                    except:
                        post_content = "No text content found in this post."
                    
                    # Generate comment using AI
                    prompt = f"Generate an engaging comment for this Instagram post. Post content: {post_content}"
                    logger.info(f"Generating comment for post {post_index} (attempt {retry_count + 1}/{max_retries})...")
                    
                    schema = get_instagram_comment_schema()
                    comment_data = await run_agent(schema, prompt)
                    
                    if comment_data and isinstance(comment_data, list) and len(comment_data) > 0:
                        # Get the first comment from the list
                        comment = comment_data[0].get('comment', '')
                        
                        # Sanitize comment (remove quotes, etc.)
                        comment = comment.strip().replace('"', '')
                        
                        if comment:
                            # Find comment textarea and post button
                            comment_textarea = browser.find_element(By.XPATH, "//textarea[@aria-label='Add a comment…' or @placeholder='Add a comment…']")
                            
                            logger.info(f"Typing comment on post {post_index}...")
                            comment_textarea.click()
                            comment_textarea.clear()
                            comment_textarea.send_keys(comment)
                            
                            # Find and click post button
                            post_button = WebDriverWait(browser, 5).until(
                                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Post') and @role='button']")))                        
                            
                            logger.info(f"Posting comment on post {post_index}...")
                            post_button.click()
                            
                            # Verify comment was posted
                            try:
                                WebDriverWait(browser, 5).until(
                                    EC.presence_of_element_located((By.XPATH, f"//div[contains(text(), '{comment[:20]}')]")))
                                logger.info(f"Comment posted on post {post_index} successfully.")
                                break
                            except TimeoutException:
                                logger.warning(f"Could not verify comment was posted for post {post_index}")
                                continue
                        else:
                            logger.warning(f"Generated comment for post {post_index} was empty after sanitization.")
                            break
                    else:
                        logger.warning(f"Failed to generate a valid comment for post {post_index}. Received: {json.dumps(comment_data)}")
                        break
                except NoSuchElementException as error:
                    retry_count += 1
                    logger.warning(f"Comment button not found for post {post_index} (attempt {retry_count}/{max_retries}): {str(error)}")
                    if retry_count < max_retries:
                        time.sleep(random.uniform(2, 5))
                        browser.execute_script("window.scrollBy(0, 100);")
                    else:
                        logger.error(f"Failed to find comment button for post {post_index} after {max_retries} attempts")
                        continue
                except Exception as error:
                    retry_count += 1
                    logger.warning(f"Attempt {retry_count}/{max_retries} failed for post {post_index}: {str(error)}")
                    if retry_count < max_retries:
                        time.sleep(random.uniform(2, 5))
                    else:
                        logger.error(f"Failed to comment on post {post_index} after {max_retries} attempts: {str(error)}")
                        continue
            
            # Scroll to the next post
            browser.execute_script("arguments[0].scrollIntoView();", posts[min(post_index, len(posts) - 1)])
            
            # Random delay between 3-7 seconds
            delay = random.uniform(3000, 7000)
            logger.info(f"Waiting {(delay / 1000):.1f} seconds before scrolling to the next post...")
            time.sleep(delay / 1000)
            
            # Increment post index
            post_index += 1
            
        except Exception as error:
            logger.error(f"Error interacting with post {post_index}: {str(error)}")
            # Save screenshot of failed interaction for debugging
            try:
                browser.save_screenshot(f"error_post_{post_index}.png")
                logger.info(f"Saved screenshot of failed post interaction: error_post_{post_index}.png")
            except Exception as screenshot_error:
                logger.warning(f"Could not save screenshot of failed interaction: {str(screenshot_error)}")
            
            # Random delay before retrying or moving to next post
            time.sleep(random.uniform(3, 7))
            post_index += 1  # Move to the next post even if there's an error