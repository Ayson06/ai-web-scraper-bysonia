import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
from database import store_in_dynamodb

API_URL = "https://m29oncz02i.execute-api.us-east-1.amazonaws.com/prod/articles/"

def get_scraped_data(url):
    try:
        response = requests.get(f"{API_URL}?url={url}")
        if response.status_code == 200:
            article = response.json()
            return article.get('content', None)
        else:
            print(f"Error: {response.status_code}, Unable to fetch data")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def scrape_website(website):
    # Check if data is already scraped
    existing_content = get_scraped_data(website)
    if existing_content:
        print(f"Using cached data for {website}")
        return existing_content

    print("Launching Chrome browser in headless mode...")
    options = Options()
    options.add_argument("--headless")  # Run Chrome without GUI
    options.add_argument("--no-sandbox")  
    options.add_argument("--disable-dev-shm-usage")  
    options.add_argument("--remote-debugging-port=9222")  

    # Automatically download ChromeDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(website)
        print("Page loaded...")
        html = driver.page_source

        # Extract content
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title else "No title found"
        published_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
        content = extract_body_content(html)  
        cleaned_content = clean_body_content(content)  

        # Store in DynamoDB
        store_in_dynamodb(title, website, published_date, cleaned_content)

        return cleaned_content

    finally:
        driver.quit()

# Extract Body Content
def extract_body_content(html_content):
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    return str(body_content) if body_content else ""

# Clean Body Content (remove scripts, styles)
def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    cleaned_content = soup.get_text(separator="\n")
    return "\n".join(line.strip() for line in cleaned_content.splitlines() if line.strip())

# Split content into smaller chunks if needed
def split_dom_content(dom_content, max_length=6000):
    return [dom_content[i: i + max_length] for i in range(0, len(dom_content), max_length)]
