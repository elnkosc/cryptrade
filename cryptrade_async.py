#!/usr/bin/python3.7
from cryptrade.logging import Logger, DEBUG_BASIC, DEBUG_DETAILED
from cryptrade.monitor import Transactions
from cryptrade.parameters import CommandLine
from cryptrade.exceptions import ParameterError
from cryptrade.exchange_api import Ticker, Order
from cryptrade.coinbase import CBApiCreator
from cryptrade.binance import BinApiCreator
from cryptrade.kraken import KrakenApiCreator
from cryptrade.bitfinex import BfxApiCreator
from cryptrade.observers import Observer

import time
import json
import asyncio


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

class OrderObserver(Observer):
    def __init__(self, o: Order) -> None:
        super().__init__(o)

    async def notify(self, o: Order) -> None:
        pass


class TickerObserver(Observer):
    def __init__(self, t: Ticker) -> None:
        super().__init__(t)

    async def make_order(self):
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
        trading = True
        if not buy_order.created and not sell_order.created:
            trading = False
        elif not buy_order.created or not sell_order.created:
            trading = parameters.empty_order

        if trading = False:
            buy_order.cancel()
            sell_order.cancel()
        else:
            await buy_order.produce(60)
            await sell_order.produce(60)


    async def notify(self, t: Ticker) -> None:
        if parameters.low_price <= t.price <= parameters.high_price:
            await self.make_order()





async def main():
    ticker_observer = TickerObserver(ticker)
    tasks = [ticker.produce(15)]
    await asyncio.gather(*tasks)

asyncio.run(main())




trading = True
while trading:

    logger.log(DEBUG_BASIC, "********** New Trade **********")

    ticker.update()
    logger.log(DEBUG_DETAILED, f"{ticker}")

    account.update()
    logger.log(DEBUG_DETAILED, f"{account}")






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
