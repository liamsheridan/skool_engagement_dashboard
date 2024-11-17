import time
import pandas as pd
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta
from pathlib import Path
import re


def login_and_get_driver():
    """Login to Skool and retrieve necessary cookies."""
    # Load environment variables
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)

    # Debug print
    print("Environment file loaded.")

    # Get credentials from the environment
    skool_email = os.getenv("SKOOL_EMAIL")
    skool_password = os.getenv("SKOOL_PASSWORD")

    # Validate credentials
    if not skool_email or not skool_password:
        raise ValueError(
            "SKOOL_EMAIL or SKOOL_PASSWORD not found in environment variables.")

    try:
        print("Logging into Skool using Selenium... Please wait.")
        options = webdriver.ChromeOptions()

        driver = webdriver.Chrome(service=Service(
            ChromeDriverManager().install()), options=options)

        print("WebDriver initiated.")

        driver.get("https://www.skool.com/login")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "email")))

        print("Login page loaded successfully.")

        # Fill in login credentials
        driver.find_element(By.ID, "email").send_keys(skool_email)
        driver.find_element(By.ID, "password").send_keys(skool_password)
        driver.find_element(
            By.CLASS_NAME, "styled__LoginButton-sc-1kn1nfb-3").click()

        print("Login form submitted.")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "styled__PostItemWrapper-sc-e4ns84-7")))

        print("Successfully logged in.")

        cookies = driver.get_cookies()
        print(f"Captured Cookies: {cookies}")

        # Extract auth token from cookies
        auth_token = next(
            (cookie["value"]
             for cookie in cookies if cookie["name"] == "auth_token"), None
        )

        if not auth_token:
            raise Exception("Auth token not found in cookies.")

        print(f"Auth token retrieved: {auth_token}")
        return driver  # Return the WebDriver instance for further use

    except TimeoutException:
        print("Timeout occurred while trying to log in.")
    except Exception as e:
        print(f"An error occurred during login: {e}")


def convert_post_time_to_date(post_time_str):
    """Convert post time to date in DD/MM/YYYY format using UTC."""
    now = datetime.utcnow()
    try:
        if 'h ago' in post_time_str:
            hours_ago = int(post_time_str.split('h')[0].strip())
            post_date = now - timedelta(hours=hours_ago)
        elif 'd ago' in post_time_str:
            days_ago = int(post_time_str.split('d')[0].strip())
            post_date = now - timedelta(days=days_ago)
        else:
            post_date = datetime.strptime(
                post_time_str, "%b %d").replace(year=now.year)
    except ValueError:
        post_date = now
    return post_date.strftime("%d/%m/%Y")


def remove_duplicates(dataframe):
    """Remove duplicates from the DataFrame."""
    dataframe.drop_duplicates(
        subset=["Title", "Post Date", "Category"], keep='first', inplace=True)


