import json
import secrets
import os

API_KEYS_FILE = "api_keys.json"
VALID_TIERS = ["free", "pro", "ultra", "mega"]

# Load keys from file
def load_keys():
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, "r") as f:
            return json.load(f)
    return {}

# Save keys to file
def save_keys(keys):
    with open(API_KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)

# Generate a new secure API key
def generate_api_key(length=32):
    return secrets.token_hex(length // 2)

# Add a new API key
def add_key():
    tier = input(f"Enter tier ({'/'.join(VALID_TIERS)}): ").strip().lower()
    if tier not in VALID_TIERS:
        print("❌ Invalid tier.")
        return

    key = generate_api_key()
    keys = load_keys()
    keys[key] = tier
    save_keys(keys)
    print(f"✅ New API key for tier '{tier}':\n{key}")

# Delete an existing API key
def delete_key():
    key = input("Enter API key to delete: ").strip()
    keys = load_keys()
    if key in keys:
        del keys[key]
        save_keys(keys)
        print("🗑️ Key deleted.")
    else:
        print("❌ Key not found.")

# List all keys
def list_keys():
    keys = load_keys()
    if not keys:
        print("No keys found.")
    else:
        for key, tier in keys.items():
            print(f"{key}  →  {tier}")

# Main menu
def menu():
    while True:
        print("\n🔐 API Key Manager")
        print("1. Add new API key")
        print("2. Delete an API key")
        print("3. List all keys")
        print("4. Exit")
        choice = input("Select an option: ").strip()
        if choice == "1":
            add_key()
        elif choice == "2":
            delete_key()
        elif choice == "3":
            list_keys()
        elif choice == "4":
            break
        else:
            print("❌ Invalid option.")

if __name__ == "__main__":
    menu()
