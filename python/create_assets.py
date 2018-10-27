import os
import sys
import time
import string
import random
import json
import operator

import cybex
from cybex import Market
from bitshares.exceptions import AssetDoesNotExistsException


CACHED_ASSETS = {}
UNUSED_ASSETS = []

VALID_ACCOUNTS = ["berlin-test{}".format(i) for i in range(1, 6)]


def generate_random_name(length=8):
    return "".join([random.choice(string.ascii_uppercase) for _ in range(length)])


def get_cybex_instance(debug=True):
    if debug is True:
        cybex.cybex.cybex_debug_config('59e27e3883fc5ec4dbff68855f83961303157df9a64a3ecf49982affd8e8d490')
        NODE_URL = "wss://shenzhen.51nebula.com"
        # NODE_URL = "wss://hangzhou.51nebula.com/"
        WALLET_PWD = '123456'
    else:
        pass

    instance = cybex.Cybex(NODE_URL)
    instance.wallet.unlock(WALLET_PWD)
    return instance


def cache_asset(symbol, account=''):
    fname = account + "_sub_assets.db"
    fd = open(fname, "a")
    fd.write(symbol)
    fd.write(",")
    fd.close()


def load_cached_assets(account=''):
    fname = account + "_sub_assets.db"
    try:
        fd = open(fname, "r")
    except:
        return []

    assets = fd.read()
    assets = assets.split(",")
    return assets[:-1]


def create_asset(symbol, instance, account):
    asset = instance.create_asset(symbol=symbol,
                                  precision=0,
                                  max_supply=10000,
                                  core_exchange_ratio={symbol: 100, 'CYB': 1},
                                  account=account)
    asset = cybex.Asset(symbol,
                        cybex_instance=instance)
    return asset


def get_asset(symbol, instance=None, account=None):
    try:
        asset = cybex.Asset(symbol,
                            cybex_instance=instance)
    except AssetDoesNotExistsException:
        if not account:
            raise

        instance.create_asset(symbol=symbol,
                              precision=0,
                              max_supply=10000,
                              core_exchange_ratio={symbol: 100, 'CYB': 1},
                              account=account)

        asset = cybex.Asset(symbol,
                            cybex_instance=instance)

        # cache_asset(symbol, account)
    return asset


def get_market(auction_asset, instance):
    _market = cybex.Market(base=cybex.Asset("CYB"),
                           quote=auction_asset,
                           cybex_instance=instance)
    return _market


def _bid(account, auction_asset, price, amount=1,
         expiration=3600, instance=None, market=None):
    if not market:
        market = get_market(auction_asset, instance)

    market.buy(price, amount, expiration,
               killfill=False, account=account)


def bid(bidder, price, amount=1, host=None, instance=None, use_cached_assets=False):
    if instance is None:
        instance = get_cybex_instance()

    if host is None:
        host = VALID_ACCOUNTS[-1]

    # if use_cached_assets is True:
    #     asset_names = load_cached_assets(host)
    # else:
    #     asset_names = []

    # for name in asset_names:
    #     asset = get_asset(name, instance, host)
    #     CACHED_ASSETS[name] = asset
    #     UNUSED_ASSETS.append(name)

    # asset = None
    # if len(UNUSED_ASSETS) != 0:
    #     name = UNUSED_ASSETS.pop()
    #     asset = CACHED_ASSETS[name]
    # else:

    name = generate_random_name()
    name = "SUB{}".format(name)
    print("Always genrate a random asset {}.".format(name))
    asset = create_asset(name, instance, host)

    _bid(bidder, asset, price, amount=amount, instance=instance)
    resp = dict(bidder=bidder,
                host=host,
                asset_symbol=asset['symbol'],
                asset_id=asset['id'],
                price=price)

    print(resp)
    return json.dumps(resp)


def _deal(account, auction_asset, price, amount=1,
          expiration=3600, instance=None, market=None):
    if isinstance(auction_asset, str):
        auction_asset = cybex.Asset(auction_asset,
                                    cybex_instance=instance)
    if not market:
        market = get_market(auction_asset, instance)



    market.sell(price, amount, expiration,
               killfill=False, account=account)


def deal(asset, price, amount=1, host=None, instance=None):
    if instance is None:
        instance = get_cybex_instance()

    if host is None:
        host = VALID_ACCOUNTS[-1]

    # issue real assets
    try:
        asset = get_asset(asset, instance)
    except:
        raise

    host_instance = cybex.account.Account(host, cybex_instance=instance)
    # we don't have any asset, issue new assets
    if host_instance.balance(asset).amount == 0:
        print("issue new asset: {}".format(asset['symbol']))
        instance.issue_asset(to=host,
                             amount=amount,
                             asset=asset,
                             account=host)

    with open("auction_result.txt".format(asset['symbol']), "w") as fd:
        fd.write(asset['symbol'])
        fd.write(":")
        fd.write(str(price))
        fd.write(":")
        fd.write(str(amount))

    print("waiting ... ")

    print("asset {} has amount: {}".format(asset['symbol'],
                                           host_instance.balance(asset).amount))

    _deal(host, asset, price, amount=amount, instance=instance)
    # remove this asset in db since it was sold in real market.
    resp = dict(status="success",
                price=price,
                amount=amount)
    print(resp)
    return json.dumps(resp)



def generate_price(min=1, max=3):
    return random.uniform(min, max)


if __name__ == "__main__":

    accounts = ["berlin-test1", "berlin-test2", "berlin-test3", "berlin-test4"]

    assets_prices = {}
    for account in accounts:
        bid_price = generate_price()
        resp = bid(account, bid_price)
        symbol = json.loads(resp)['asset_symbol']
        assets_prices[symbol] = bid_price

    asset = json.loads(resp)['asset_symbol']
    asset, deal_price = max(assets_prices.items(), key=operator.itemgetter(1))
    print("deal price: {}, asset name: {}".format(deal_price, asset))

    deal(asset, deal_price)