def scrape_community_posts(driver, community_url):
    """Scrape all posts from a given Skool community."""
    posts_data = []
    try:
        # Navigate to the community page
        driver.get(community_url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "styled__PostItemWrapper-sc-e4ns84-7")))

        while True:
            # Extract post elements
            post_elements = driver.find_elements(
                By.XPATH, "//div[contains(@class, 'styled__PostItemWrapper-sc-e4ns84-7')]"
            )

            for post in post_elements:
                try:
                    # Extract post details
                    name_element = post.find_element(
                        By.XPATH, ".//span[contains(@class, 'UserNameText')]"
                    )
                    name = name_element.text if name_element else "N/A"

                    # Extract profile picture with refined XPath
                    try:
                        profile_picture_element = post.find_element(
                            By.XPATH, ".//div[contains(@class, 'styled__AvatarWrapper-sc-1o1lx2q-0')]//img"
                        )
                        profile_picture = profile_picture_element.get_attribute(
                            "src") if profile_picture_element else "N/A"
                    except NoSuchElementException:
                        profile_picture = "N/A"

                    # Extract user level using class name method
                    try:
                        level_element = post.find_element(
                            By.CLASS_NAME, "styled__BadgeWrapper-sc-1o1lx2q-2"
                        )
                        level = level_element.text.strip() if level_element else "N/A"
                    except NoSuchElementException:
                        level = "N/A"

                    post_time_element = post.find_element(
                        By.XPATH, ".//div[contains(@class, 'PostTimeContent')]"
                    )
                    post_time_raw = post_time_element.text if post_time_element else "N/A"
                    post_time = post_time_raw.replace(" in", "").strip()
                    post_date = convert_post_time_to_date(post_time)

                    category_element = post.find_element(
                        By.XPATH, ".//div[contains(@class, 'GroupFeedLinkLabel')]"
                    )
                    category = category_element.text if category_element else "N/A"

                    title_element = post.find_element(
                        By.XPATH, ".//div[contains(@class, 'Title')]"
                    )
                    title = title_element.text if title_element else "N/A"

                    description_element = post.find_element(
                        By.XPATH, ".//div[contains(@class, 'ContentPreviewWrapper')]"
                    )
                    description = description_element.text if description_element else "N/A"

                    likes_element = post.find_element(
                        By.XPATH, ".//div[contains(@class, 'LikesCount')]"
                    )
                    likes = likes_element.text if likes_element else "0"

                    comments_element = post.find_element(
                        By.XPATH, ".//div[contains(@class, 'CommentsCount')]"
                    )
                    comments = comments_element.text if comments_element else "0"

                    date_scraped = datetime.utcnow().strftime("%d/%m/%Y")

                    posts_data.append({
                        "Name": name,
                        "Profile Picture": profile_picture,
                        "Level": level,
                        "Post Date": post_date,
                        "Category": category,
                        "Title": title,
                        "Description": description,
                        "Likes": likes,
                        "Comments": comments,
                        "Date Scraped": date_scraped
                    })
                except NoSuchElementException as e:
                    print(f"An element was not found: {e}")

            # Step 3: Track the number of posts before clicking the next button
            previous_post_count = len(posts_data)
            print(f"Number of posts before clicking next: {
                  previous_post_count}")

            # Step 2: Check if there is a next page button and click it, or scroll down to load more
            try:
                next_button = driver.find_element(
                    By.XPATH, "//button[contains(@class, 'styled__ButtonWrapper-sc-dscagy-1') and span[text()='Next']]"
                )
                print("Next button found. Attempting to click it...")

                # Scroll to the button
                driver.execute_script(
                    "arguments[0].scrollIntoView();", next_button
                )

                # Click the button
                next_button.click()
                time.sleep(5)  # Allow time for the next page to load
                print("Next button clicked. Waiting for new content to load...")

            except NoSuchElementException:
                print("No more pages available or pagination ended.")
                break

            # Step 3: After clicking next, check if new posts were loaded
            current_post_elements = driver.find_elements(
                By.XPATH, "//div[contains(@class, 'styled__PostItemWrapper-sc-e4ns84-7')]"
            )

        # Log collected data to check if data is collected
        print(f"Collected {len(posts_data)} posts.")

    except Exception as e:
        print(f"An error occurred while scraping: {e}")
    finally:
        # Store scraped data in a DataFrame and save it to CSV
        if posts_data:
            df = pd.DataFrame(posts_data)
            remove_duplicates(df)  # Remove duplicates from the DataFrame

            # Extract community identifier from the URL
            community_identifier = re.sub(
                r'https://www\.skool\.com/', '', community_url).replace('/', '_')
            output_file = f"scraped_community_posts_{community_identifier}.csv"

            # Save DataFrame to CSV file
            df.to_csv(output_file, index=False)
            print(f"Data scraped and saved to {output_file}.")
            return output_file  # Return the path to the saved CSV file
        else:
            print("No data collected, CSV not saved.")
            return None


def scrape_community_data(community_url, community_owner):
    driver = login_and_get_driver()
    if driver:
        scraped_data = scrape_community_posts(driver, community_url)
        driver.quit()
        return scraped_data
    else:
        return None
