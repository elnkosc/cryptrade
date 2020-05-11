import argparse
from cryptrade.exceptions import ParameterError


class TradeParameters:
    def __init__(self):
        self._currency = "BTC"
        self._exchange = "coinbase"
        self._delta = 1.5
        self._basic_amount = 0.001
        self._buying_currency = "EUR"

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
    def delta(self):
        return self._delta

    @property
    def basic_amount(self):
        return self._basic_amount



class CommandLine(TradeParameters):
    def __init__(self):
        super().__init__()

        parser = argparse.ArgumentParser(
            description="Trade automatically on Coinbase Pro in multiple crypto currencies.",
            epilog="This application will cryptrade the selected currency and volumes. It will create a buying and\n"
                   "sales order that are a specified percentage below and over the market price. When an order\n"
                   "is matched, a new pair of orders is created. The amount of units to cryptrade is increased by one\n"
                   "for the next consecutive order-type while for the other order-type it is decreased by one.\n"
                   "Happy trading!")

        # positional parameters
        parser.add_argument("exchange", type=str, action="store", metavar="exchange",
                            choices=["coinbase", "binance", "kraken", "bitfinex"],
                            help="Exchange to cryptrade on. Currently supported: Coinbase Pro, Binance, Bitfinex")
        parser.add_argument("currency", type=str, action="store", metavar="currency",
                            help="Currency to cryptrade in (btc, eth, xrp, ltc, bch).")

        # optional parameters
        parser.add_argument("-c", "--currency", dest="buying_currency", type=str, default="eur", action="store",
                            help="(Crypto) currency to use for buying.")
        parser.add_argument("-d", "--delta", dest="trade_delta", type=float, default=1.5, action="store",
                            help="Percentage (0.0 < cryptrade < 100.0) by which market price should change "
                                 "before making a cryptrade (accepts fractional numbers).")
        parser.add_argument("-a", "--amount", dest="trade_amount", type=float, default=0.001, action="store",
                            help="Initial amount to start trading with (btc>=0.001, eth>=0.01, xrp>=1, ltc=0.1).")
        parser.add_argument("-l", "--logging", dest="logging_level", type=int, default=1,
                            action="store", choices=[1, 2, 3],
                            help="Logging level 0=Off, 1=Basic, 2=Detailed.")

        args = parser.parse_args()

        self._currency = args.currency.upper()
        self._exchange = args.exchange.lower()
        self._delta = args.trade_delta / 100
        self._basic_amount = args.trade_amount
        self._buying_currency = args.buying_currency.upper()

        if self._delta <= 0 or self._delta >= 1:
            raise ParameterError("cryptrade, cryptrade-delta should be between 0 & 100%")
