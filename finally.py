import dash
from dash import dcc, html
import plotly.graph_objects as go
import yfinance as yf
from dash.dependencies import Input, Output
import random
import pandas as pd
import numpy as np
from datetime import timedelta

# List of predefined stock symbols
STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NFLX', 'MU', 'INTC', 'PYPL', 'F', 'WMT', 'KO', 'SNAP', 'SHOP', 'CSCO', 'UBER', 'SBUX', 'TWTR', 'ADBE', 'NKE', 'MCD', 'NOK', 'PEP', 'BB', 'ORCL', 'AA', 'SONY']

# List of background colors
BACKGROUND_COLORS = [
    "lightblue", "lightgreen", "lightyellow", "lightpink", "lightgray", "lavender", "lightcoral", "powderblue", "honeydew", "lightsteelblue"
]

# Fetch stock data
def fetch_stock_data(symbol, period="1mo", interval="1d"):
    stock = yf.Ticker(symbol)
    data = stock.history(period=period, interval=interval)
    # Keep only weekdays (Monday to Friday)
    return data[data.index.weekday < 5]

# Fetch company name
def fetch_company_name(symbol):
    stock = yf.Ticker(symbol)
    return stock.info.get('longName', 'Company Name Not Found')

# Simulate future stock prices using linear regression
def simulate_future_prices(data, days=5):
    x = np.arange(len(data))
    y = data['Close'].values
    coef = np.polyfit(x, y, 1)
    poly = np.poly1d(coef)
    future_dates = pd.date_range(data.index[-1] + timedelta(days=1), periods=days, freq='B')  # 'B' frequency ensures weekdays
    future_prices = poly(np.arange(len(data), len(data) + days))
    return pd.DataFrame({'Date': future_dates, 'Close': future_prices}).set_index('Date')

# Create Dash app with external stylesheets for Animate.css
app = dash.Dash(__name__, external_stylesheets=['https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css'])

# Random background color for the window
window_bg_color = random.choice(BACKGROUND_COLORS)

# Layout
app.layout = html.Div(style={'backgroundColor': window_bg_color, 'padding': '20px'}, children=[
    html.H1("Real-Time Stock Price Viewer", style={
        'textAlign': 'center',
        'color': 'black',
        'animation': 'fadeIn 2s ease-out',  # Fade-in animation for header
    }),

    # Controls for selecting stock symbol, period, graph type, and update button
    html.Div(style={'display': 'flex', 'justifyContent': 'space-evenly', 'alignItems': 'center', 'marginBottom': '20px'}, children=[
        html.Div(style={'width': '20%'}, children=[  # Added a fixed width to keep consistent spacing
            html.Label("Select Stock Symbol to View:", style={'fontSize': '16px'}),
            dcc.Dropdown(
                id='stock-dropdown',
                options=[{'label': symbol, 'value': symbol} for symbol in STOCK_SYMBOLS],
                value='AAPL',
                style={'width': '100%', 'transition': 'background-color 0.3s ease'}  # Smooth background color transition
            ),
        ]),
        html.Div(style={'width': '20%'}, children=[  # Added a fixed width to keep consistent spacing
            html.Label("Select Time Period:", style={'fontSize': '16px'}),
            dcc.Dropdown(
                id='period-dropdown',
                options=[{'label': period, 'value': period} for period in ["1d", "5d", "1mo", "3mo", "6mo", "1y"]],
                value='1mo',
                style={'width': '100%', 'transition': 'background-color 0.3s ease'}
            ),
        ]),
        html.Div(style={'width': '20%'}, children=[  # Added a fixed width to keep consistent spacing
            html.Label("Select Graph Type:", style={'fontSize': '16px'}),
            dcc.Dropdown(
                id='graph-type-dropdown',
                options=[
                    {'label': 'Line Chart', 'value': 'line'},
                    {'label': 'Bar Chart', 'value': 'bar'},
                ],
                value='line',
                style={'width': '100%', 'transition': 'background-color 0.3s ease'}
            ),
        ]),
        html.Div(children=[  
            html.Button("Update", id="update-button", n_clicks=0, style={
                'fontSize': '16px',
                'padding': '10px',
                'marginTop': '0px',
                'backgroundColor': '#007bff',  # Blue background color
                'color': 'white',  # White text color
                'border': 'none',
                'borderRadius': '5px',  # Rounded corners
                'cursor': 'pointer',
                'transition': 'background-color 0.3s ease, transform 0.3s ease',  # Smooth transition for hover and zoom
                'width': '100px',  # Fixed width for consistency
                'boxShadow': '0px 4px 6px rgba(0, 0, 0, 0.1)',  # Subtle shadow effect
            })
        ]),

    ]),

    # Display company name and stock price
    html.Div(style={'textAlign': 'center', 'animation': 'fadeIn 2s ease-out'}, children=[
        html.Div(id='company-name', style={'fontSize': '18px', 'marginBottom': '10px'}),
        html.Div(id='price-label', style={'fontSize': '20px', 'fontWeight': 'bold', 'marginBottom': '20px'}), 
    ]),

    # Stock price graph
    dcc.Graph(id='stock-graph', config={'displayModeBar': True}),  # Removed 'animate': true
])

