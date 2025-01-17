import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import sqlite3
from datetime import datetime

# Initialize Dash app
app = dash.Dash(__name__)

# Function to query data for mentions of a single term
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

    # Convert 'date' column to datetime format
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

# Function to get co-occurrence data for two terms
def get_co_occurrences(search_string_1, search_string_2):
    conn = sqlite3.connect('scraped_articles.db')
    query = f"""
    SELECT date, COUNT(*) AS co_occurrences
    FROM articles
    WHERE (title LIKE ? OR content LIKE ?)
    AND (title LIKE ? OR content LIKE ?)
    GROUP BY date
    ORDER BY date
    """
    df = pd.read_sql(query, conn, params=[f'%{search_string_1}%', f'%{search_string_1}%', f'%{search_string_2}%', f'%{search_string_2}%'])
    conn.close()

    # Convert 'date' to datetime format
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['month'] = df['date'].dt.to_period('M')
    monthly_co_occurrences = df.groupby('month').size().reset_index(name='co_occurrences')
    monthly_co_occurrences['month'] = monthly_co_occurrences['month'].dt.to_timestamp()

    # Rolling average for smoother trends
    monthly_co_occurrences['rolling_mean'] = monthly_co_occurrences['co_occurrences'].rolling(window=3).mean()

    return monthly_co_occurrences

# Layout of the Dash app
app.layout = html.Div([
    html.H1("Politico Mentions and Co-occurrence Analysis"),
    
    # Input section for search term
    html.Div([
        html.Label("Search for a term:"),
        dcc.Input(id="input", value="Brexit", type="text"),
        html.Button('Submit', id='submit-val', n_clicks=0),
        dcc.Graph(id="mentions-graph")
    ]),

    # Inputs for custom co-occurrence terms
    html.Div([
        html.Label("Enter two terms for co-occurrence analysis:"),
        html.Div([
            dcc.Input(id="term-1", value="Brexit", type="text", placeholder="Enter first term"),
            dcc.Input(id="term-2", value="EU", type="text", placeholder="Enter second term"),
            html.Button('Submit Co-occurrence', id='submit-cooccurrence', n_clicks=0)
        ]),
    ]),

    # Co-occurrence Graph
    html.Div([
        dcc.Graph(id="co-occurrence-graph")
    ])
])

# Update the main graph and co-occurrence graph based on user input
@app.callback(
    [dash.dependencies.Output('mentions-graph', 'figure'),
     dash.dependencies.Output('co-occurrence-graph', 'figure')],
    [dash.dependencies.Input('submit-val', 'n_clicks'),
     dash.dependencies.Input('submit-cooccurrence', 'n_clicks')],
    [dash.dependencies.State('input', 'value'),
     dash.dependencies.State('term-1', 'value'),
     dash.dependencies.State('term-2', 'value')]
)
def update_graphs(n_clicks_mentions, n_clicks_cooccurrence, search_term, term_1, term_2):
    # Main mentions graph for the first term
    df_mentions = get_data_from_db(search_term)
    fig_mentions = px.line(df_mentions, x='month', y='rolling_mean', title=f'Monthly Mentions for "{search_term}"')

    # Co-occurrence graph for the two user-provided terms
    if n_clicks_cooccurrence > 0:  # Co-occurrence terms are submitted
        df_co_occurrence = get_co_occurrences(term_1, term_2)
        fig_co_occurrence = px.line(df_co_occurrence, x='month', y='rolling_mean', title=f'Co-occurrence of "{term_1}" and "{term_2}"')
    else:
        fig_co_occurrence = px.line(title="Co-occurrence graph requires two terms to be entered")

    return fig_mentions, fig_co_occurrence

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)
