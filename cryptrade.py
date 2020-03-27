#!/usr/bin/python3.7
from trade import coinbase
from trade import binance
from trade import logging
from trade.parameters import CommandLine
import sys
import time

# Define general preferences
WAIT_TIME = 5             # refresh time (in seconds) for trade update check
SINGLE_ORDER_WAIT = 3600  # max time before cancelling a single order (when empty orders are allowed)

# Define user credentials for Coinbase Pro Default account
CB_API_KEY = "f838c0a61cff1238686a55ffa3034cf1"
CB_API_SECRET = "/RisYHuXlEbiWVr4Ifsj+Al5aXCLOiL7pOJZGlnuQdVvCErrKxBU0ksulFiEww1hdOe5xV9Am8WSiBBSXbWRdQ=="
CB_API_PASS = "41dyi6ndhxs"

# Define user credentials for Binance account
BIN_API_KEY = "M9yDcO7zYm0RblzssDipFj3HnFUGsCWyV9YQ983onBo1MwYen4Ggnq8wULx44JZI"
BIN_API_SECRET = "H1BntqKYOBlkxb1r63PDvCtj9H8J4rIA5nibvRCzRZji3ZCeXUICCEaSVOYzyqhV"

# API key for alerts via pushbullet service
PUSH_BULLET_API_KEY = "o.DO1wLeDTw4k2WcO20MKCQLsYVjTpwt63"

# create global object instances
parameters = CommandLine()
logger = logging.Logger(parameters.logging_level)

# create abstract factory for API instantiation
if parameters.exchange == "coinbase":
    api_factory = coinbase.CBApiCreator()
    api_key = CB_API_KEY
    api_secret = CB_API_SECRET
    api_pass = CB_API_PASS
elif parameters.exchange == "binance":
    api_factory = binance.BinApiCreator()
    api_key = BIN_API_KEY
    api_secret = BIN_API_SECRET
    api_pass = None
else:
    raise AttributeError("Invalid argument: exchange unknown")

# create the concrete API interfaces
trade_client = api_factory.create_trade_client(api_key, api_secret, api_pass)
trade_product = api_factory.create_product(trade_client, parameters.trading_currency, parameters.buying_currency,
                                           parameters.basic_amount)
ticker = api_factory.create_ticker(trade_client, trade_product)
account = api_factory.create_account(trade_client, trade_product)
buying = api_factory.create_accumulator("buy")
selling = api_factory.create_accumulator("sell")

try:
    ticker.update()

    # wait for right market price to start
    wait_msg = False
    while ticker.price > parameters.high_price or ticker.price < parameters.low_price:
        if not wait_msg:
            wait_msg = True
            logger.log(logging.BASIC, f"Waiting for price to be in range {parameters.low_price:6.4f} - "
                                      f"{parameters.high_price:6.4f}")
        time.sleep(WAIT_TIME)
        ticker.update()

    account.update(ticker.price)

    # start trading!
    buy_units = parameters.basic_units
    sell_units = parameters.basic_units
    trading = True
    while trading:

        ticker.update()
        logger.log(logging.DETAILED, f"{ticker}")

        # make buy order
        buy_price = ticker.bid * (1 - parameters.delta)
        buy_amount = min(max(buy_units, parameters.basic_units) * parameters.basic_amount,
                         account.buying_amount / buy_price)
        buy_order = api_factory.create_order(trade_client, trade_product, "buy", buy_price, buy_amount)
        logger.log(logging.DETAILED, f"{buy_order}")

        # make sales order
        sell_price = ticker.ask * (1 + parameters.delta)
        sell_amount = min(max(sell_units, parameters.basic_units) * parameters.basic_amount,
                          account.trading_amount)
        sell_order = api_factory.create_order(trade_client, trade_product, "sell", sell_price, sell_amount)
        logger.log(logging.DETAILED, f"{sell_order}")

        # allow 1 failed order when empty orders are allowed
        single_order = False
        if buy_order.error and sell_order.error:
            trading = False
        elif buy_order.error or sell_order.error:
            trading = parameters.empty_order
            single_order = True

        check_orders = True
        total_wait = 0
        while trading and check_orders:
            time.sleep(WAIT_TIME)
            total_wait += WAIT_TIME

            if single_order and total_wait > SINGLE_ORDER_WAIT:
                check_orders = False

            if not sell_order.error:
                if sell_order.status():
                    check_orders = False
                    selling.add(sell_order.filled_size, sell_order.executed_value)

                    if sell_order.filled_size > 0:
                        buy_units -= 1
                        sell_units += 1

                    logger.alert(logging.BASIC, "SELL-ORDER COMPLETE", f"{sell_order}")

            if not buy_order.error:
                if buy_order.status():
                    check_orders = False
                    buying.add(buy_order.filled_size, buy_order.executed_value)

                    if buy_order.filled_size > 0:
                        sell_units -= 1
                        buy_units += 1

                    logger.alert(logging.BASIC, "BUY-ORDER COMPLETE", f"{buy_order}")

        # cancel any (matching) order(s)
        sell_order.cancel()
        buy_order.cancel()

        # account.update(ticker.price)
        logger.log(logging.DETAILED, f"{account}\n{buying}\n{selling}\n")

    logger.alert(logging.BASIC, "TRADING ABORTED!",
                 f"Trading result : {selling.value - selling.fee - buying.value - buying.fee:6.2f}")

except Exception:
    trade_client.cancel_all(trade_product)
    logger.log(logging.BASIC, f"Exception raised: {sys.exc_info()[0]}")
