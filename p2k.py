import traceback
from web3 import Web3
import json
import concurrent.futures

# If you enjoy using this script, bananas are much appreciated: 0xd32f25Dfa932b8064A81B8254E7997CAeBc85F97
address = Web3.toChecksumAddress("")
key = ""
NUM_RUNS = 100
TEAM_NUMBER = 1

# DO NOT TOUCH ANYTHING BELOW THIS LINE

txs = []
out = []

w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com/'))
abi = '[{"inputs":[{"internalType":"uint256","name":"_teamId","type":"uint256"},{"internalType":"bool","name":"_energy","type":"bool"}],"name":"runAdventureVRF","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}]'
contractAddress = Web3.toChecksumAddress("0x70C575588B98C1F46B1382c706AdAf398A874e3E")
contract = w3.eth.contract(address=Web3.toChecksumAddress(contractAddress), abi=abi)


nonce = w3.eth.get_transaction_count(address)
for i in range(NUM_RUNS):
    send_txn = contract.functions.runAdventureVRF(
        TEAM_NUMBER,
        False
        ).buildTransaction({
            'value': 0,
            'chainId': 137,
            'gas': 500000,
            'gasPrice': Web3.toWei(150, 'gwei'),
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
