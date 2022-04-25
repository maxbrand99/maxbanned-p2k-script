# AUTHOR: https://twitter.com/maxbrand99

import math
from web3 import Web3
import concurrent.futures

# DONATIONS: 0xd32f25Dfa932b8064A81B8254E7997CAeBc85F97
# I release this script for free and rely on the donations of my fellow Kongz.
address = Web3.toChecksumAddress("")
key = ""
NUM_RUNS = 50
TEAM_NUMBER = 0

# Change the gas price if you want. I am not responsible for stuck txs if you decide to be cheap on gas.
GAS_PRICE = 150

# Set this to true to use fuel rods
USE_FUEL_RODS = False

# 0 = No Charm
# 1 = Cyber Fragment
# 2 = Rainbow Crystal
# 3 = Promethean Relic
CHARM_TO_USE = 0


# DO NOT TOUCH ANYTHING BELOW THIS LINE

txs = []
out = []


w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com/'))
gameABI = '[{"inputs":[{"internalType":"uint256","name":"_teamId","type":"uint256"},{"internalType":"bool","name":"_energy","type":"bool"}],"name":"runAdventureVRF","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_teamId","type":"uint256"},{"internalType":"uint256","name":"_charm","type":"uint256"}],"name":"activateCharm","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"}],"name":"charmInUse","outputs":[{"internalType":"uint256","name":"charmType","type":"uint256"},{"internalType":"uint256","name":"hp","type":"uint256"}],"stateMutability":"view","type":"function"}]'
gameAddress = Web3.toChecksumAddress("0x70C575588B98C1F46B1382c706AdAf398A874e3E")
gameContract = w3.eth.contract(address=gameAddress, abi=gameABI)
charmAddress = Web3.toChecksumAddress("0x7cBCCC4a1576d7A05eB6f6286206596BCBee14aC")
charmABI = '[{"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'
charmContract = w3.eth.contract(address=charmAddress, abi=charmABI)

if CHARM_TO_USE != 0:
    if not CHARM_TO_USE in [1, 2, 3]:
        print("INVALID CHARM NUMBER. PLEASE READ THE COMMENTS ON LINES 12-15!")
        raise SystemExit
    charmBalance = charmContract.functions.balanceOf(address, CHARM_TO_USE).call()
    if charmBalance < math.ceil(NUM_RUNS / 50):
        print("NOT ENOUGH CHARMS IN INVENTORY FOR THIS NUMBER OF RUNS. PLEASE GET MORE CHARMS OR REDUCE THE NUMBER OF RUNS.")
        raise SystemExit
    charmInUse = gameContract.functions.charmInUse(address, TEAM_NUMBER).call()
    if not charmInUse[1] in [0, 1]:
        print("THIS TEAM CURRENTLY HAS A CHARM THAT IS ALREADY IN USE. PLEASE SET CHARM NUMBER TO 0 AND RUN " + str(int(charmInUse[1] / 200)) + " MORE RUNS WITH BANANAS OR " + str(int(charmInUse[1] / (10000/30))) + " MORE RUNS WITH FUEL RODS.")
        raise SystemExit
    nonce = w3.eth.get_transaction_count(address)
    completedRuns = 0
    for i in range(math.ceil(NUM_RUNS / 50)):
        send_txn = gameContract.functions.activateCharm(TEAM_NUMBER, CHARM_TO_USE).buildTransaction({
            'value': 0,
            'chainId': 137,
            'gas': 491337,
            'gasPrice': Web3.toWei(GAS_PRICE, 'gwei'),
            'nonce': nonce
        })
        signed_txn = w3.eth.account.sign_transaction(send_txn, private_key=key)
        txs.append(signed_txn)
        nonce += 1
        for j in range(50):
            if completedRuns == NUM_RUNS:
                break
            completedRuns += 1
            send_txn = gameContract.functions.runAdventureVRF(TEAM_NUMBER, USE_FUEL_RODS).buildTransaction({
                'value': 0,
                'chainId': 137,
                'gas': 491337,
                'gasPrice': Web3.toWei(GAS_PRICE, 'gwei'),
                'nonce': nonce
            })
            signed_txn = w3.eth.account.sign_transaction(send_txn, private_key=key)
            txs.append(signed_txn)
            nonce += 1
else:
    nonce = w3.eth.get_transaction_count(address)
    for i in range(NUM_RUNS):
        send_txn = gameContract.functions.runAdventureVRF(TEAM_NUMBER, USE_FUEL_RODS).buildTransaction({
            'value': 0,
            'chainId': 137,
            'gas': 491337,
            'gasPrice': Web3.toWei(GAS_PRICE, 'gwei'),
            'nonce': nonce
        })
        signed_txn = w3.eth.account.sign_transaction(send_txn, private_key=key)
        txs.append(signed_txn)
        nonce += 1

def load_url(signed_txn):
    attempts = 0
    oldtx = w3.toHex(w3.keccak(signed_txn.rawTransaction))
    while attempts < 10:
        try:
            tx = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        except:
            tx = oldtx
        try:
            oldtx = tx
            receipt = w3.eth.wait_for_transaction_receipt(tx, 10)
            if receipt["status"] == 1:
                print("success\t" + w3.toHex(w3.keccak(signed_txn.rawTransaction)))
            else:
                print("fail\t" + w3.toHex(w3.keccak(signed_txn.rawTransaction)))
            break
        except Exception as e:
            print(e)
        attempts += 1
    return w3.toHex(w3.keccak(signed_txn.rawTransaction))


with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_to_url = (executor.submit(load_url, tx) for tx in txs)
    for future in concurrent.futures.as_completed(future_to_url):
        try:
            data = future.result()
        except Exception as exc:
            data = str(type(exc))
        finally:
            out.append(data)
            print(out)
            print(str(len(out)), end="\r")
