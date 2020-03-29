cryptrade is a project that offers a a high level abstraction of a cryptocurrency trade API. It offers classes for:
* Accounts, holding both fiat currency (EUR, USD, ..) as well as crypto currencies (BTH, ETH, ...)
* Products, representing what you can actually trade on a crypto exchange, eg. BTC-EUR (buy BTC pay in EUR) or ETH-BTC (buy ETH pay in BTC)
* Orders, the actual trade (buying or selling) of crypto currency
* Ticker, providing 'real-time' info on market-price and bid/ask prices

These (abstract) interfaces provide the basic validations needed to successfully trade on an online exchange, make the necessary API calls, and handle the responses.

Besides trading objects, there are also (abstract) classes for getting/setting global trade parameters (e.g. using the commandline) and logging information for debug purposes (stdout, to file, PushBullet)

At this moment, the following crypto exchanges are supported:
* Coinbase Pro (http://pro.coinbase.com), formerly known ad GDAX
* Binance (http://binance.com)

The classes for these exchanges are offered through an abstract factory so you can transparently switch in your client program between the different exchanges (or use them in parallel).

cryptrade.py is a sample program that is added to show the usage of this package. It's operation can be directed using commandline parameters. Use "python cryptrade.py -h" for an overview of its usage.

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
    }
}
~~~~

This project uses the official python interface for [binance.com](http://python-binance.readthedocs.io/en/latest) as well as the 'unofficial' python interface for [Coinbase Pro](https://github.com/danpaquin/coinbasepro-python) by Daniel Paquin.
