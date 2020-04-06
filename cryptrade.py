#!/usr/bin/python3.7
from trade import coinbase
from trade import binance
from trade import kraken
from trade import logging
from trade.parameters import CommandLine
from trade import ParameterError

import time
import json

# Define general preferences
WAIT_TIME = 15            # refresh time (in seconds) for trade update check
SINGLE_ORDER_WAIT = 7200  # max time before cancelling a single order (when empty orders are allowed)

APIs = {
    "coinbase": coinbase.CBApiCreator(),
    "binance": binance.BinApiCreator(),
    "kraken": kraken.KrakenApiCreator()
}

parameters = CommandLine()
logger = logging.Logger(parameters.logging_level)

credentials = json.load(open(__file__.replace(".py", ".json"), "r"))

if parameters.exchange in APIs:
    api_factory = APIs[parameters.exchange]
else:
    raise ParameterError("exchange-name unknown or unsupported")

trade_client = api_factory.create_trade_client(credentials)
trade_product = api_factory.create_product(trade_client, parameters.trading_currency, parameters.buying_currency)
ticker = api_factory.create_ticker(trade_client, trade_product)
account = api_factory.create_account(trade_client, trade_product)
buying = api_factory.create_transaction_monitor("buy")
selling = api_factory.create_transaction_monitor("sell")

buy_units = parameters.basic_units
sell_units = parameters.basic_units
trading = True
while trading:

    ticker.update()
    logger.log(logging.DETAILED, f"{ticker}")

    account.update(ticker.price)
    logger.log(logging.DETAILED, f"{account}")

    # make buy order
    buy_price = min(parameters.high_price, ticker.bid * (1 - parameters.delta))
    buy_amount = min(max(buy_units, parameters.basic_units) * parameters.basic_amount,
                     account.buying_amount / buy_price)
    buy_order = api_factory.create_order(trade_client, trade_product, "buy", buy_price, buy_amount)
    logger.log(logging.DETAILED, f"{buy_order}")

    # make sales order
    sell_price = max(parameters.low_price, ticker.ask * (1 + parameters.delta))
    sell_amount = min(max(sell_units, parameters.basic_units) * parameters.basic_amount,
                      account.trading_amount)
    sell_order = api_factory.create_order(trade_client, trade_product, "sell", sell_price, sell_amount)
    logger.log(logging.DETAILED, f"{sell_order}")

    # allow 1 failed order when empty orders are allowed
    single_order = False
    if not buy_order.created and not sell_order.created:
        trading = False
    elif not buy_order.created or not sell_order.created:
        trading = parameters.empty_order
        single_order = True

    check_orders = True
    total_wait = 0
    while trading and check_orders:
        time.sleep(WAIT_TIME)
        total_wait += WAIT_TIME

        if single_order and total_wait > SINGLE_ORDER_WAIT:
            check_orders = False

        if sell_order.created:
            if sell_order.status():
                check_orders = False
                selling.add(sell_order.filled_size, sell_order.executed_value)
                if sell_order.filled_size > 0:
                    buy_units -= 1
                    sell_units += 1
                logger.alert(logging.BASIC, "SELL-ORDER FINISHED", f"{sell_order}")
                buy_order.cancel()
            elif sell_order.error:
                logger.log(logging.DETAILED, sell_order.message)

        if buy_order.created:
            if buy_order.status():
                check_orders = False
                buying.add(buy_order.filled_size, buy_order.executed_value)
                if buy_order.filled_size > 0:
                    sell_units -= 1
                    buy_units += 1
                logger.alert(logging.BASIC, "BUY-ORDER FINISHED", f"{buy_order}")
                sell_order.cancel()
            elif buy_order.error:
                logger.log(logging.DETAILED, buy_order.message)

    logger.log(logging.DETAILED, f"{buying}\n{selling}\n")

logger.alert(logging.BASIC, "TRADING ABORTED! Trading result: ",
             f"{selling.total_value - selling.total_fee - buying.total_valuevalue - buying.total_feefee:6.2f}")
