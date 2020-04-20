#!/usr/bin/python3.7
from cryptrade import History, Observer, coinbase, binance, kraken, bitfinex

import asyncio
import json

credentials = json.load(open("cryptrade.json", "r"))

exchanges = ["coinbase", "binance", "kraken", "bitfinex"]

APIs = {
    "coinbase": coinbase.CBApiCreator(),
    "binance": binance.BinApiCreator(),
    "kraken": kraken.KrakenApiCreator(),
    "bitfinex": bitfinex.BfxApiCreator()
}

client = {}
product = {}
ticker = {}
ticker_log = {}
account = {}
account_log = {}
ticker_observer = {}
account_observer = {}

for exchange, api_factory in APIs.items():
    client[exchange] = api_factory.create_trade_client(credentials)
    product[exchange] = api_factory.create_product(client[exchange], "BTC", "EUR")
    ticker[exchange] = api_factory.create_ticker(client[exchange], product[exchange])
    ticker_observer[exchange] = Observer(ticker[exchange])
    ticker_log[exchange] = History(exchange, ticker[exchange], 60, 1440)
    account[exchange] = api_factory.create_account(client[exchange])
    account_observer[exchange] = Observer(account[exchange])
    account_log[exchange] = History(exchange, account[exchange], 60, 1440)


async def main():
    ticker_tasks = [ticker[k].produce(10) for k, v in APIs.items()]
    account_tasks = [account[k].produce(10) for k, v in APIs.items()]
    tasks = ticker_tasks + account_tasks
    await asyncio.wait(tasks)


asyncio.run(main())
