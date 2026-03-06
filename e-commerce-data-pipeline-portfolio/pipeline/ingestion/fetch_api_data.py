import requests
import pandas as pd
import boto3
from datetime import datetime
import os

def fetch_fakestore_data(endpoint):
    """Fetch data from FakeStoreAPI"""
    url = f"https://fakestoreapi.com/{endpoint}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def upload_to_s3(df, bucket, key):
    """Upload DataFrame to S3 as Parquet"""
    s3 = boto3.client('s3')
    # In a real scenario, we'd use io.BytesIO to avoid local disk
    temp_path = f"/tmp/{os.path.basename(key)}"
    df.to_parquet(temp_path, index=False)
    s3.upload_file(temp_path, bucket, key)
    os.remove(temp_path)

def main():
    # Configuration
    S3_BUCKET = os.getenv('S3_RAW_BUCKET', 'my-ecommerce-raw-zone')
    date_str = datetime.now().strftime("%Y/%m/%d")
    
    print("Fetching products...")
    products = fetch_fakestore_data('products')
    df_products = pd.DataFrame(products)
    upload_to_s3(df_products, S3_BUCKET, f"raw/products/{date_str}/products.parquet")
    
    print("Fetching orders (carts)...")
    carts = fetch_fakestore_data('carts')
    df_carts = pd.DataFrame(carts)
    upload_to_s3(df_carts, S3_BUCKET, f"raw/orders/{date_str}/orders.parquet")
    
    print("Ingestion complete.")

if __name__ == "__main__":
    main()
