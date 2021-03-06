#!/usr/bin/python3.7
from cryptrade.coinbase import CBApiCreator
from cryptrade.binance import BinApiCreator
from cryptrade.kraken import KrakenApiCreator
from cryptrade.bitfinex import BfxApiCreator
from cryptrade.monitor import TickerMonitor

import asyncio
import json

credentials = json.load(open("credentials.json", "r"))

APIs = {
    "coinbase": CBApiCreator(),
    "binance": BinApiCreator(),
    "kraken": KrakenApiCreator(),
    "bitfinex": BfxApiCreator()
}

client = {}
product = {}
ticker = {}
ticker_log = {}
trading_currency = {}
buying_currency = {}

for exchange, api_factory in APIs.items():
    client[exchange] = api_factory.create_trade_client(credentials)
    trading_currency[exchange] = api_factory.create_currency("BTC")
    buying_currency[exchange] = api_factory.create_currency("EUR")
    product[exchange] = api_factory.create_product(client[exchange], trading_currency[exchange],
                                                   buying_currency[exchange])
    ticker[exchange] = api_factory.create_ticker(client[exchange], product[exchange])
    ticker_log[exchange] = TickerMonitor(ticker[exchange], exchange + " / " + product[exchange].prod_id, 24 * 60 * 60)


async def report(interval):
    while True:
        for k, v in APIs.items():
            print(ticker_log[k])
        await asyncio.sleep(interval)


async def main():
    ticker_tasks = [ticker[k].produce(15) for k, v in APIs.items()]
    output_tasks = [report(15)]
    tasks = ticker_tasks + output_tasks
    await asyncio.gather(*tasks)

asyncio.run(main())
