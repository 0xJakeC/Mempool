import asyncio
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
import websockets

# Connect to an Ethereum node via WebSocket
infura_url = "wss://mainnet.infura.io/ws/v3/e33870ee2cd8461db67d69e018b6f8f3"
web3 = Web3(Web3.WebsocketProvider(infura_url))

# Check if the connection is successful
if not web3.is_connected():
    print("Failed to connect to the Ethereum network.")
    exit()

# If using a PoA network like Rinkeby, add the middleware
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Define the wallet address to monitor
wallet_address = Web3.to_checksum_address("0xE2588450DFa9a7b862984c215AF88853b15A60a5")

# ERC20 Transfer function signature
erc20_transfer_signature = web3.keccak(text="transfer(address,uint256)").hex()[:10]

# Function to get transaction details
def get_transaction_details(tx):
    details = {
        "gasLimit": tx['gas'],
        "gasPrice": Web3.fromWei(tx['gasPrice'], 'gwei'),
        "maxPriorityFeePerGas": Web3.fromWei(tx.get('maxPriorityFeePerGas', 0), 'gwei'),
        "maxFeePerGas": Web3.fromWei(tx.get('maxFeePerGas', 0), 'gwei'),
        "value": Web3.fromWei(tx['value'], 'ether'),
        "type": "ETH"
    }
    if tx['input'][:10] == erc20_transfer_signature:
        details["type"] = "ERC20"
        details["token_to"] = "0x" + tx['input'][34:74]
        details["token_value"] = Web3.fromWei(int(tx['input'][74:], 16), 'ether')  # Assumes 18 decimals
    return details

# Callback for new pending transactions
async def handle_pending_transaction(tx_hash):
    try:
        tx = web3.eth.get_transaction(tx_hash)
        if tx and tx['from'] == wallet_address:
            details = get_transaction_details(tx)
            print(f"Transaction from {wallet_address} detected:")
            for key, value in details.items():
                print(f"{key}: {value}")
            print("-" * 40)
    except Exception as e:
        print(f"Error processing transaction {tx_hash}: {e}")

# Subscribe to pending transactions and handle them
async def subscribe_pending_transactions():
    async with websockets.connect(infura_url) as ws:
        await ws.send(json.dumps({
            "jsonrpc": "2.0",
            "method": "eth_subscribe",
            "params": ["newPendingTransactions"],
            "id": 1
        }))
        subscription_response = await ws.recv()
        print(subscription_response)

        while True:
            try:
                message = await ws.recv()
                message_json = json.loads(message)
                if 'params' in message_json:
                    tx_hash = message_json['params']['result']
                    await handle_pending_transaction(tx_hash)
            except Exception as e:
                print(f"Error in subscription loop: {e}")
                break

# Run the subscription loop
asyncio.run(subscribe_pending_transactions())
