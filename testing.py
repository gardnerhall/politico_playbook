import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm  # For progress bar
import time  # For sleep
import re  # For regex matching

# Function to send the HTTP request and return the response
def send_request(url):
    try:
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

# Function to extract valid URLs from <a> tags (filter URLs by base_url)
def extract_urls(links, base_url):
    urls = set()  # Use a set to automatically handle duplicate URLs
    for link in links:
        href = link['href']
        full_url = urljoin(base_url, href)  # Construct full URL
        
        # Check if the URL starts with base_url (or any other conditions you deem fit)
        if full_url.startswith(base_url):
            urls.add(full_url)
    return urls

# Function to find the "next page" link
def find_next_page(soup):
    next_page_link = soup.find('a', class_='next page-numbers')
    if next_page_link and 'href' in next_page_link.attrs:
        return next_page_link['href']
    return None

# Function to grab the body text from an individual article
def grab_article_body(url):
    response = send_request(url)
    if not response:
        return None

    soup = BeautifulSoup(response.content, 'lxml')

    # Find all <p> tags to extract the body text
    paragraphs = soup.find_all('p')

    # Combine all the paragraph texts
    article_text = ' '.join([para.get_text() for para in paragraphs])

    return article_text

# Function to save URLs and their associated text to a file
def save_urls_and_text(urls, output_file="scraped_articles.txt"):
    with open(output_file, 'w') as file:
        for url, article_text in urls:
            file.write(f"URL: {url}\n")
            file.write(f"Content: {article_text}\n\n")
    print(f"Saved {len(urls)} articles to '{output_file}'")

# Main function to scrape the website, extract URLs, and then scrape content from each URL
def scrape_website_for_urls(url, output_file="scraped_articles.txt", max_pages=20):
    all_urls = set()  # Set to store all unique URLs

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
        all_urls.update(urls)  # Add the new URLs to the set

        # Debugging: print how many URLs were scraped from this page
        print(f"Scraped {len(urls)} URLs from page {page_num}")

        # Step 4: Find the next page URL (pagination)
        soup = BeautifulSoup(response.content, 'lxml')
        next_page = find_next_page(soup)

        if not next_page:
            break  # No next page, stop the loop

        # If there is a next page, update the URL, otherwise, break the loop
        print(f"Going to next page: {next_page}")
        time.sleep(2)  # Sleep between requests to avoid being blocked

    # Step 5: Now go to each article URL and grab the body content
    articles = []
    for article_url in all_urls:
        print(f"Scraping article: {article_url}")
        article_text = grab_article_body(article_url)
        if article_text:
            articles.append((article_url, article_text))

    # Step 6: Save the scraped articles to a file
    if articles:
        save_urls_and_text(articles, output_file)
    else:
        print("No articles were scraped.")

    return articles  # Return the list of articles with their body content

# Example usage
base_url = "https://www.politico.eu/newsletter/london-playbook/"
scrape_website_for_urls(base_url)