from setuptools import setup
import sys

if sys.version_info[0] < 3:
    with open('readme.md') as f:
        long_description = f.read()
else:
    with open('readme.md', encoding='utf-8') as f:
        long_description = f.read()
setup(
    name='cryptrade',
    version='1.103',
    packages=['cryptrade'],
    url='https://github.com/elnkosc/cryptrade/',
    license='GNU General Public License v3.0',
    author='Koen Schilders',
    author_email='koen@schilders.org',
    description='Basic crypto trading API for developing trading bots with transparent access to Coinbase Pro, Binance, Kraken, and Bitfinex',
    long_description=long_description,
    long_description_content_type='text/markdown'
)
