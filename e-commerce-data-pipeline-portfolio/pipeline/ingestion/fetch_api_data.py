import requests
import pandas as pd
import boto3
from datetime import datetime, timedelta
import os
import time
import numpy as np

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
                print(f"Failed to fetch {endpoint} after {max_retries} attempts: {e}")
                return None
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Request error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"Failed to fetch {endpoint}: {e}")
                return None

def generate_synthetic_products(num_products=20):
    """Generate synthetic product data as fallback"""
    categories = ['electronics', 'clothing', 'books', 'home', 'sports']
    data = []
    for i in range(1, num_products + 1):
        data.append({
            'id': i,
            'title': f'Product {i}',
            'price': round(np.random.uniform(10, 500), 2),
            'description': f'High quality product {i}',
            'category': np.random.choice(categories),
            'image': f'https://via.placeholder.com/250?text=Product{i}',
            'rating': {
                'rate': round(np.random.uniform(1, 5), 1),
                'count': int(np.random.uniform(10, 500))
            }
        })
    return data

def generate_synthetic_carts(num_carts=20):
    """Generate synthetic cart/order data as fallback"""
    data = []
    for i in range(1, num_carts + 1):
        date = datetime.now() - timedelta(days=np.random.randint(0, 30))
        num_products = np.random.randint(1, 5)
        products = []
        for _ in range(num_products):
            products.append({
                'productId': np.random.randint(1, 21),
                'quantity': np.random.randint(1, 5)
            })
        data.append({
            'id': i,
            'userId': np.random.randint(1, 11),
            'date': date.isoformat(),
            'products': products
        })
    return data

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
    
    # Fetch products
    try:
        print("📦 Fetching products from FakeStoreAPI...")
        products = fetch_fakestore_data('products')
        if products is None:
            print("⚠️  API fetch failed. Generating synthetic products...")
            products = generate_synthetic_products()
        else:
            print(f"✅ Fetched {len(products)} products from API")
    except Exception as e:
        print(f"⚠️  Error fetching products: {e}. Generating synthetic data...")
        products = generate_synthetic_products()
    
    df_products = pd.DataFrame(products)
    print(f"✅ Prepared {len(df_products)} products")
    
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
    
    # Fetch orders/carts
    try:
        print("\n📦 Fetching orders from FakeStoreAPI...")
        carts = fetch_fakestore_data('carts')
        if carts is None:
            print("⚠️  API fetch failed. Generating synthetic orders...")
            carts = generate_synthetic_carts()
        else:
            print(f"✅ Fetched {len(carts)} orders from API")
    except Exception as e:
        print(f"⚠️  Error fetching orders: {e}. Generating synthetic data...")
        carts = generate_synthetic_carts()
    
    df_carts = pd.DataFrame(carts)
    print(f"✅ Prepared {len(df_carts)} orders")
    
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
    
    print("\n✅ Ingestion complete!")

if __name__ == "__main__":
    main()
