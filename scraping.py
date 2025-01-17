import sqlite3
from requests import get
from bs4 import BeautifulSoup

#Function to clear the database
def clear_db(db_name="scraped_articles.db"):
    # Connect to the database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Get the names of all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    # Drop all tables
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()

clear_db()  # Uncomment this line to clear the database

# Function to send the HTTP request and return the response
def send_request(url):
    try:
        response = get(url, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx, 5xx)
        return response
    except Exception as e:
        print(f"Error accessing {url}: {e}")
        return None

# Function to extract and clean article data
def grab_article_data(url):
    response = send_request(url)
    if not response:
        return None

    soup = BeautifulSoup(response.content, 'lxml')

    # Extract title
    title = soup.find('h1', class_='hero__title')  # Title has class 'hero__title'
    title = title.get_text(strip=True) if title else None  # If no title, return None
    print(f"Found title: {title}")  # Debugging line to check the title

    # Extract date
    date = soup.find('span', class_='date-time__date')  # Date has class 'date-time__date'
    date = date.get_text(strip=True) if date else None  # If no date, return None
    print(f"Found date: {date}")  # Debugging line to check the date

    # Extract author (from the <a> tag inside a div with class 'authors article-meta__authors')
    author_tag = soup.find('div', class_='authors article-meta__authors')
    if author_tag:
        author_link = author_tag.find('a')  # Find the <a> tag within the author section
        author = author_link.get_text(strip=True) if author_link else None  # If no author, return None
    else:
        author = None
    print(f"Found author: {author}")  # Debugging line to check the author

    # Skip the article if either title or author is missing or empty
    if not title or not author:
        print(f"Skipping article: {url}")  # Debugging line to check why articles are skipped
        return None

    # Extract article body (all <p> tags)
    paragraphs = soup.find_all('p')
    article_text = ' '.join([para.get_text() for para in paragraphs])

    return title, author, date, article_text

# Function to create the SQLite database and table if it doesn't exist
def create_db(db_name="scraped_articles.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY,
            title TEXT,
            author TEXT,
            date TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to save data into the database
def save_to_db(data, db_name="scraped_articles.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Insert data into the articles table
    cursor.executemany('''
        INSERT INTO articles (title, author, date, content)
        VALUES (?, ?, ?, ?)
    ''', data)
    
    conn.commit()
    conn.close()

# Function to scrape a single page and extract valid article links
def get_valid_article_urls(page_url, base_url):
    response = send_request(page_url)
    if not response:
        return []

    soup = BeautifulSoup(response.content, 'lxml')

    # Find all article links on this page
    article_links = soup.find_all('a', href=True)
    
    # Filter out links that:
    # 1. Do not start with the base URL.
    # 2. Do not contain 'london-playbook' in the URL.
    article_urls = {
        link['href'] for link in article_links
        if link['href'].startswith(base_url) and '-' in link['href'][len(base_url):]
    }

    return article_urls

# Main function to scrape a list of URLs and save the data to the database
def scrape_and_save_to_db(base_url, max_pages=10, db_name="scraped_articles.db"):
    create_db(db_name)  # Create the database and table if not exists

    all_articles = []

    for page_num in range(1, max_pages + 1):
        page_url = f"{base_url}/page/{page_num}/"
        print(f"Scraping page {page_num}: {page_url}")

        # Get valid article URLs from the page
        article_urls = get_valid_article_urls(page_url, base_url)

        for article_url in article_urls:
            print(f"Scraping article: {article_url}")
            article_data = grab_article_data(article_url)
            if article_data:
                all_articles.append(article_data)
        
        print(f"Finished scraping page {page_num}, found {len(article_urls)} articles.")

    # Save all collected articles to the database
    save_to_db(all_articles, db_name)
    print(f"Saved {len(all_articles)} articles to the database.")

# Example usage
base_url = "https://www.politico.eu/newsletter/london-playbook"  # Base URL
scrape_and_save_to_db(base_url, max_pages=50)

