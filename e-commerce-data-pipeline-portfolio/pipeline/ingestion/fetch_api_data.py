import requests
import pandas as pd
import boto3
from datetime import datetime
import os
import time

def fetch_fakestore_data(endpoint, max_retries=3):
    """Fetch data from FakeStoreAPI with retry logic"""
    url = f"https://fakestoreapi.com/{endpoint}"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ Failed to fetch {endpoint} after {max_retries} attempts: {e}")
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
    
    print("=" * 70)
    print("🔄 E-Commerce Data Ingestion - FakeStoreAPI")
    print("=" * 70)
    
    # Fetch products from FakeStoreAPI
    print("\n📦 Fetching products from FakeStoreAPI...")
    try:
        products = fetch_fakestore_data('products')
        df_products = pd.DataFrame(products)
        print(f"✅ Fetched {len(df_products)} products from FakeStoreAPI")
        
        if S3_BUCKET:
            try:
                s3 = boto3.client('s3')
                temp_path = "/tmp/products.parquet"
                df_products.to_parquet(temp_path, index=False)
                s3.upload_file(temp_path, S3_BUCKET, f"raw/products/{date_str}/products.parquet")
                os.remove(temp_path)
                print(f"✅ Uploaded to S3: s3://{S3_BUCKET}/raw/products/{date_str}/products.parquet")
            except Exception as e:
                print(f"⚠️  S3 upload failed: {e}. Saving locally instead...")
                os.makedirs("data/raw/products", exist_ok=True)
                df_products.to_parquet("data/raw/products/products.parquet")
                print(f"✅ Saved products locally: data/raw/products/products.parquet")
        else:
            print("ℹ️  S3_RAW_BUCKET not configured. Saving locally...")
            os.makedirs("data/raw/products", exist_ok=True)
            df_products.to_parquet("data/raw/products/products.parquet")
            print(f"✅ Saved products locally: data/raw/products/products.parquet")
    except Exception as e:
        print(f"❌ Failed to fetch products: {e}")
        raise
    
    # Fetch carts/orders from FakeStoreAPI
    print("\n📋 Fetching carts/orders from FakeStoreAPI...")
    try:
        carts = fetch_fakestore_data('carts')
        df_carts = pd.DataFrame(carts)
        print(f"✅ Fetched {len(df_carts)} carts/orders from FakeStoreAPI")
        
        if S3_BUCKET:
            try:
                s3 = boto3.client('s3')
                temp_path = "/tmp/orders.parquet"
                df_carts.to_parquet(temp_path, index=False)
                s3.upload_file(temp_path, S3_BUCKET, f"raw/orders/{date_str}/orders.parquet")
                os.remove(temp_path)
                print(f"✅ Uploaded to S3: s3://{S3_BUCKET}/raw/orders/{date_str}/orders.parquet")
            except Exception as e:
                print(f"⚠️  S3 upload failed: {e}. Saving locally instead...")
                os.makedirs("data/raw/orders", exist_ok=True)
                df_carts.to_parquet("data/raw/orders/orders.parquet")
                print(f"✅ Saved orders locally: data/raw/orders/orders.parquet")
        else:
            print("ℹ️  S3_RAW_BUCKET not configured. Saving locally...")
            os.makedirs("data/raw/orders", exist_ok=True)
            df_carts.to_parquet("data/raw/orders/orders.parquet")
            print(f"✅ Saved orders locally: data/raw/orders/orders.parquet")
    except Exception as e:
        print(f"❌ Failed to fetch carts: {e}")
        raise
    
    print("\n" + "=" * 70)
    print("✨ Data ingestion complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
