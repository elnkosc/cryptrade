import argparse

class TradeParameters:
    def __init__(self):
        self._logging_level = 1
        self._currency = "BTC"
        self._exchange = "coinbase"
        self._empty_order = False
        self._low_price = 0
        self._high_price = 1000000
        self._delta = 1.5
        self._basic_amount = 0.001
        self._basic_units = 1
        self._buying_currency = "EUR"

    @property
    def logging_level(self):
        return self._logging_level

    @property
    def exchange(self):
        return self._exchange

    @property
    def trading_currency(self):
        return self._currency

    @property
    def buying_currency(self):
        return self._buying_currency

    @property
    def empty_order(self):
        return self._empty_order

    @property
    def low_price(self):
        return self._low_price

    @property
    def high_price(self):
        return self._high_price

    @property
    def delta(self):
        return self._delta

    @property
    def basic_amount(self):
        return self._basic_amount

    @property
    def basic_units(self):
        return self._basic_units


class CommandLine(TradeParameters):
    def __init__(self):
        super().__init__()

        parser = argparse.ArgumentParser(
            description="Trade automatically on Coinbase Pro in multiple crypto currencies.",
            epilog="This application will trade the selected currency and volumes. It will create a buying and\n"
                   "sales order that are a specified percentage below and over the market price. When an order\n"
                   "is matched, a new pair of orders is created. The amount of units to trade is increased by one\n"
                   "for the next consecutive order-type while for the other order-type it is decreased by one.\n"
                   "Happy trading!")

        # positional parameters
        parser.add_argument("exchange", type=str, action="store", metavar="exchange",
                            choices=["coinbase", "binance", "kraken"],
                            help="Exchange to trade on. Currently supported: Coinbase Pro, Binance")
        parser.add_argument("currency", type=str, action="store", metavar="currency",
                            choices=["btc", "eth", "xrp", "ltc", "bch"],
                            help="Currency to trade in (btc, eth, xrp, ltc, bch).")

        # optional paramaters
        parser.add_argument("-c", "--currency", dest="buying_currency", type=str, default="eur", action="store",
                            choices=["eur", "btc"],
                            help="(Crypto) currency to use for buying.")
        parser.add_argument("-d", "--delta", dest="trade_delta", type=float, default=1.5, action="store",
                            help="Percentage (0.0 < trade < 100.0) by which market price should change "
                                 "before making a trade (accepts fractional numbers).")
        parser.add_argument("-a", "--amount", dest="trade_amount", type=float, default=0.001, action="store",
                            help="Initial amount to start trading with (btc>=0.001, eth>=0.01, xrp>=1, ltc=0.1).")
        parser.add_argument("-u", "--units", dest="trade_units", type=int, default=1, action="store",
                            help="Initial amount of units to start trading with (> 0).")
        parser.add_argument("-l", "--logging", dest="logging_level", type=int, default=1,
                            action="store", choices=[1, 2, 3],
                            help="Logging level 0=Off, 1=Basic, 2=Detailed.")
        parser.add_argument("-e", "--empty", dest="empty_order", action="store_true",
                            help="When specified, allow trading when buying or sales order cannot be made due to "
                                 "insufficient funds.")
        parser.add_argument("-ph", "--high_price", dest="high_price", type=float, default=100000.0, action="store",
                            help="Start trading when market price is below this value")
        parser.add_argument("-pl", "--low_price", dest="low_price", type=float, default=0.0, action="store",
                            help="Start trading when market price is above this value")

        args = parser.parse_args()

        self._logging_level = args.logging_level
        self._currency = args.currency.upper()
        self._exchange = args.exchange.lower()
        self._empty_order = args.empty_order
        self._low_price = args.low_price
        self._high_price = args.high_price
        self._delta = args.trade_delta / 100
        self._basic_amount = args.trade_amount
        self._basic_units = args.trade_units
        self._buying_currency = args.buying_currency.upper()

        if self._low_price < 0:
            raise AttributeError("Invalid argument: low_price, minimum price cannot be negative")

        if self._high_price < self._low_price:
            raise AttributeError("Invalid argument: high_price, should be higher than low_price")

        if self._delta <= 0 or self._delta >= 1:
            raise AttributeError("Invalid argument: trade, trade-delta should be between 0 & 100%")

        if self._basic_units <= 0:
            raise AttributeError("Invalid argument: units, should be higher than 0")
