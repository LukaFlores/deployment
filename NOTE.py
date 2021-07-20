# import config, tulipy 
# import alpaca_trade_api as tradeapi
# from helper import calculate_quantity

# api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)


# symbols = ['SPY', 'IWM', 'DIA']

# for symbol in symbols:
#     api.submit_order()

#     quote = api.get_last_quote(symbol)

#     api.submit_order(
#         symbol = symbol
#         side = 'buy'
#         type = 'market'
#         qty = calculate_quantity(quote.bidprice)
#         time_in_force = 'day'

#     )

# orders = api.list_orders()
# positions = api.list_positions() take qty/2 for partial profits

#ATR AVERAGE TRUE RANGE

# minute_bars = api.get_barset(symbol, '1Min', limit=390, start=pd.Timestamp(start_minute_bar), end=pd.Timestamp(end_minute_bar)).df
# atr = tulipy.atr(high,low,close, period)




#TRAILING STOP EXAMPLES
# api.submit_order(
#         symbol = symbol
#         side = 'sell'
#         type = 'trailing_stop'
#         trail_price = '0.2'
#         qty = calculate_quantity(quote.bidprice)
#         time_in_force = 'day'
#     )


# api.submit_order(
#         symbol = symbol
#         side = 'sell'
#         type = 'trailing_stop'
#         trail_percent = '0.2'
#         qty = calculate_quantity(quote.bidprice)
#         time_in_force = 'day'
#     )
