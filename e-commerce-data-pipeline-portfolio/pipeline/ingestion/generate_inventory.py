import os
from datetime import datetime

import boto3
import numpy as np
import pandas as pd


def generate_inventory_data(num_products: int = 20) -> pd.DataFrame:
    """Generate synthetic inventory data.

    Creates a DataFrame with product inventory information including
    supplier ID, stock quantity, and restock threshold.

    Args:
        num_products: Number of synthetic products to generate.

    Returns:
        DataFrame with inventory data.
    """
    data = {
        'product_id': range(1, num_products + 1),
        'supplier_id': np.random.randint(100, 105, size=num_products),
        'stock_quantity': np.random.randint(0, 500, size=num_products),
        'restock_threshold': np.random.randint(10, 50, size=num_products),
        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return pd.DataFrame(data)

def main() -> None:
    """Generate and upload inventory data to S3."""
    S3_BUCKET = os.getenv('S3_RAW_BUCKET', '').strip()
    date_str = datetime.now().strftime("%Y/%m/%d")
    
    print("Generating inventory feed...")
    df_inventory = generate_inventory_data()
    print(f"✅ Generated {len(df_inventory)} inventory records")
    
    # Save as CSV for the "CSV Source" requirement
    temp_path = "/tmp/inventory_feed.csv"
    df_inventory.to_csv(temp_path, index=False)
    
    if not S3_BUCKET:
        print("⚠️  S3_RAW_BUCKET not configured. Saving locally instead.")
        local_dir = "data/raw/inventory"
        os.makedirs(local_dir, exist_ok=True)
        local_path = f"{local_dir}/inventory.csv"
        df_inventory.to_csv(local_path, index=False)
        print(f"✅ Saved inventory locally: {local_path}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return
    
    try:
        s3 = boto3.client('s3')
        s3.upload_file(temp_path, S3_BUCKET, f"raw/inventory/{date_str}/inventory.csv")
        os.remove(temp_path)
        print(f"✅ Uploaded inventory to S3: {S3_BUCKET}/raw/inventory/{date_str}/inventory.csv")
        print("✅ Inventory ingestion complete.")
    except Exception as e:
        print(f"⚠️  Failed to upload to S3: {e}")
        print(f"   Bucket: {S3_BUCKET}")
        print("   Saving locally as fallback...")
        local_dir = "data/raw/inventory"
        os.makedirs(local_dir, exist_ok=True)
        local_path = f"{local_dir}/inventory.csv"
        df_inventory.to_csv(local_path, index=False)
        print(f"✅ Saved inventory locally: {local_path}")
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    main()
