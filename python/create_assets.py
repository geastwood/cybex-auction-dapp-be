import cybex


cybex.cybex.cybex_debug_config('59e27e3883fc5ec4dbff68855f83961303157df9a64a3ecf49982affd8e8d490')
NODE_URL = "wss://shenzhen.51nebula.com"
# NODE_URL = "wss://hangzhou.51nebula.com/"

WALLET_PWD = '123456'
instance = cybex.Cybex(NODE_URL)
instance.wallet.unlock(WALLET_PWD)
# instance.create_asset(symbol="LDKLSFSLDHSKFH",
#                       precision=3,
#                       max_supply=10000,
#                       core_exchange_ratio={'LDKLSFSLDHSKFH': 100, 'CYB': 1},
#                       description="test",
#                       account="berlin-test5")

instance.issue_asset(to="berlin-test5",
                     amount=1000,
                     asset="LDKLSFSLDHSKFH",
                     account="berlin-test5")
