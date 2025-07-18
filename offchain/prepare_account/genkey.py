from aptos_sdk.account import Account

async def main():
    # Generate two accounts
    alice = Account.generate()
    bob = Account.generate()
    
    print("=== Addresses ===")
    privkey_alice = alice.private_key.hex()
    privkey_bob = bob.private_key.hex()

    print(f"Alice's private key: {privkey_alice}")
    with open("./testkey/Alice", 'w') as f:
        f.write(privkey_alice)
    
    print(f"Bob's private key: {privkey_bob}")
    with open("./testkey/Bob", 'w') as f:
        f.write(privkey_bob)
    
    print(f"Alice's address: {alice.address()}")
    print(f"Bob's address: {bob.address()}")
    

