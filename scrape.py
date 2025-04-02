import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager  # Automatically download the correct ChromeDriver
from bs4 import BeautifulSoup
from datetime import datetime
from database import store_in_dynamodb  # Assuming you have this function to store data in DynamoDB

API_URL = "https://m29oncz02i.execute-api.us-east-1.amazonaws.com/prod/articles/"  # FastAPI endpoint to fetch articles

# Function to fetch scraped data from API (to check if data is already scraped)
def get_scraped_data(url):
    try:
        # Send GET request to the API to fetch data
        response = requests.get(f"{API_URL}?url={url}")

        if response.status_code == 200:
            article = response.json()
            print("API Response:", article)  # Print the entire response to check its structure
            return article.get('content', None)  # Use .get to safely access 'content'
        else:
            print(f"Error: {response.status_code}, Unable to fetch data")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Main scraping function
def scrape_website(website):
    # Check if the website is already scraped via the API
    existing_content = get_scraped_data(website)
    if existing_content:
        print(f"Using cached data for {website}")
        return existing_content

    print("Launching Chrome browser in headless mode...")
    options = Options()
    options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--no-sandbox")  # Bypass OS-level security
    options.add_argument("--disable-dev-shm-usage")  # Prevent memory issues
    options.add_argument("--remote-debugging-port=9222")  # Set debugging port

    # Use webdriver_manager to automatically download ChromeDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(website)
        print("Page loaded...")
        html = driver.page_source

        # Extract content using BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # For example, extracting title and published date from the meta tags (you can modify this as per your needs)
        title = soup.title.string if soup.title else "No title found"
        published_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Set current time as published date (or extract it from the page)
        content = str(soup.body)  # Extract body content (can be cleaned or processed as needed)

        # Store the scraped content in DynamoDB
        store_in_dynamodb(title, website, published_date, content)  # Save to DB via the API

        # Extract and clean the body content
        body_content = extract_body_content(html)
        cleaned_content = clean_body_content(body_content)
        return cleaned_content

    finally:
        driver.quit()


# Extract Body Content from HTML
def extract_body_content(html_content):
    if not html_content:
        print("Error: Empty HTML content!")
        return ""

    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    if body_content:
        return str(body_content)
    
    print("Error: No body content found!")
    return ""


# Clean Body Content (remove scripts/styles)
def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    # Remove scripts and styles
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    # Get cleaned text
    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(
        line.strip() for line in cleaned_content.splitlines() if line.strip()
    )

    return cleaned_content

# Split DOM Content into chunks (if it's too long)
def split_dom_content(dom_content, max_length=6000):
    return [
        dom_content[i: i + max_length] for i in range(0, len(dom_content), max_length)
    ]
