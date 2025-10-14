# FILE: generate_fyers_token.py

import sys
import toml
from pathlib import Path
from fyers_apiv3 import fyersModel

def generate_fyers_token():
    """
    A seamless, single-run script to generate a Fyers API access token
    by reading credentials from a secrets.toml file.
    """
    print("--- Fyers Access Token Generation ---")

    # --- Part 1: Load Credentials from secrets.toml ---
    try:
        secrets_path = Path(__file__).resolve().parent / "secrets.toml"
        secrets = toml.load(secrets_path)
        
        client_id = secrets.get("fyers", {}).get("client_id")
        secret_key = secrets.get("fyers", {}).get("secret_key")
        
        if not client_id or not secret_key:
            raise KeyError("client_id or secret_key not found in secrets.toml")
            
    except FileNotFoundError:
        print(f"🚨 ERROR: The secrets.toml file was not found in your project's root directory.")
        sys.exit(1)
    except KeyError as e:
        print(f"🚨 ERROR: Your secrets.toml file is missing a required key: {e}")
        sys.exit(1)
        
    redirect_uri = "https://127.0.0.1"

    # --- Part 2: Generate the Authentication URL ---
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type="code",
        grant_type="authorization_code"  # <-- THIS IS THE REQUIRED FIX
    )

    auth_url = session.generate_authcode()
    
    print("\nStep 1: Get your Authentication Token")
    print("Please follow these instructions carefully:\n")
    print(f"🔗 1. Go to the following URL in your browser:\n\n   {auth_url}\n")
    print("   2. Log in with your Fyers credentials.")
    print("   3. From your browser's address bar, copy the entire long string of characters")
    print("      that comes AFTER '&auth_code='")
    
    print("-" * 40)
    
    # --- Part 3: Get User Input and Generate Access Token ---
    try:
        auth_code = input("📋 Paste the Authentication Token here and press Enter: ")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)

    if not auth_code:
        print("🚨 ERROR: Authentication Token cannot be empty.")
        sys.exit(1)

    print("\nReceived. Generating access token...")

    session.set_token(auth_code.strip())
    response = session.generate_token()

    # --- Part 4: Display the Result ---
    print("-" * 40)
    if response.get("s") == "ok":
        access_token = response.get("access_token")
        print("✅ Success! Your Access Token has been generated.\n")
        print(f"🔑 Your Access Token is:\n\n   {access_token}\n")
        print("   Please copy this new token and update the `access_token` value in your secrets.toml file.")
    else:
        print("❌ Failed to generate access token.")
        print(f"   Error: {response.get('message', 'Unknown error')}")

if __name__ == "__main__":
    generate_fyers_token()