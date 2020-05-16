#!/usr/bin/python3.7
from cryptrade.logging import Logger, DEBUG_BASIC, DEBUG_DETAILED
from cryptrade.monitor import Transactions
from cryptrade.parameters import CommandLine
from cryptrade.exceptions import ParameterError
from cryptrade.coinbase import CBApiCreator
from cryptrade.binance import BinApiCreator
from cryptrade.kraken import KrakenApiCreator
from cryptrade.bitfinex import BfxApiCreator

import time
import json

# Define general preferences
WAIT_TIME = 60            # refresh time (in seconds) for cryptrade update check
SINGLE_ORDER_WAIT = 7200  # max time before cancelling a single order (when empty orders are allowed)

APIs = {
    "coinbase": CBApiCreator(),
    "binance": BinApiCreator(),
    "kraken": KrakenApiCreator(),
    "bitfinex": BfxApiCreator()
}

parameters = CommandLine()
logger = Logger(parameters.logging_level)

credentials = json.load(open(__file__.replace(".py", ".json"), "r"))

if parameters.exchange in APIs:
    api_factory = APIs[parameters.exchange]
else:
    raise ParameterError("exchange-name unknown or unsupported")

client = api_factory.create_trade_client(credentials)
trading_currency = api_factory.create_currency(parameters.trading_currency)
buying_currency = api_factory.create_currency(parameters.buying_currency)
product = api_factory.create_product(client, trading_currency, buying_currency)
ticker = api_factory.create_ticker(client, product)
account = api_factory.create_account(client)

buying = Transactions("buy", api_factory.maker_fee())
selling = Transactions("sell", api_factory.maker_fee())

buy_units = parameters.basic_units
sell_units = parameters.basic_units
trading = True
while trading:

    logger.log(DEBUG_BASIC, "********** New Trade **********")

    ticker.update()
    logger.log(DEBUG_DETAILED, f"{ticker}")

    account.update()
    logger.log(DEBUG_DETAILED, f"{account}")

    # make buy order
    buy_price = min(parameters.high_price, ticker.bid * (1 - parameters.delta))
    buy_amount = min(buy_units * parameters.basic_amount,
                     account.currency_balance(parameters.buying_currency) / buy_price)
    buy_order = api_factory.create_order(client, product, "buy", buy_price, buy_amount)
    logger.log(DEBUG_DETAILED, f"{buy_order}")

    # make sales order
    sell_price = max(parameters.low_price, ticker.ask * (1 + parameters.delta))
    sell_amount = min(sell_units * parameters.basic_amount, account.currency_balance(parameters.trading_currency))
    sell_order = api_factory.create_order(client, product, "sell", sell_price, sell_amount)
    logger.log(DEBUG_DETAILED, f"{sell_order}")

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
                    if buy_units > parameters.basic_units:
                        buy_units -= 1
                    sell_units += 1
                logger.alert(DEBUG_BASIC, "SELL-ORDER FINISHED", f"{sell_order}")
            elif sell_order.error:
                logger.log(DEBUG_DETAILED, sell_order.message)

        if buy_order.created:
            if buy_order.status():
                check_orders = False
                buying.add(buy_order.filled_size, buy_order.executed_value)
                if buy_order.filled_size > 0:
                    if sell_units > parameters.basic_units:
                        sell_units -= 1
                    buy_units += 1
                logger.alert(DEBUG_BASIC, "BUY-ORDER FINISHED", f"{buy_order}")
            elif buy_order.error:
                logger.log(DEBUG_DETAILED, buy_order.message)

    buy_order.cancel()
    sell_order.cancel()
    logger.log(DEBUG_DETAILED, f"{buying}\n{selling}\n")

logger.alert(DEBUG_BASIC, "TRADING ABORTED! Trading result: ",
             f"{selling.value - selling.total_fee - buying.value - buying.total_fee:6.2f}")
