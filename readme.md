cryptrade is a project that offers a a high level abstraction of a crypto-currency trade API. It offers classes for:
* Accounts, holding both fiat currency (EUR, USD, etc) as well as crypto currencies (BTH, ETH, etc)
* Products, representing what you can actually trade on a crypto exchange, eg. BTC-EUR (buy BTC pay in EUR) or ETH-BTC (buy ETH pay in BTC)
* Orders, the actual trade (buying or selling) of crypto currency
* Tickers, providing 'real-time' info on market-price and bid/ask prices

The (abstract) exchange interfaces provide the basic validations needed to successfully trade on an online exchange, make the necessary API calls, and handle the responses. To make the underlying exchange transparent, the API is provided using an Abstract Factory pattern. 

On top of this, classes are provided for:
* Ticker, Account, and Order monitoring (implemented using the Observer pattern)
* Transactions, representing the total of buying/selling transactions
* Logger, providing logging classes for logging to console, file, and through PushBullet. These classes are implemented as Singletons.

At this moment, the following crypto exchanges are supported:
* Coinbase Pro (http://pro.coinbase.com), formerly known as GDAX
* Binance (http://binance.com)
* Kraken (http://www.kraken.com)
* Bitfinex (http://bitfinex.com)

The interfaces can be used in a synchronous manner, however they also include asynchronous interfaces so it is possible to make use of the asyncio package for cooperative multitasking using an event-loop.

Two sample programs are included:
* cryptrade.py, a sample program that shows the usage of this package. It's operation can be directed using commandline parameters. It will trade according a very simple algorithm.
~~~~
usage: cryptrade.py [-h] [-c {eur,btc}] [-d TRADE_DELTA] [-a TRADE_AMOUNT]
                    exchange currency

positional arguments:
  exchange              Exchange to trade on. Currently supported: coinbase,
                        binance, kraken, bitfinex
  currency              Currency to trade in: btc, eth, xrp, ltc, bch, ...

optional arguments:
  -h, --help            show this help message and exit
  -c CURRENCY, --currency CURRENCY
                        (Crypto) currency to use for buying.
  -d TRADE_DELTA, --delta TRADE_DELTA
                        Percentage (0.0 < trade < 100.0) by which market price
                        should change before making a trade (accepts
                        fractional numbers).
  -a TRADE_AMOUNT, --amount TRADE_AMOUNT
                        Initial amount to start trading with (btc>=0.001,
                        eth>=0.01, xrp>=1, ltc=0.1).
~~~~
* tickermonitor.py, shows how the asynchronous interfaces can be used by implementing a tickermonitor for all supported exchanges in parallel.

Make sure you provide your credentials (API key & secret) before using it. They should be stored in a json file like:
~~~~
{
    "coinbase" : 
     {
        "api_key" : "your api key",
        "api_secret" : "your api secret",
        "api_pass" : "you api password"
    },
    "binance" :
    {
        "api_key" : "your api key",
        "api_secret" : "your api secret"
    },
    "kraken" :
    {
        "api_key" : "your api key",
        "api_secret" : "your api secret"
    },
    "bitfinex" :
    {
        "api_key" : "your api key",
        "api_secret" : "your api secret"
    },
    "pushbullet" :
    {
        "api_key" : "your api key"
    }
}
~~~~

The cryptrade module contains the following packages:
* logging (logging interfaces)
* parameters (interfaces for dealing with -commandline- parameters)
* exceptions (containing module-specific exceptions)
* observers (containing base classes for observables and observers as well as the monitroing classes)
* exchange_api (containing the abstract interface for trading)
* binance (containing concrete implementation for Binance)
* bitfinex (containing concrete implementation for Bitfinex)
* kraken (containing concrete implementation for Kraken)
* coinbase (containing concrete implementation for Coinbase Pro)

This project uses the official python interface for [binance.com](http://python-binance.readthedocs.io/en/latest) as well as the 'unofficial' python interface for [Coinbase Pro](https://github.com/danpaquin/coinbasepro-python) by Daniel Paquin, the official python interface for [Kraken.com](https://github.com/veox/python3-krakenex), and the official python interface from [bitfinex.com](https://github.com/bitfinexcom/bitfinex-api-py).

Special requests or questions: send me a message!

Want to stimulate the ongoing development? Your BTCs are welcome! Send them to bitcoin:15pqCjD7pPPraGJ8T4yfbkrtFTBX8M4jyw