# Callback to update the graph, company name, and stock price
@app.callback(
    [Output('stock-graph', 'figure'),
     Output('company-name', 'children'),
     Output('price-label', 'children')],
    [Input('update-button', 'n_clicks'),  # Only trigger when the update button is clicked
     Input('stock-dropdown', 'value'),
     Input('period-dropdown', 'value'),
     Input('graph-type-dropdown', 'value'),
     Input('stock-graph', 'hoverData')]
)
def update_graph(n_clicks, symbol, period, graph_type, hoverData):
    # Proceed only if the button has been clicked
    if n_clicks == 0:
        return go.Figure(), "Please click 'Update' to fetch data", "Price: Not Available"
    
    data = fetch_stock_data(symbol, period=period)
    company_name = fetch_company_name(symbol)
    
    if data.empty:
        return go.Figure(), "Error: No data available", "Price: Not Available"
    
    # Simulate future stock prices
    future_data = simulate_future_prices(data, days=5)
    
    # Combine historical and future data
    combined_data = pd.concat([data, future_data])
    
    # Prepare the graph based on selected graph type
    if graph_type == 'line':
        fig = go.Figure(go.Scatter(x=combined_data.index, y=combined_data['Close'], mode='lines', name=f'{symbol} Stock Price', line=dict(color='dodgerblue', width=2)))
    else:
        fig = go.Figure(go.Bar(x=combined_data.index, y=combined_data['Close'], name=f'{symbol} Stock Price', marker=dict(color='dodgerblue')))
    
    # Update figure layout with animation effects
    fig.update_layout(
        title=f"Stock Prices for {symbol} ({period} period)",
        xaxis_title='Date',
        yaxis_title='Price ($)',
        hovermode='x unified',
        font=dict(family="Helvetica", size=14, color="black"),
        showlegend=False,  # Hide legend for simplicity
        plot_bgcolor='white',  # White background for the plot
        paper_bgcolor=window_bg_color,  # Keep the window background color consistent
        transition={'duration': 500},  # Smooth transition effect for chart rendering
    )
    
    # Get the most recent stock price
    last_price = data['Close'].iloc[-1]
    price_label = f"Last Price for {symbol}: ${last_price:.2f}"
    
    # If hover data exists, update the price label based on hover
    if hoverData:
        point = hoverData['points'][0]
        date = point['x']
        price = point['y']
        price_label = f"Price on {date}: ${price:.2f}"
    
    return fig, f"Company: {company_name}", price_label

if __name__ == '__main__':
    app.run_server(debug=True)
