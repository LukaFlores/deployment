import sqlite3
import config
import alpaca_trade_api as tradeapi
from datetime import date, datetime
import pandas as pd
import tulipy 
import numpy 
import pytz


print(datetime.now())

#Connection to SQLITE
connection = sqlite3.connect(config.DB_File)
connection.row_factory = sqlite3.Row


cursor = connection. cursor()

cursor.execute("""
    SELECT id from strategy WHERE name = 'bollinger_bands'
""")

strategy_id = cursor.fetchone()['id']

cursor.execute("""
    SELECT symbol, name
    from stock
    join stock_strategy on stock_strategy.stock_id = stock.id
    where stock_strategy.strategy_id = ?
""", (strategy_id,))

stocks = cursor.fetchall()
symbols = [stock['symbol'] for stock in stocks]

#Getting Current Date and Opening 15 Minute Time Range

current_date = pd.Timestamp.today().strftime("%Y-%m-%d")

today = date.today() 
market_timezone = pytz.timezone('America/New_York')
start_dt = datetime(today.year,today.month,today.day, 9, 30)
start_minute_bar = market_timezone.localize(start_dt).isoformat()
end_dt = datetime(today.year,today.month,today.day, 16, 00)
end_minute_bar = market_timezone.localize(end_dt).isoformat()


api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

#Checking For Past Orders from that day
orders = api.list_orders(status='all', limit=500, after={current_date})
existing_orders_symbols = [order.symbol for order in orders if order.status != 'canceled']

messages = []

for symbol in symbols:
    minute_bars = api.get_barset(symbol, '1Min', start=start_minute_bar, end=end_minute_bar).df

    if len(minute_bars[symbol,'close']) >= 20:

        lower, middle , upper = tulipy.bbands(minute_bars[symbol,'close'].to_numpy(), 20, 2)

        current_candle = minute_bars.iloc[-1]
        previous_candle = minute_bars.iloc[-2]

        if current_candle[symbol,'close'] > lower[-1] and previous_candle[symbol, 'close'] < lower[-2]:
            if symbol not in existing_orders_symbols:
                limit_price = current_candle[symbol,'close']

                candle_range = current_candle[symbol,'high'] - current_candle[symbol,'low']

                message = f"Selling Short for {symbol} at {limit_price}\n\n"
                messages.append(message)

                #Printing For LOG
                print(message)

                # Placing Trade
            #     try: 
            #         api.submit_order(
            #             symbol=symbol,
            #             side='buy',
            #             type='limit',
            #             qty=calculate_quantity(limit_price),
            #             time_in_force='day',
            #             order_class='bracket',
            #             limit_price = limit_price,
            #             take_profit=dict(
            #                 limit_price= limit_price + (candle_range * 3),
            #             ),
            #             stop_loss=dict(
            #                 stop_price= limit_price - (candle_range),
            #             )
            #         )
            #     except Exception as e:
            #         print(f"Could not submit order {e}")
            # else:
            #     print(f"Already an Order for {symbol}, skipping")
            
