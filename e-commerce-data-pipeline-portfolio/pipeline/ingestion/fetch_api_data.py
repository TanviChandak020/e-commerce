import requests
import pandas as pd
import boto3
from datetime import datetime
import os
import time

# Browser-like headers to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
}

def fetch_fakestore_products(max_retries=3):
    """Fetch products from FakeStoreAPI"""
    url = "https://fakestoreapi.com/products"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"FakeStoreAPI attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
    return None

def fetch_fakestore_carts(max_retries=3):
    """Fetch carts from FakeStoreAPI"""
    url = "https://fakestoreapi.com/carts"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"FakeStoreAPI carts attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
    return None

def fetch_dummyjson_products(max_retries=3):
    """Fallback: Fetch products from DummyJSON API"""
    url = "https://dummyjson.com/products?limit=20"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Transform DummyJSON format to match FakeStoreAPI structure
            return [
                {
                    'id': p['id'],
                    'title': p['title'],
                    'price': p['price'],
                    'description': p['description'],
                    'category': p['category'],
                    'image': p['thumbnail'],
                    'rating': {
                        'rate': p['rating'],
                        'count': 100
                    }
                } for p in data.get('products', [])
            ]
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"DummyJSON attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
    return None

def fetch_dummyjson_carts(max_retries=3):
    """Fallback: Fetch carts from DummyJSON API"""
    url = "https://dummyjson.com/carts?limit=20"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Transform DummyJSON format to match FakeStoreAPI structure
            return [
                {
                    'id': c['id'],
                    'userId': c['userId'],
                    'date': datetime.now().isoformat(),
                    'products': c.get('products', [])
                } for c in data.get('carts', [])
            ]
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"DummyJSON carts attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
    return None

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
    print("🔄 E-Commerce Data Ingestion")
    print("=" * 70)
    
    # Fetch products with fallback
    print("\n📦 Fetching products...")
    products = fetch_fakestore_products()
    
    if products is None:
        print("⚠️  FakeStoreAPI blocked. Trying DummyJSON...")
        products = fetch_dummyjson_products()
    
    if products is None:
        print("❌ All product sources failed")
        raise Exception("Unable to fetch products from any API")
    
    df_products = pd.DataFrame(products)
    print(f"✅ Fetched {len(df_products)} products")
    
    # Fetch carts with fallback
    print("\n📋 Fetching carts/orders...")
    carts = fetch_fakestore_carts()
    
    if carts is None:
        print("⚠️  FakeStoreAPI blocked. Trying DummyJSON...")
        carts = fetch_dummyjson_carts()
    
    if carts is None:
        print("❌ All cart sources failed")
        raise Exception("Unable to fetch carts from any API")
    
    df_carts = pd.DataFrame(carts)
    print(f"✅ Fetched {len(df_carts)} carts/orders")
    
    # Save to S3 or local storage
    print(f"\n🗄️  Storage Configuration: S3_RAW_BUCKET={'SET' if S3_BUCKET else 'NOT SET'}")
    
    if S3_BUCKET:
        try:
            s3 = boto3.client('s3')
            
            # Upload products
            temp_path = "/tmp/products.parquet"
            df_products.to_parquet(temp_path, index=False)
            s3.upload_file(temp_path, S3_BUCKET, f"raw/products/{date_str}/products.parquet")
            os.remove(temp_path)
            print(f"✅ Uploaded products to S3: s3://{S3_BUCKET}/raw/products/{date_str}/products.parquet")
            
            # Upload carts
            temp_path = "/tmp/orders.parquet"
            df_carts.to_parquet(temp_path, index=False)
            s3.upload_file(temp_path, S3_BUCKET, f"raw/orders/{date_str}/orders.parquet")
            os.remove(temp_path)
            print(f"✅ Uploaded carts to S3: s3://{S3_BUCKET}/raw/orders/{date_str}/orders.parquet")
        except Exception as e:
            print(f"⚠️  S3 upload failed: {e}. Saving locally instead...")
            os.makedirs("data/raw/products", exist_ok=True)
            df_products.to_parquet("data/raw/products/products.parquet", index=False)
            os.makedirs("data/raw/orders", exist_ok=True)
            df_carts.to_parquet("data/raw/orders/orders.parquet", index=False)
            print(f"✅ Saved locally to data/raw/")
    else:
        print("→ Saving to local filesystem...")
        os.makedirs("data/raw/products", exist_ok=True)
        df_products.to_parquet("data/raw/products/products.parquet", index=False)
        os.makedirs("data/raw/orders", exist_ok=True)
        df_carts.to_parquet("data/raw/orders/orders.parquet", index=False)
        print(f"✅ Saved locally to data/raw/")
    
    print("\n" + "=" * 70)
    print("✨ Data ingestion complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
