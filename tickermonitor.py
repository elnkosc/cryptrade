#!/usr/bin/python3.7
from cryptrade.coinbase import CBApiCreator
from cryptrade.binance import BinApiCreator
from cryptrade.kraken import KrakenApiCreator
from cryptrade.bitfinex import BfxApiCreator
from cryptrade.monitor import TickerMonitor

import asyncio
import json

credentials = json.load(open("cryptrade.json", "r"))

exchanges = ["coinbase", "binance", "kraken", "bitfinex"]

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

for exchange, api_factory in APIs.items():
    client[exchange] = api_factory.create_trade_client(credentials)
    product[exchange] = api_factory.create_product(client[exchange], "BTC", "EUR")
    ticker[exchange] = api_factory.create_ticker(client[exchange], product[exchange])
    ticker_log[exchange] = TickerMonitor(ticker[exchange], exchange, 24 * 60 * 60)


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
