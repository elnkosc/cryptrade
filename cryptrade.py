#!/usr/bin/python3.7
from cryptrade.monitor import Transactions
from cryptrade.parameters import CommandLine
from cryptrade.logging import Logger, DEBUG_BASIC, DEBUG_DETAILED
from cryptrade.exceptions import ParameterError
from cryptrade.coinbase import CBApiCreator
from cryptrade.binance import BinApiCreator
from cryptrade.kraken import KrakenApiCreator
from cryptrade.bitfinex import BfxApiCreator

import time
import json

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
product = api_factory.create_product(client, parameters.trading_currency, parameters.buying_currency)
ticker = api_factory.create_ticker(client, product)
account = api_factory.create_account(client)

buying = Transactions("buy", api_factory.maker_fee())
selling = Transactions("sell", api_factory.maker_fee())

while True:
    ticker.update()
    logger.log(DEBUG_DETAILED, f"{ticker}")

    account.update()
    logger.log(DEBUG_DETAILED, f"{account}")

    # make buy order
    buy_price = ticker.bid * (1 - parameters.delta)
    buy_amount = parameters.basic_amount
    buy_order = api_factory.create_order(client, product, "buy", buy_price, buy_amount)
    logger.log(DEBUG_DETAILED, f"{buy_order}")

    # make sales order
    sell_price = ticker.ask * (1 + parameters.delta)
    sell_amount = parameters.basic_amount
    sell_order = api_factory.create_order(client, product, "sell", sell_price, sell_amount)
    logger.log(DEBUG_DETAILED, f"{sell_order}")

    check_orders = True
    while check_orders:
        time.sleep(60)

        if sell_order.created:
            if sell_order.status():
                check_orders = False
                selling.add(sell_order.filled_size, sell_order.executed_value)
                logger.alert(DEBUG_BASIC, "SELL-ORDER FINISHED", f"{sell_order}")
            elif sell_order.error:
                logger.log(DEBUG_DETAILED, sell_order.message)

        if buy_order.created:
            if buy_order.status():
                check_orders = False
                buying.add(buy_order.filled_size, buy_order.executed_value)
                logger.alert(DEBUG_BASIC, "BUY-ORDER FINISHED", f"{buy_order}")
            elif buy_order.error:
                logger.log(DEBUG_DETAILED, buy_order.message)

    buy_order.cancel()
    sell_order.cancel()
    logger.log(DEBUG_DETAILED, f"{buying}\n{selling}\n")
