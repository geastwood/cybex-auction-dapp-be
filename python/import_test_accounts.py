import cybex

cybex.cybex.cybex_debug_config('59e27e3883fc5ec4dbff68855f83961303157df9a64a3ecf49982affd8e8d490')

NODE_URL = "wss://shenzhen.51nebula.com"

WALLET_PWD = '123456'
instance = cybex.Cybex(NODE_URL)

instance.wallet.unlock(WALLET_PWD)
assert not instance.wallet.locked()

private_keys = []
with open("accounts.txt", "r") as f:
    private_keys = f.read()
    private_keys = private_keys.split()


for private_key in private_keys:
    try:
        instance.wallet.addPrivateKey(private_key)
    except:
        print("the account already in db")

print(instance.wallet.getAccounts())
