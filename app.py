# Import necessary Dash components
import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import sqlite3
from datetime import datetime

# Initialize Dash app
app = dash.Dash(__name__)

# Your database query function (example)
def get_data_from_db(search_string):
    conn = sqlite3.connect('scraped_articles.db')
    query = f"""
    SELECT date, COUNT(*) AS mentions
    FROM articles
    WHERE title LIKE ? OR content LIKE ?
    GROUP BY date
    ORDER BY date
    """
    df = pd.read_sql(query, conn, params=[f'%{search_string}%', f'%{search_string}%'])
    conn.close()

    # Convert the 'date' column to datetime format
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Get the current year and month
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Filter out data from the current ongoing month
    df = df[~((df['date'].dt.year == current_year) & (df['date'].dt.month == current_month))]

    # Add a 'month' column to group by month and year
    df['month'] = df['date'].dt.to_period('M')

    # Count occurrences per month
    monthly_mentions = df.groupby('month').size().reset_index(name='mentions')

    # Convert 'month' from Period to datetime (first day of each month)
    monthly_mentions['month'] = monthly_mentions['month'].dt.to_timestamp()

    # Compute the rolling mean (for monthly smoothing)
    monthly_mentions['rolling_mean'] = monthly_mentions['mentions'].rolling(window=3).mean()

    return monthly_mentions

# Example: Query the database for a string
search_string = "Brexit"
df = get_data_from_db(search_string)

# Create the initial chart
fig = px.line(df, x='month', y='rolling_mean', title=f'Rolling Monthly Mean of Mentions for "{search_string}"')

# Layout of the Dash app
app.layout = html.Div([
    html.H1("Politico Mentions Analysis"),
    html.Div([
        html.Label("Search for a term:"),
        dcc.Input(id="input", value="Brexit", type="text"),
        html.Button('Submit', id='submit-val', n_clicks=0),
        dcc.Graph(id="graph", figure=fig)
    ])
])

# Update the graph based on the input value
@app.callback(
    dash.dependencies.Output('graph', 'figure'),
    [dash.dependencies.Input('submit-val', 'n_clicks')],
    [dash.dependencies.State('input', 'value')]
)
def update_graph(n_clicks, value):
    # Get the updated data based on the search string
    df = get_data_from_db(value)
    # Create the updated figure with rolling mean
    fig = px.line(df, x='month', y='rolling_mean', title=f'Rolling Monthly Mean of Mentions for "{value}"')
    return fig

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)


