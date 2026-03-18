import pandas as pd
import numpy as np
import boto3
from datetime import datetime
import os

def generate_inventory_data(num_products=20):
    """Generate synthetic inventory data"""
    data = {
        'product_id': range(1, num_products + 1),
        'supplier_id': np.random.randint(100, 105, size=num_products),
        'stock_quantity': np.random.randint(0, 500, size=num_products),
        'restock_threshold': np.random.randint(10, 50, size=num_products),
        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return pd.DataFrame(data)

def main():
    S3_BUCKET = os.getenv('S3_RAW_BUCKET', 'my-ecommerce-raw-zone')
    
    if S3_BUCKET == 'my-ecommerce-raw-zone':
        print("⚠️  Using default bucket name. Set S3_RAW_BUCKET environment variable for production.")
    
    date_str = datetime.now().strftime("%Y/%m/%d")
    
    print("Generating inventory feed...")
    df_inventory = generate_inventory_data()
    print(f"✅ Generated {len(df_inventory)} inventory records")
    
    # Save as CSV for the "CSV Source" requirement
    temp_path = "/tmp/inventory_feed.csv"
    df_inventory.to_csv(temp_path, index=False)
    
    try:
        s3 = boto3.client('s3')
        s3.upload_file(temp_path, S3_BUCKET, f"raw/inventory/{date_str}/inventory.csv")
        os.remove(temp_path)
        print(f"✅ Uploaded inventory to S3: {S3_BUCKET}/raw/inventory/{date_str}/inventory.csv")
        print("✅ Inventory ingestion complete.")
    except Exception as e:
        print(f"⚠️  Failed to upload inventory to S3: {e}")
        print(f"   Bucket: {S3_BUCKET}")
        print(f"   Please ensure the S3 bucket exists and credentials are correct")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

if __name__ == "__main__":
    main()
