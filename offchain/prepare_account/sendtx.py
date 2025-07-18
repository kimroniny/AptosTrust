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

    # 1. Build the transaction
    print("\n=== 1. Building the transaction ===")
    
    # Create the entry function payload
    # This specifies which function to call and with what arguments
    entry_function = EntryFunction.natural(
        "0x1::aptos_account",  # Module address and name
        "transfer",            # Function name
        [],                    # Type arguments (empty for this function)
        [
            # Function arguments with their serialization type
            TransactionArgument(account_bob.address(), Serializer.struct),  # Recipient address
            TransactionArgument(1000, Serializer.u64),                      # Amount to transfer (1000 octas)
        ],
    )
    
    # Get the chain ID for the transaction
    chain_id = await rest_client.chain_id()
    
    # Get the sender's current sequence number
    account_data = await rest_client.account(account_alice.address())
    sequence_number = int(account_data["sequence_number"])
    
    # Create the raw transaction with all required fields
    raw_transaction = RawTransaction(
        sender=account_alice.address(),                                    # Sender's address
        sequence_number=sequence_number,                           # Sequence number to prevent replay attacks
        payload=TransactionPayload(entry_function),                # The function to call
        max_gas_amount=2000,                                       # Maximum gas units to use
        gas_unit_price=100,                                        # Price per gas unit in octas
        expiration_timestamps_secs=int(time.time()) + 600,         # Expires in 10 minutes
        chain_id=chain_id,                                         # Chain ID to ensure correct network
    )
    
    print("Transaction built successfully")
    print(f"Sender: {raw_transaction.sender}")
    print(f"Sequence Number: {raw_transaction.sequence_number}")
    print(f"Max Gas Amount: {raw_transaction.max_gas_amount}")
    print(f"Gas Unit Price: {raw_transaction.gas_unit_price}")
    print(f"Expiration Timestamp: {time.ctime(raw_transaction.expiration_timestamps_secs)}")

    # 3. Sign the transaction
    print("\n=== 3. Signing the transaction ===")
    
    # Sign the raw transaction with the sender's private key
    # This creates a cryptographic signature that proves the sender authorized this transaction
    signed_transaction = await rest_client.create_bcs_signed_transaction(
        account_alice,                           # Account with the private key
        TransactionPayload(entry_function),  # The payload from our transaction
        sequence_number=sequence_number  # Use the same sequence number as before
    )
    
    print("Transaction signed successfully")
    # We can't easily extract the signature from the signed transaction object,
    # but we can confirm it was created

    # Check final balances
    alice_before_balance = await rest_client.account_balance(account_alice.address())
    bob_before_balance = await rest_client.account_balance(account_bob.address())
    
    print("\n=== Balances: before transmitting ===")
    print(f"Alice: {alice_before_balance} octas")
    print(f"Bob: {bob_before_balance}")

    # 4. Submit the transaction
    print("\n=== 4. Submitting the transaction ===")
    
    # Submit the signed transaction to the blockchain
    # This broadcasts the transaction to the network for processing
    tx_hash = await rest_client.submit_bcs_transaction(signed_transaction)
    
    print(f"Transaction submitted with hash: {tx_hash}")

    # 5. Wait for the transaction to complete
    print("\n=== 5. Waiting for transaction completion ===")
    
    # Wait for the transaction to be processed by the blockchain
    # This polls the blockchain until the transaction is confirmed
    await rest_client.wait_for_transaction(tx_hash)
    
    # Get the transaction details to check its status
    transaction_details = await rest_client.transaction_by_hash(tx_hash)
    success = transaction_details["success"]
    vm_status = transaction_details["vm_status"]
    gas_used = transaction_details["gas_used"]
    
    print(f"Transaction completed with status: {'SUCCESS' if success else 'FAILURE'}")
    print(f"VM Status: {vm_status}")
    print(f"Gas used: {gas_used}")

    # Check final balances
    alice_final_balance = await rest_client.account_balance(account_alice.address())
    bob_final_balance = await rest_client.account_balance(account_bob.address())
    
    print("\n=== Final Balances ===")
    print(f"Alice: {alice_final_balance} octas (spent {alice_before_balance - alice_final_balance} octas on transfer and gas)")
    print(f"Bob: {bob_final_balance} octas (received {bob_final_balance - bob_before_balance} octas)")

 
if __name__ == "__main__":
    asyncio.run(main())