import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime
from database import store_in_dynamodb  # Assuming you have a custom database module

API_URL = "https://m29oncz02i.execute-api.us-east-1.amazonaws.com/prod/articles/"  # FastAPI endpoint to fetch articles

# Function to fetch scraped data from the API (cached data)
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

# Function to scrape website content using Selenium
def scrape_website(website):
    # Check if the website is already scraped via the API
    existing_content = get_scraped_data(website)
    if existing_content:
        print(f"Using cached data for {website}")
        return existing_content

    # Set Chrome options for headless mode
    print("Launching Chrome browser in headless mode...")
    options = Options()
    options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Setup for driver
    driver = webdriver.Chrome(service=Service("/usr/bin/chromedriver"), options=options)

    try:
        driver.get(website)
        print("Page loaded...")
        html = driver.page_source

        # Extract content using BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Extract title and published date
        title = soup.title.string if soup.title else "No title found"
        published_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Set current time as published date
        content = str(soup.body)  # Extract body content (can be cleaned or processed as needed)

        # Save scraped content to DynamoDB via the custom store_in_dynamodb function
        store_in_dynamodb(title, website, published_date, content)

        # Extract and clean body content from the HTML
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

    # Remove all script and style tags
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    cleaned_content = soup.get_text(separator="\n")
    
    # Clean up the content (remove extra spaces and newlines)
    cleaned_content = "\n".join(line.strip() for line in cleaned_content.splitlines() if line.strip())

    return cleaned_content

# Split DOM Content into smaller chunks (if the content is too long)
def split_dom_content(dom_content, max_length=6000):
    return [
        dom_content[i:i + max_length] for i in range(0, len(dom_content), max_length)
    ]
