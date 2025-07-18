import asyncio
from aptos_sdk.account import Account
from aptos_sdk.async_client import FaucetClient, RestClient
from aptos_sdk.transactions import EntryFunction, TransactionPayload, TransactionArgument, RawTransaction
from aptos_sdk.bcs import Serializer
import time
 
# Network configuration
NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
FAUCET_URL = "https://faucet.devnet.aptoslabs.com"
 
async def main():
    # Initialize the clients
    rest_client = RestClient(NODE_URL)
    faucet_client = FaucetClient(FAUCET_URL, rest_client)
    
    print("Connected to Aptos devnet")
    
    # More code will go here
    # Generate two accounts
    with open('./testkey/Alice', 'r') as f:
        account_alice = Account.load_key(f.read())
    with open('./testkey/Bob', 'r') as f:
        account_bob = Account.load_key(f.read())
    
    
    print("=== Addresses ===")
    print(f"Alice's private key: {account_alice.private_key.hex()}")
    print(f"Bob's private key: {account_bob.private_key.hex()}")
    print(f"Alice's address: {account_alice.address()}")
    print(f"Bob's address: {account_bob.address()}")

 
if __name__ == "__main__":
    asyncio.run(main())