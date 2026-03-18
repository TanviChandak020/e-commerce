import requests
import pandas as pd
import boto3
from datetime import datetime
import os
import time

def fetch_fakestore_data(endpoint, max_retries=3):
    """Fetch data from FakeStoreAPI with retry logic and proper headers"""
    url = f"https://fakestoreapi.com/{endpoint}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Attempt {attempt + 1} failed ({e}). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"Failed to fetch {endpoint} after {max_retries} attempts")
                raise
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Request error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

def upload_to_s3(df, bucket, key):
    """Upload DataFrame to S3 as Parquet"""
    try:
        s3 = boto3.client('s3')
        # In a real scenario, we'd use io.BytesIO to avoid local disk
        temp_path = f"/tmp/{os.path.basename(key)}"
        df.to_parquet(temp_path, index=False)
        s3.upload_file(temp_path, bucket, key)
        os.remove(temp_path)
        print(f"✅ Uploaded to S3: {key}")
    except Exception as e:
        print(f"⚠️  Failed to upload to S3: {e}")
        print(f"   Bucket: {bucket}")
        print(f"   Key: {key}")
        raise

def main():
    # Configuration
    S3_BUCKET = os.getenv('S3_RAW_BUCKET', '').strip()
    date_str = datetime.now().strftime("%Y/%m/%d")
    
    try:
        print("Fetching products...")
        products = fetch_fakestore_data('products')
        df_products = pd.DataFrame(products)
        print(f"✅ Fetched {len(df_products)} products")
        
        if S3_BUCKET:
            try:
                upload_to_s3(df_products, S3_BUCKET, f"raw/products/{date_str}/products.parquet")
            except Exception as e:
                print(f"⚠️  S3 upload failed: {e}. Saving locally instead...")
                os.makedirs("data/raw/products", exist_ok=True)
                df_products.to_parquet(f"data/raw/products/products.parquet")
                print(f"✅ Saved products locally: data/raw/products/products.parquet")
        else:
            print("⚠️  S3_RAW_BUCKET not configured. Saving locally...")
            os.makedirs("data/raw/products", exist_ok=True)
            df_products.to_parquet(f"data/raw/products/products.parquet")
            print(f"✅ Saved products locally: data/raw/products/products.parquet")
    except Exception as e:
        print(f"⚠️  Failed to fetch products: {e}")
        return
    
    try:
        print("Fetching orders (carts)...")
        carts = fetch_fakestore_data('carts')
        df_carts = pd.DataFrame(carts)
        print(f"✅ Fetched {len(df_carts)} orders")
        
        if S3_BUCKET:
            try:
                upload_to_s3(df_carts, S3_BUCKET, f"raw/orders/{date_str}/orders.parquet")
            except Exception as e:
                print(f"⚠️  S3 upload failed: {e}. Saving locally instead...")
                os.makedirs("data/raw/orders", exist_ok=True)
                df_carts.to_parquet(f"data/raw/orders/orders.parquet")
                print(f"✅ Saved orders locally: data/raw/orders/orders.parquet")
        else:
            print("⚠️  S3_RAW_BUCKET not configured. Saving locally...")
            os.makedirs("data/raw/orders", exist_ok=True)
            df_carts.to_parquet(f"data/raw/orders/orders.parquet")
            print(f"✅ Saved orders locally: data/raw/orders/orders.parquet")
    except Exception as e:
        print(f"⚠️  Failed to fetch orders: {e}")
        return
    
    print("✅ Ingestion complete.")

if __name__ == "__main__":
    main()
