import json
import logging

import facebook_scraper as fs

# Configure logging
logging.basicConfig(filename="scraper.log", level=logging.INFO)


# Load page list from config
def load_config(file_path="config.json"):
    with open(file_path, "r") as file:
        config = json.load(file)
    return config["pages"]


# Convert cookies from EditThisCookie format to facebook-scraper format
def convert_cookies(exported_cookies_path="exported_cookies.json", output_path="cookies.json"):
    with open(exported_cookies_path, "r") as file:
        exported_cookies = json.load(file)["cookies"]
    cookies = {cookie["name"]: cookie["value"] for cookie in exported_cookies}
    with open(output_path, "w") as file:
        json.dump(cookies, file, indent=4)
    return cookies


# Main script
def main():
    try:
        # Convert cookies
        cookies = convert_cookies()  # Automatically generates cookies.json

        # Load pages from config
        pages = load_config("config.json")

        for page in pages:
            fs.write_posts_to_csv(
                account=page,
                # The method uses get_posts internally so you can use the same arguments, and they will be passed along
                page_limit=5,
                timeout=60,
                options={
                    'allow_extra_requests': False
                },
                filename=f'./data/messages_{page}.csv',  # Will throw an error if the file already exists
                resume_file='next_page.txt',
                # Will save a link to the next page in this file after fetching it and use it when starting.
                matching='.+',
                # A regex can be used to filter all the posts matching a certain pattern (here, we accept anything)
                not_matching='^Warning',
                # And likewise those that don't fit a pattern (here, we filter out all posts starting with "Warning")
                format='csv',  # Output file format, can be csv or json, defaults to csv
                days_limit=2,  # Number of days for the oldest post to fetch, defaults to 3650,
                cookies=cookies
            )
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
