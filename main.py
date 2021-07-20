import sqlite3, config
from fastapi import FastAPI , Request , Form 
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date
import alpaca_trade_api as tradeapi


app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def index(request: Request):
    stock_filter = request.query_params.get('filter', False)

    connection = sqlite3.connect(config.DB_File)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if stock_filter == 'new_closing_highs':
      cursor.execute("""
            SELECT * FROM (SELECT symbol, name, stock_id,
            MAX(close) AS max_close, date FROM stock_price
            LEFT JOIN stock ON stock.id = stock_price.stock_id
            GROUP BY stock_id ORDER BY symbol
        ) WHERE date = (SELECT MAX(date) FROM stock_price);
    """)
    elif stock_filter == 'new_closing_lows':
        cursor.execute("""
            SELECT * FROM (SELECT symbol, name, stock_id, MIN(close) 
            AS min_close, date FROM stock_price
            LEFT JOIN stock ON stock.id = stock_price.stock_id
            GROUP BY stock_id ORDER BY symbol
        ) WHERE date = (SELECT MAX(date) FROM stock_price);
    """)
    elif stock_filter == 'rsi_overbought' :
        cursor.execute("""
                    SELECT symbol, name, stock_id, date
                    FROM stock_price LEFT JOIN stock ON stock.id = stock_price.stock_id
                    WHERE rsi_14 > 70 AND date = (SELECT MAX(date) FROM stock_price) 
                    ORDER BY symbol
            """)
    elif stock_filter == 'rsi_oversold' :
        cursor.execute("""
                    SELECT symbol, name, stock_id, date
                    FROM stock_price LEFT JOIN stock ON stock.id = stock_price.stock_id
                    WHERE rsi_14 < 30 AND date = (SELECT MAX(date) FROM stock_price) 
                    ORDER BY symbol
            """)
    elif stock_filter == 'above_sma_20' :
        cursor.execute("""
                    SELECT symbol, name, stock_id, date
                    FROM stock_price LEFT JOIN stock ON stock.id = stock_price.stock_id
                    WHERE close > sma_20 AND date = (SELECT MAX(date) FROM stock_price) 
                    ORDER BY symbol
            """)
    elif stock_filter == 'below_sma_20' :
        cursor.execute("""
                    SELECT symbol, name, stock_id, date
                    FROM stock_price LEFT JOIN stock ON stock.id = stock_price.stock_id
                    WHERE close < sma_20 AND date = (SELECT MAX(date) FROM stock_price) 
                    ORDER BY symbol
            """)
    elif stock_filter == 'above_sma_50' :
        cursor.execute("""
                    SELECT symbol, name, stock_id, date
                    FROM stock_price LEFT JOIN stock ON stock.id = stock_price.stock_id
                    WHERE close > sma_50 AND date = (SELECT MAX(date) FROM stock_price) 
                    ORDER BY symbol
            """)
    elif stock_filter == 'below_sma_50' :
        cursor.execute("""
                    SELECT symbol, name, stock_id, date
                    FROM stock_price LEFT JOIN stock ON stock.id = stock_price.stock_id
                    WHERE close < sma_50 AND date = (SELECT MAX(date) FROM stock_price) 
                    ORDER BY symbol
            """)
    
    else:
        cursor.execute("""
            SELECT id, symbol, name FROM stock Order by symbol
        """)

    rows = cursor.fetchall()
    current_date = date.today().isoformat()

    cursor.execute("""
        SELECT symbol,rsi_14,sma_20,sma_20,mom_12,close
        FROM stock JOIN stock_price on stock_price.stock_id=stock.id
        WHERE date = (SELECT MAX(date) FROM stock_price);
    """)

    indicator_rows = cursor.fetchall()
    indicator_values = {}
    for row in indicator_rows:
        indicator_values[row['symbol']]= row 


    return templates.TemplateResponse("index.html", {"request": request, "stocks": rows, "indicator_values" : indicator_values})


@app.get("/stock/{symbol}")
def stock_detail(request: Request, symbol):
    connection = sqlite3.connect(config.DB_File)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM strategy
    """)
    strategies = cursor.fetchall()

    cursor.execute("""
        SELECT id, symbol, name FROM stock WHERE symbol = ?
    """, (symbol,))
    row = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM stock_price WHERE stock_id = ? ORDER by date DESC
    """, (row['id'],))
    prices = cursor.fetchall()

    return templates.TemplateResponse("stock_detail.html", {"request": request, "stock": row, "bars" : prices, "strategies" : strategies})

@app.post("/apply_strategy")
async def appy_strategy(strategy_id: int = Form(...), stock_id: int = Form(...)):
    connection = sqlite3.connect(config.DB_File)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO stock_strategy (stock_id, strategy_id) VALUES (? , ?)
    """, (stock_id, strategy_id))
    
    connection.commit()
    return RedirectResponse(url=f"/strategy/{strategy_id}", status_code=303)

@app.get("/strategies")
def strategies(request: Request):
    connection = sqlite3.connect(config.DB_File)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM strategy
    """)
    strategies = cursor.fetchall()

    print(strategies)
    return templates.TemplateResponse("strategies.html", {"request" : request, "strategies" : strategies})
    
@app.get("/orders")
def orders(request: Request):
    api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
    orders = api.list_orders(status='all', limit=500 )

    return templates.TemplateResponse("orders.html" , {"request" : request, "orders" : orders})


@app.get("/strategy/{strategy_id}")
def strategy(request: Request, strategy_id):
    connection = sqlite3.connect(config.DB_File)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name from strategy where id = ?
    """, (strategy_id,))

    strategy = cursor.execute("""
        SELECT symbol, name
        FROM stock JOIN stock_strategy on stock_strategy.stock_id = stock.id
        WHERE strategy_id = ?
    """, (strategy_id,))

    stocks = cursor.fetchall()

    return templates.TemplateResponse("strategy.html" , {"request" : request, "stocks" : stocks , "strategy" : strategy})