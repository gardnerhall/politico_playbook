import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Function to query the database and get the count of mentions for a specific string
def get_mentions_count(db_name="scraped_articles.db", search_string=""):
    # Connect to the existing database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Fetch articles with their date and content
    cursor.execute("SELECT date, content FROM articles WHERE content IS NOT NULL")
    articles = cursor.fetchall()

    # Initialize an empty list to store the results
    mentions = []

    # Loop through each article
    for date, content in articles:
        if content and search_string.lower() in content.lower():  # Case-insensitive search
            count = content.lower().count(search_string.lower())  # Count occurrences
            mentions.append({"date": date, "mention_count": count})

    # Convert the result to a pandas dataframe
    df = pd.DataFrame(mentions)

    # Close the connection
    conn.close()

    # Return the dataframe
    return df

# Function to plot a time series with weekly smoothing
def plot_time_series(df, search_string):
    # Ensure the 'date' column is in datetime format
    df['date'] = pd.to_datetime(df['date'])

    # Set 'date' as the index for time series analysis
    df.set_index('date', inplace=True)

    # Resample the data by week and sum the mentions per week
    weekly_data = df.resample('W').sum()  # W for weekly resampling

    # Smooth the data with a rolling mean (window size of 2 for this example)
    weekly_data['smoothed'] = weekly_data['mention_count'].rolling(window=10).mean()

    # Plotting the time series data
    plt.figure(figsize=(10, 6))
    plt.plot(weekly_data.index, weekly_data['mention_count'], label='Original Mentions', color='blue', alpha=0.6)
    plt.plot(weekly_data.index, weekly_data['smoothed'], label='Smoothed Mentions (Rolling Mean)', color='red', linestyle='--')
    plt.title(f'Time Series of Mentions for "{search_string}" (Weekly)')
    plt.xlabel('Date')
    plt.ylabel('Mention Count')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Show the plot
    plt.show()

# Example usage
if __name__ == "__main__":
    search_string = input("Enter the search string: ")
    df = get_mentions_count(search_string=search_string)

    # Display the dataframe (long format)
    if not df.empty:
        print(f"\nMention counts for '{search_string}':\n")
        print(df)
        # Plot the time series with weekly smoothing
        plot_time_series(df, search_string)
    else:
        print(f"No mentions found for '{search_string}'.")

