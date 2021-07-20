import sqlite3
import config
import alpaca_trade_api as tradeapi
from datetime import date
import pandas as pd
import smtplib, ssl
from twilio.rest import Client


# Create a secure SSL context
context = ssl.create_default_context()

#Connection to SQLITE
connection = sqlite3.connect(config.DB_File)
connection.row_factory = sqlite3.Row


cursor = connection. cursor()

cursor.execute("""
    SELECT id from strategy WHERE name = 'opening_range_breakout'
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

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

#Getting Current Date and Opening 15 Minute Time Range
NY = 'America/New_York'
current_date = pd.Timestamp.today().strftime("%Y-%m-%d")
start_minute_bar = pd.Timestamp(f"{current_date} 9:30", tz=NY).isoformat() 
end_minute_bar = pd.Timestamp(f"{current_date} 9:45", tz=NY).isoformat()


#Checking For Past Orders from that day
orders = api.list_orders(status='all', limit=500, after={current_date})
existing_orders_symbols = [order.symbol for order in orders if order.status != 'canceled']

messages = []

for symbol in symbols:
    minute_bars = api.get_barset(symbol, '1Min', limit=1000, start=pd.Timestamp(current_date), end=pd.Timestamp(current_date)).df

    #Getting Range of First 15 Minutes
    opening_range_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index < end_minute_bar)
    opening_range_bars = minute_bars.loc[opening_range_mask]

    #Finding High, Low and Spread in First 15 Minutes
    opening_range_low = opening_range_bars[symbol,'low'].min()
    opening_range_high = opening_range_bars[symbol,'high'].max()
    opening_range = opening_range_high - opening_range_low

    #Finding Range After First 15 Minutes
    after_opening_range_mask = minute_bars.index >= end_minute_bar
    after_opening_range_bars = minute_bars.loc[after_opening_range_mask]

    #Finding Range Above high of First 15 Minutes
    after_opening_range_breakout = after_opening_range_bars[after_opening_range_bars[symbol]['close'] > opening_range_high]

    #Finding Limit Price of Trade, First Breakout Above High in First 15 Minutes
    if not after_opening_range_breakout.empty:

        if symbol not in existing_orders_symbols:
            limit_price = after_opening_range_breakout[symbol]['close'][0]

            message = f"Placing Order for {symbol} at {limit_price}, Closed Above {opening_range_high}\n{after_opening_range_breakout.index[0]}\n\n"
            messages.append(message)

            #Printing For LOG
            print(message)
            # Placing Trade
            try:
                api.submit_order(
                    symbol=symbol,
                    side='buy',
                    type='limit',
                    qty=calculate_quantity(limit_price),
                    time_in_force='day',
                    order_class='bracket',
                    limit_price = limit_price,
                    take_profit=dict(
                        limit_price= limit_price + opening_range,
                    ),
                    stop_loss=dict(
                        stop_price= limit_price - opening_range,
                    )
            )
            except Exception as e:
                print(f"Could not submit order {e}")
        else:
            print(f"Already an Order for {symbol}, skipping")

with smtplib.SMTP_SSL(config.EMAIL_HOST, config.EMAIL_PORT, context=context) as server:
    server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
    email_message = f"Subject: Trade Notifications for {current_date}\n\n"
    email_message += "\n\n".join(messages)


    print(messages)
    # if messages :
        #SEND EMAIL
        #server.sendmail(config.EMAIL_ADDRESS, config.EMAIL_ADDRESS, email_message)
        #server.semdmail(config.EMAIL_ADDRESS, config.EMAIL_SMS, email_message)

        #SEND TWILIO SMS
            
       #Twilio Connection
    client = Client(config.account_sid, config.auth_token)
    message = client.messages.create(
        from_=config.TWILIO_NUMBER,
        to=config.PHONE_NUMBER,
        body= email_message
    )
    print(message.sid)
    # else:
    #     print("No Trade Notifications")

