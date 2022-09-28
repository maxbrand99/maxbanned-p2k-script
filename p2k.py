# AUTHOR: https://twitter.com/maxbrand99

import math
import time
from web3 import Web3
import concurrent.futures
import requests
import json

# DONATIONS: 0xd32f25Dfa932b8064A81B8254E7997CAeBc85F97
# I release this script for free and rely on the donations of my fellow Kongz.
address = Web3.toChecksumAddress("")
key = ""
NUM_RUNS = 25
TEAM_NUMBER = 1

# Change the gas price if you want. I am not responsible for stuck txs if you decide to be cheap on gas.
GAS_PRICE = 100

# Set this to true to use fuel rods
USE_FUEL_RODS = False


# DO NOT TOUCH ANYTHING BELOW THIS LINE

out = []
requestsRan = []
w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com/'))
gameABI = '[{"inputs":[{"internalType":"uint256","name":"_teamId","type":"uint256"},{"internalType":"bool","name":"_energy","type":"bool"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"queryManyAdventuresVRF","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_requestId","type":"uint256"}],"name":"settleAdventureRuns","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
gameAddress = Web3.toChecksumAddress("0x70C575588B98C1F46B1382c706AdAf398A874e3E")
gameContract = w3.eth.contract(address=gameAddress, abi=gameABI)


def sendTxSingle(signed_txn):
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


def getUncompleted(address, attempts=0):
    url = "https://api.thegraph.com/subgraphs/name/clumsier/cyberkongz-polygon-subgraph"

    payload = '{"query":"query getUncompletedRuns($user:String){multipleAdventuresRuns(where:{user:$user,ready:true,completed:false}){requestId,team{id}}}","variables":{"user":"' + str(address).lower() + '"}}'
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    try:
        json_data = json.loads(response.text)
        if 'data' in json_data:
            return json_data
    except Exception as e:
        if attempts > 3:
            print("Could not get uncompleted runs, something is wrong")
            print(e)
            print(response)
            print(response.text)
            raise SystemExit
        else:
            return getUncompleted(attempts + 1)


def sendTxBatch(txs):
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_url = (executor.submit(sendTxSingle, tx) for tx in txs)
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                data = future.result()
            except Exception as exc:
                data = str(type(exc))
            finally:
                out.append(data)
                print(out)
                print(str(len(out)), end="\r")


def initRuns():
    txs = []
    nonce = w3.eth.get_transaction_count(address)
    startedRuns = 0
    batchesStarted = 0
    for i in range(math.floor(NUM_RUNS / 25)):
        startedRuns += 25
        batchesStarted += 1
        send_txn = gameContract.functions.queryManyAdventuresVRF(TEAM_NUMBER, USE_FUEL_RODS, 25).buildTransaction({
            'value': 0,
            'chainId': 137,
            'gas': 491337,
            'gasPrice': Web3.toWei(GAS_PRICE, 'gwei'),
            'nonce': nonce
        })
        signed_txn = w3.eth.account.sign_transaction(send_txn, private_key=key)
        txs.append(signed_txn)
        nonce += 1
    if NUM_RUNS != startedRuns:
        batchesStarted += 1
        send_txn = gameContract.functions.queryManyAdventuresVRF(TEAM_NUMBER, USE_FUEL_RODS, NUM_RUNS - startedRuns).buildTransaction({
            'value': 0,
            'chainId': 137,
            'gas': 491337,
            'gasPrice': Web3.toWei(GAS_PRICE, 'gwei'),
            'nonce': nonce
        })
        signed_txn = w3.eth.account.sign_transaction(send_txn, private_key=key)
        txs.append(signed_txn)
        nonce += 1

    sendTxBatch(txs)
    return batchesStarted


def finalizeRuns(batchesStarted):
    txs = []
    nonce = w3.eth.get_transaction_count(address)
    while batchesStarted > 0:
        uncompleted = getUncompleted(address)
        if len(uncompleted['data']['multipleAdventuresRuns']) > 0:
            for request in uncompleted['data']['multipleAdventuresRuns']:
                if request['requestId'] in requestsRan:
                    continue
                send_txn = gameContract.functions.settleAdventureRuns(int(request['requestId'])).buildTransaction({
                    'value': 0,
                    'chainId': 137,
                    'gas': 3491337,
                    'gasPrice': Web3.toWei(GAS_PRICE, 'gwei'),
                    'nonce': nonce
                })
                signed_txn = w3.eth.account.sign_transaction(send_txn, private_key=key)
                txs.append(signed_txn)
                nonce += 1
                batchesStarted -= 1
                requestsRan.append(request['requestId'])
        else:
            print("Waiting 10 seconds for chainlink VRF")
            time.sleep(10)
    sendTxBatch(txs)


uncompleted = getUncompleted(address)
if len(uncompleted['data']['multipleAdventuresRuns']) > 0:
    finalizeRuns(len(uncompleted['data']['multipleAdventuresRuns']))
batchesStarted = initRuns()
finalizeRuns(batchesStarted)
