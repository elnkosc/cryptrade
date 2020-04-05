cryptrade is a project that offers a a high level abstraction of a cryptocurrency trade API. It offers classes for:
* Accounts, holding both fiat currency (EUR, USD, ..) as well as crypto currencies (BTH, ETH, ...)
* Products, representing what you can actually trade on a crypto exchange, eg. BTC-EUR (buy BTC pay in EUR) or ETH-BTC (buy ETH pay in BTC)
* Orders, the actual trade (buying or selling) of crypto currency
* Ticker, providing 'real-time' info on market-price and bid/ask prices
* Transactions, representing the total of buying/selling transactions

These (abstract) interfaces provide the basic validations needed to successfully trade on an online exchange, make the necessary API calls, and handle the responses.

Besides trading objects, there are also (abstract) classes for getting/setting global trade parameters (e.g. using the commandline) and logging information for debug purposes (stdout, to file, PushBullet)

At this moment, the following crypto exchanges are supported:
* Coinbase Pro (http://pro.coinbase.com), formerly known as GDAX
* Binance (http://binance.com)
* Kraken (http://www.kraken.com)

The classes for these exchanges are offered through an abstract factory so you can transparently switch in your client program between the different exchanges (or use them in parallel).

cryptrade.py is a sample program that is added to show the usage of this package. It's operation can be directed using commandline parameters.
~~~~
usage: cryptrade.py [-h] [-c {eur,btc}] [-d TRADE_DELTA] [-a TRADE_AMOUNT]
                    exchange currency

positional arguments:
  exchange              Exchange to trade on. Currently supported: coinbase,
                        binance, kraken
  currency              Currency to trade in (btc, eth, xrp, ltc, bch).

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
    }
}
~~~~

This project uses the official python interface for [binance.com](http://python-binance.readthedocs.io/en/latest) as well as the 'unofficial' python interface for [Coinbase Pro](https://github.com/danpaquin/coinbasepro-python) by Daniel Paquin and the official python interface for [Kraken.com](https://github.com/veox/python3-krakenex).

Special requests or questions: send me a message!

Want to stimulate the ongoing development? Your BTCs are welcome! Send them to bitcoin:15pqCjD7pPPraGJ8T4yfbkrtFTBX8M4jyw
