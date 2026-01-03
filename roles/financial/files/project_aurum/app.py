import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime
import os
import time
from sqlalchemy import create_engine, text

# --- DATABASE CONNECTION ---
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'aurum_db')
DB_USER = os.getenv('DB_USER', 'titan')
DB_PASS = os.getenv('DB_PASS', 'titan_secure_password')

db_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"
engine = create_engine(db_url)

def init_db():
    retries = 5
    while retries > 0:
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS metrics (
                        timestamp TIMESTAMP PRIMARY KEY,
                        gold_price FLOAT, oil_price FLOAT, us_debt FLOAT,
                        yield_curve FLOAT, real_rates FLOAT,
                        hyg_spread FLOAT, m2_supply FLOAT, pmi_index FLOAT
                    );
                """))
                conn.commit()
            return
        except Exception:
            retries -= 1
            time.sleep(5)

# --- DATA FETCHING ENGINES ---
def get_fred_data(series_id):
    try:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        # Force reading with error_bad_lines skipped
        df = pd.read_csv(url, on_bad_lines='skip')
        val = df.iloc[-1, 1]
        return float(val)
    except Exception as e:
        print(f"FRED Error ({series_id}): {e}")
        return 0.0

def get_macro_data():
    yc = get_fred_data('T10Y2Y')
    real_rates = get_fred_data('DFII10') 
    hyg_spread = get_fred_data('BAMLC0A0CM')
    m2_supply = get_fred_data('M2SL') 
    
    # PMI PATCH: Leave as 0.0 if failed, handle in display
    pmi = get_fred_data('NAPM')
        
    return yc, real_rates, hyg_spread, m2_supply, pmi

def get_live_market():
    try:
        tickers = yf.Tickers("GC=F CL=F")
        gold = tickers.tickers['GC=F'].history(period="1d")['Close'].iloc[-1]
        oil = tickers.tickers['CL=F'].history(period="1d")['Close'].iloc[-1]
        return gold, oil
    except: return 0, 0

def get_us_debt():
    try:
        url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
        params = {"sort": "-record_date", "page[size]": 1}
        r = requests.get(url, params=params).json()
        return float(r['data'][0]['tot_pub_debt_out_amt'])
    except: return 38000000000000

# --- APP SETUP ---
init_db()
app = dash.Dash(__name__)
server = app.server

# --- LAYOUT ---
app.layout = html.Div(style={'backgroundColor': '#050505', 'color': '#e0e0e0', 'fontFamily': 'monospace', 'minHeight': '100vh', 'padding': '20px'}, children=[
    
    html.Div(style={'maxWidth': '1400px', 'margin': '0 auto'}, children=[
        html.H1("TITAN // SENTINEL V2.0", style={'color': '#FFD700', 'borderBottom': '1px solid #333', 'marginBottom': '10px'}),
        html.Div("PROTOCOL: DEPRESSION / RECESSION / SUPPLY SHOCK DETECTION", style={'color': '#666', 'fontSize': '12px', 'marginBottom': '20px'}),
    ]),

    # ROWS
    html.H4("// SOVEREIGN LAYER (Recession Prediction)", style={'color': '#888', 'borderBottom': '1px dashed #333', 'marginTop': '30px'}),
    html.Div(id='row-sovereign', style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '10px'}),

    html.H4("// SYSTEMIC LAYER (Financial Plumbing)", style={'color': '#888', 'borderBottom': '1px dashed #333', 'marginTop': '30px'}),
    html.Div(id='row-systemic', style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '10px'}),

    html.H4("// PHYSICAL LAYER (Real World)", style={'color': '#888', 'borderBottom': '1px dashed #333', 'marginTop': '30px'}),
    html.Div(id='row-physical', style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '10px'}),

    dcc.Graph(id='main-chart', style={'height': '40vh', 'marginTop': '40px'}),
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0)
])

@app.callback(
    [Output('row-sovereign', 'children'), Output('row-systemic', 'children'), Output('row-physical', 'children'), Output('main-chart', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_system(n):
    gold, oil = get_live_market()
    debt = get_us_debt()
    yc, real_rate, hyg_oas, m2, pmi = get_macro_data()
    now = datetime.now()

    try:
        new_row = pd.DataFrame([{
            'timestamp': now, 'gold_price': gold, 'oil_price': oil, 'us_debt': debt,
            'yield_curve': yc, 'real_rates': real_rate, 'hyg_spread': hyg_oas, 'm2_supply': m2, 'pmi_index': pmi
        }])
        new_row.to_sql('metrics', engine, if_exists='append', index=False)
    except: pass

    try:
        df = pd.read_sql("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1440", engine).sort_values('timestamp')
    except: df = pd.DataFrame()

    def card(title, value, suffix="", risk_check=None):
        color = "#e0e0e0"
        if risk_check == "RED": color = "#ff4444" 
        if risk_check == "GREEN": color = "#00ff00"
        return html.Div([
            html.H4(title, style={'color': '#666', 'fontSize': '10px', 'marginBottom': '5px'}),
            html.H2(f"{value}{suffix}", style={'color': color, 'fontSize': '24px', 'margin': '0'})
        ], style={'backgroundColor': '#111', 'padding': '15px', 'borderRadius': '4px', 'width': '30%', 'textAlign': 'center', 'border': '1px solid #222'})

    # LOGIC
    yc_color = "RED" if yc < 0 else "GREEN"
    rr_color = "RED" if real_rate > 2.0 else "e0e0e0"
    hyg_color = "RED" if hyg_oas > 5.0 else "GREEN"
    pmi_color = "RED" if pmi < 50 and pmi > 0 else "GREEN" 
    oil_color = "RED" if oil > 100 else "e0e0e0"

    r1 = [card("10Y-2Y YIELD CURVE", f"{yc:.2f}", "%", yc_color), card("REAL INTEREST RATES", f"{real_rate:.2f}", "%", rr_color), card("US DEBT", f"${debt/1000000000000:,.2f}", " T")]
    r2 = [card("HYG CREDIT SPREAD", f"{hyg_oas:.2f}", "%", hyg_color), card("M2 MONEY SUPPLY", f"${m2/1000:,.1f}", " T"), card("GOLD PRICE", f"${gold:,.0f}")]
    
    # DISPLAY LOGIC for PMI (Handle 0.0)
    pmi_display = f"{pmi:.1f}" if pmi > 0 else "NO DATA"
    r3 = [card("ISM MANUF. PMI", pmi_display, "", pmi_color), card("CRUDE OIL (WTI)", f"${oil:.2f}", "", oil_color), card("DEBT/GOLD RATIO", f"{(debt/gold)/1000000000:,.2f}", " B")]

    fig = make_subplots(rows=1, cols=1)
    if not df.empty:
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['yield_curve'], mode='lines', name='Yield Curve', line=dict(color='#00ff00' if yc > 0 else '#ff0000')))
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['oil_price'], mode='lines', name='Oil Price', line=dict(color='#ff8800'), yaxis="y2"))
    fig.update_layout(title="RECESSION SIGNAL (Curve) vs INFLATION SIGNAL (Oil)", plot_bgcolor='#050505', paper_bgcolor='#050505', font=dict(color='#ccc'), height=400, yaxis2=dict(overlaying='y', side='right', showgrid=False))

    return r1, r2, r3, fig

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)
