import requests
import json
import os
import time

def fetch_and_save_data():
    url = "https://api.shadowpay.com/api/v2/user/items/prices"
    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer 36663c5979e004871a1f7275df6ff5c4"
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # Transform data structure
        transformed_data = [
            {
                "Item": item["steam_market_hash_name"],
                "Price": item["price"]
            } for item in data["data"]
        ]
        
        # Create JSON folder if it doesn't exist
        os.makedirs("JSON", exist_ok=True)
        
        # Save transformed data
        with open("JSON/shadowpay_data.json", 'w', encoding='utf-8') as f:
            json.dump(transformed_data, f, indent=4, ensure_ascii=False)
        
        print("Data saved successfully", flush=True)
    
    except Exception as e:
        print(f"Error fetching or saving data: {e}", flush=True)

def main():
    while True:
        fetch_and_save_data()
        time.sleep(5)

if __name__ == "__main__":
    main()