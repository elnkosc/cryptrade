from trade import coinbase
from trade import binance
from trade.parameters import CommandLine
import time
import json

# store all your API credentials in json file!
credentials = json.load(open(__file__.replace(".py", ".json"), "r"))

# create global object instances
parameters = CommandLine()

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
buying = api_factory.create_accumulator("buy")
selling = api_factory.create_accumulator("sell")

try:
    ticker.update()
    account.update(ticker.price)

    # start trading!
    trading = True
    while trading:

        ticker.update()

        # make buy order
        buy_price = ticker.bid * (1 - parameters.delta)
        buy_amount = min(parameters.basic_amount, account.buying_amount / buy_price)
        buy_order = api_factory.create_order(trade_client, trade_product, "buy", buy_price, buy_amount)

        # make sales order
        sell_price = ticker.ask * (1 + parameters.delta)
        sell_amount = min(parameters.basic_amount, account.trading_amount)
        sell_order = api_factory.create_order(trade_client, trade_product, "sell", sell_price, sell_amount)

        # check on failure
        if buy_order.error or sell_order.error:
            trading = False

        check_orders = True
        while trading and check_orders:
            time.sleep(5)

            if sell_order.status():
                check_orders = False
                selling.add(sell_order.filled_size, sell_order.executed_value)
                buy_order.cancel()

            if buy_order.status():
                check_orders = False
                buying.add(buy_order.filled_size, buy_order.executed_value)
                sell_order.cancel()

        account.update(ticker.price)

except Exception:
    trade_client.cancel_all(trade_product)
