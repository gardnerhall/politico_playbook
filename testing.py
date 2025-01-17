import requests
import sqlite3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
from tqdm import tqdm
import time

# Function to send the HTTP request and return the response
def send_request(url):
    try:
        # Send a GET request to the website with a timeout
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx, 5xx)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return None

# Function to parse the HTML content and extract all <a> tags with href attributes
def parse_html_for_links(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    return soup.find_all('a', href=True)  # Find all <a> tags with href attribute

# Function to extract valid URLs from <a> tags (filter URLs by base_url and check for dash '-')
def extract_urls(links, base_url):
    urls = set()  # Use a set to automatically handle duplicate URLs
    for link in links:
        href = link['href']
        full_url = urljoin(base_url, href)  # Construct full URL

        # Check if the URL starts with base_url and contains a dash ('-') in the path
        if full_url.startswith(base_url) and '-' in full_url[len(base_url):]:
            urls.add(full_url)
    return urls

# Function to find the "next page" link
def find_next_page(soup):
    next_page_link = soup.find('a', class_='next page-numbers')
    if next_page_link and 'href' in next_page_link.attrs:
        return next_page_link['href']
    return None

# Function to grab the title, author, date, and body text from an individual article
def grab_article_body(url):
    response = send_request(url)
    if not response:
        return None

    soup = BeautifulSoup(response.content, 'lxml')

    # Extract title
    title = soup.find('h1', class_='hero__title')  # Title has class 'hero__title'
    title = title.get_text(strip=True) if title else "No title found"

    # Extract date
    date = soup.find('span', class_='date-time__date')  # Date has class 'date-time__date'
    date = date.get_text(strip=True) if date else "No date found"

    # Extract author (from the <a> tag inside a div with class 'authors article-meta__authors')
    author_tag = soup.find('div', class_='authors article-meta__authors ')
    if author_tag:
        author_link = author_tag.find('a')  # Find the <a> tag within the author section
        author = author_link.get_text(strip=True) if author_link else "No author found"
    else:
        author = "No author found"

    # Extract article body (all <p> tags)
    paragraphs = soup.find_all('p')
    article_text = ' '.join([para.get_text() for para in paragraphs])

    return title, author, date, article_text

# Function to save article data into a CSV file
def save_articles_to_csv(articles, output_file="scraped_articles.csv"):
    # Define the headers for the CSV
    headers = ['Date', 'Author', 'Title', 'Text']

    # Open the CSV file for writing
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # Write the headers
        for article in articles:
            # Each article is a tuple (title, author, date, text)
            writer.writerow(article)

    print(f"Saved {len(articles)} articles to '{output_file}'")

# Main function to scrape the website, extract URLs, and then scrape content from each URL
def scrape_website_for_urls(url, output_file="scraped_articles.csv", max_pages=None):
    all_articles = []  # List to store all article data (title, author, date, text)
    all_urls = set()  # Set to store all unique article URLs

    # Loop over pages and scrape articles
    for page_num in tqdm(range(1, max_pages + 1), desc="Scraping Pages"):
        # Step 1: Build the page URL and send the HTTP request
        page_url = f"{url}page/{page_num}/"
        print(f"Scraping page {page_num} at {page_url}")
        response = send_request(page_url)
        if response is None:
            break

        # Step 2: Parse the HTML content and find all <a> tags
        links = parse_html_for_links(response.content)

        # Step 3: Extract and process URLs (filter by base_url)
        urls = extract_urls(links, url)
        print(f"Scraped {len(urls)} URLs from page {page_num}")
        all_urls.update(urls)  # Add new URLs to the set

        # Step 4: Find the next page URL (pagination)
        soup = BeautifulSoup(response.content, 'lxml')
        next_page = find_next_page(soup)

        if not next_page:
            break  # No next page, stop the loop

        print(f"Going to next page: {next_page}")
        time.sleep(2)  # Delay between requests to avoid overloading the server

    # Step 5: Now grab the article content from each URL
    for article_url in all_urls:
        print(f"Scraping article: {article_url}")
        title, author, date, article_text = grab_article_body(article_url)
        if article_text:  # Only save if there's content
            all_articles.append((date, author, title, article_text))

    # Step 6: Save the scraped articles to a CSV
    if all_articles:
        save_articles_to_csv(all_articles, output_file)
    else:
        print("No articles were scraped.")

    return all_articles  # Return the list of articles with their content

# Example usage
base_url = "https://www.politico.eu/newsletter/london-playbook/"  # Use the base URL directly
scrape_website_for_urls(base_url, output_file="scraped_articles.csv", max_pages=5)
