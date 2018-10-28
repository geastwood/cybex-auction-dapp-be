import os
import random
import json
import string
import cybex
import rsa


def generate_id(min=0, max=65534):
    return int(random.uniform(min, max))


def generate_nonce(min=0, max=1000000):
    return int(random.uniform(min, max))


def generate_random_name(length=8):
    return "".join([random.choice(string.ascii_uppercase) for _ in range(length)])


def generate_price(min=1, max=3):
    return random.uniform(min, max)


class Auction(object):

    def __init__(self,
                 id=1,
                 host="berlin-test5",
                 expiration=3600,
                 amount=1,
                 debug=True):
        self._expiration = expiration
        self._amount = amount
        self._instance = self._get_cybex_instance(debug)
        self._host = host
        self._name = "auction"
        self._id = id

    def _get_cybex_instance(self, debug=True):
        if debug is True:
            cybex.cybex.cybex_debug_config('59e27e3883fc5ec4dbff68855f83961303157df9a64a3ecf49982affd8e8d490')
            NODE_URL = "wss://shenzhen.51nebula.com"
            WALLET_PWD = '123456'
        else:
            pass
        instance = cybex.Cybex(NODE_URL)
        instance.wallet.unlock(WALLET_PWD)
        return instance

    def _create_asset(self, symbol):
        asset = self._instance.create_asset(symbol=symbol,
                                            precision=0,
                                            max_supply=10000,
                                            core_exchange_ratio={symbol: 100, 'CYB': 1},
                                            account=self._host)
        asset = cybex.Asset(symbol,
                            cybex_instance=self._instance)
        return asset


    def bid(self, account, auction_asset, price):
        raise NotImplementedError

    def deal(self, auction_asset, price):
        raise NotImplementedError


class BlindAuction(Auction):

    def __init__(self, *args, **kwargs):
        super(BlindAuction, self).__init__(*args, **kwargs)
        self._name = "blind_auction"

        pub_fname = "./db/{}_{}_{}.pub".format(self._id, self._host, self._name)
        priv_fname = "./db/{}_{}_{}".format(self._id, self._host, self._name)

        if os.path.isfile(pub_fname) and os.path.isfile(priv_fname):
            print("Load public key and private key for auction {}".format(self._id))
            with open(pub_fname, "rb") as fd:
                _pub_key_data = fd.read()
                self._pub_key = rsa.PublicKey.load_pkcs1(_pub_key_data)
            with open(priv_fname, "rb") as fd:
                _priv_key_data = fd.read()
                self._priv_key = rsa.PrivateKey.load_pkcs1(_priv_key_data)
        else:
            print("Generate public key and private key for auction {}".format(self._id))
            self._pub_key, self._priv_key = rsa.newkeys(2048)
            with open(pub_fname, "wb") as fd:
                fd.write(self._pub_key.save_pkcs1())
            with open(priv_fname, "wb") as fd:
                fd.write(self._priv_key.save_pkcs1())

        self._bid_history_fname = "./bid/{}_{}_{}.txt".format(self._id, self._host, self._name)
        if os.path.isfile(self._bid_history_fname):
            print("Load bid history from database {}...".format(self._bid_history_fname))
            with open(self._bid_history_fname, "r") as fd:
                self._bid_history = json.loads(fd.read())
        else:
            print("No bid history found...")
            self._bid_history = []

    def _bid(self, account, auction_asset, price):
        market = cybex.Market(base=cybex.Asset("CYB"),
                              quote=auction_asset,
                              cybex_instance=self._instance)

        memo_id = generate_id()
        nonce = generate_nonce()
        data = {"account": account, "asset": auction_asset['symbol'], "price": price,
                "nonce": nonce}
        self._bid_history.append(data)
        with open(self._bid_history_fname, "w") as fd:
            fd.write(json.dumps(self._bid_history))

        data = json.dumps(data)
        # print("blind data:", data)
        memo_data = self._encrypt(data)
        # print("encrypt blind data:", memo_data)
        self._instance.custom([], memo_id, memo_data, account=self._host)
        market.buy(price, self._amount, self._expiration,
                   killfill=False, account=account)

    def _encrypt(self, data):
        data = data.encode('utf8')
        crypto_data = rsa.encrypt(data, self._pub_key)
        return str(crypto_data)

    def bid(self, bidder, price):
        name = "SUB{}".format(generate_random_name())
        print("Genrate a random asset {}.".format(name))

        asset = self._create_asset(name)
        self._bid(bidder, asset, 0.1)
        resp = dict(account=bidder,
                    host=self._host,
                    asset=asset['symbol'],
                    price=price)

        print(resp)
        return json.dumps(resp)

    def deal(self, auction_asset, price):
        if isinstance(auction_asset, str):
            asset = cybex.Asset(auction_asset)
        else:
            asset = auction_asset

        host_instance = cybex.account.Account(self._host, cybex_instance=self._instance)
        # we don't have any asset, issue new assets
        if host_instance.balance(asset).amount == 0:
            print("issue new asset: {}".format(asset['symbol']))
            self._instance.issue_asset(to=self._host,
                                       amount=self._amount,
                                       asset=asset,
                                       account=self._host)

        print("asset {} has amount: {}".format(asset['symbol'],
                                               host_instance.balance(asset).amount))

        self._deal(asset, price)
        # remove this asset in db since it was sold in real market.
        resp = dict(status="success",
                    price=price,
                    amount=self._amount)
        print(resp)
        return json.dumps(resp)

    def _deal(self, auction_asset, price):
        market = cybex.Market(base=cybex.Asset("CYB"),
                              quote=auction_asset,
                              cybex_instance=self._instance)


        market.sell(price, self._amount, self._expiration,
                    killfill=False, account=self._host)


    def finalize_deal(self):
        max_price = None
        winner_asset = None
        winner_bidder = None
        for x in self._bid_history:
            if max_price is None and \
                winner_asset is None and \
                winner_bidder is None:
                max_price = x['price']
                winner_asset = x['asset']
                winner_bidder = x['account']
            else:
                if max_price < x['price']:
                    max_price = x['price']
                    winner_asset = x['asset']
                    winner_bidder = x['account']
        self.deal(winner_asset, max_price)
        resp = dict(winner=winner_bidder,
                    asset=winner_asset,
                    price=max_price)

        os.rename(self._bid_history_fname, "{}.bk".format(self._bid_history_fname))
        # os.remove(self._bid_history_fname)
        return json.dumps(resp)


if __name__ == "__main__":
    blind_auction = BlindAuction(id=2)

    bidders = ["berlin-test1", "berlin-test2"]
    for bidder in bidders:
        bid_price = generate_price()
        resp = blind_auction.bid(bidder, bid_price)

    resp = blind_auction.finalize_deal()
    print(resp)
