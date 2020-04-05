#!/usr/bin/python3.7
from trade import coinbase
from trade import binance
from trade import kraken
from trade import logging
from trade.parameters import CommandLine
import sys
import time
import json

# store all your API credentials in json file!
credentials = json.load(open(__file__.replace(".py", ".json"), "r"))

# create global object instances
parameters = CommandLine()
logger = logging.Logger(parameters.logging_level)

APIs = {
    "coinbase": coinbase.CBApiCreator(),
    "binance": binance.BinApiCreator(),
    "kraken": kraken.KrakenApiCreator()
}

# create abstract factory for API instantiation
if parameters.exchange in APIs:
    api_factory = APIs[parameters.exchange]
else:
    raise AttributeError("Invalid argument: exchange unknown")

# create the concrete API interfaces
trade_client = api_factory.create_trade_client(credentials)
trade_product = api_factory.create_product(trade_client, parameters.trading_currency, parameters.buying_currency)
ticker = api_factory.create_ticker(trade_client, trade_product)
account = api_factory.create_account(trade_client, trade_product)
buying = api_factory.create_transaction_monitor("buy")
selling = api_factory.create_transaction_monitor("sell")

try:
    ticker.update()
    account.update(ticker.price)

    trading = True
    while trading:

        ticker.update()
        logger.log(logging.DETAILED, f"{ticker}")

        # make buy order
        buy_price = min(parameters.high_price, ticker.bid * (1 - parameters.delta))
        buy_amount = min(parameters.basic_amount, account.buying_amount / buy_price)
        buy_order = api_factory.create_order(trade_client, trade_product, "buy", buy_price, buy_amount)

        # make sales order
        sell_price = max(parameters.low_price, ticker.ask * (1 + parameters.delta))
        sell_amount = min(parameters.basic_amount, account.trading_amount)
        sell_order = api_factory.create_order(trade_client, trade_product, "sell", sell_price, sell_amount)

        check_orders = True
        total_wait = 0
        while trading and check_orders:
            time.sleep(10)

            if sell_order.created:
                if sell_order.status():
                    check_orders = False
                    selling.add(sell_order.filled_size, sell_order.executed_value)
                    logger.alert(logging.BASIC, "SELL-ORDER FINISHED", f"{sell_order}")
                elif sell_order.error:
                    logger.log(logging.DETAILED, sell_order.message)

            if buy_order.created:
                if buy_order.status():
                    check_orders = False
                    buying.add(buy_order.filled_size, buy_order.executed_value)
                    logger.alert(logging.BASIC, "BUY-ORDER FINISHED", f"{buy_order}")
                elif buy_order.error:
                    logger.log(logging.DETAILED, buy_order.message)

        # cancel any (matching) order(s)
        sell_order.cancel()
        buy_order.cancel()

        account.update(ticker.price)

    logger.alert(logging.BASIC, "TRADING ABORTED!")

except Exception:
    logger.log(logging.BASIC, f"Exception raised: {sys.exc_info()[0]}")
