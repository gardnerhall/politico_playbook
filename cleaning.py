import sqlite3
from dateutil import parser

# Function to clean date (only keep the date part)
def clean_date(date_str):
    """
    This function takes a date string, converts it to a datetime object,
    and returns only the date part (in YYYY-MM-DD format).
    """
    try:
        # Try to parse the date string into a datetime object
        date_obj = parser.parse(date_str.strip())
        # Return only the date part (without time)
        return date_obj.date()
    except (ValueError, TypeError):
        # Handle invalid or missing dates
        return None

# Function to update all dates in the database
def update_dates_in_db(db_name="scraped_articles.db"):
    # Connect to the existing database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Fetch all articles with their dates from the 'articles' table
    cursor.execute("SELECT id, date FROM articles WHERE date IS NOT NULL")
    articles = cursor.fetchall()
    
    for article_id, date_str in articles:
        # Clean the date
        cleaned_date = clean_date(date_str)
        
        # If the date is valid, update the article
        if cleaned_date:
            cursor.execute('''
                UPDATE articles
                SET date = ?
                WHERE id = ?
            ''', (cleaned_date, article_id))
        else:
            print(f"Skipping article {article_id} with invalid date: {date_str}")
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print("Finished updating dates in the database.")

# Example usage
if __name__ == "__main__":
    update_dates_in_db()