import os
import subprocess
import tempfile
from typing import Optional

import boto3
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, explode, to_date


def create_spark_session() -> SparkSession:
    """Create and configure a Spark session.

    Returns:
        SparkSession: Configured Spark session.
    """ \
        .appName("EcommerceDataTransformation") \
        .config("spark.driver.memory", "2g") \
        .config("spark.executor.memory", "2g") \
        .getOrCreate()

def download_from_s3(
    s3_client: "boto3.client", bucket: str, prefix: str
) -> Optional[str]:
    """Download latest parquet file matching prefix from S3.

    Args:
        s3_client: Boto3 S3 client.
        bucket: S3 bucket name.
        prefix: S3 key prefix to search.

    Returns:
        Path to downloaded file or None if not found.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if 'Contents' not in response:
            print(f"⚠️  No files found at s3://{bucket}/{prefix}")
            return None
        
        # Get the latest file
        files = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
        if not files:
            return None
        
        latest_file = files[0]['Key']
        print(f"📥 Reading from S3: s3://{bucket}/{latest_file}")
        
        # Download to temp file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.parquet')
        s3_client.download_file(bucket, latest_file, temp_path)
        return temp_path
    except Exception as e:
        print(f"❌ Error downloading from S3: {e}")
        return None

def upload_to_s3(
    s3_client: "boto3.client", bucket: str, local_path: str, s3_key: str
) -> None:
    """Upload local parquet file to S3.

    Args:
        s3_client: Boto3 S3 client.
        bucket: S3 bucket name.
        local_path: Local file path.
        s3_key: S3 destination key.
    """
    try:
        s3_client.upload_file(local_path, bucket, s3_key)
        print(f"📤 Uploaded to S3: s3://{bucket}/{s3_key}")
    except Exception as e:
        print(f"❌ Error uploading to S3: {e}")
        raise

def transform_orders(spark: SparkSession, raw_path: str, processed_path: str) -> None:
    """Transform raw orders data - handles both FakeStore and DummyJSON formats.

    Args:
        spark: Spark session.
        raw_path: Path to raw parquet data.
        processed_path: Output path for processed data.
    """
    try:
        print(f"Reading orders from: {raw_path}")
        
        if not os.path.exists(raw_path):
            print(f"⚠️  No files found at {raw_path}")
            return
        
        df = spark.read.parquet(raw_path)
        print(f"✅ Loaded {df.count()} orders")
        
        # Check schema to determine format
        schema_str = str(df.schema)
        is_dummyjson = "discountedTotal" in schema_str or "discountPercentage" in schema_str
        
        if is_dummyjson:
            print("🔎 Detected DummyJSON format")
            # DummyJSON: products array has {id, title, price, quantity, thumbnail, discountPercentage, discountedTotal, total}
            df_flattened = df.withColumn("product", explode(col("products"))) \
                .select(
                    col("id").alias("order_id"),
                    col("userId").alias("customer_id"),
                    col("date").alias("order_date"),
                    col("product.id").alias("product_id"),
                    col("product.quantity").alias("quantity")
                )
        else:
            print("🔎 Detected FakeStore format")
            # FakeStore: products array has {productId, quantity}
            df_flattened = df.withColumn("product", explode(col("products"))) \
                .select(
                    col("id").alias("order_id"),
                    col("userId").alias("customer_id"),
                    to_date(col("date")).alias("order_date"),
                    col("product.productId").alias("product_id"),
                    col("product.quantity").alias("quantity")
                )
        
        df_final = df_flattened.withColumn("processed_at", current_timestamp())
        
        os.makedirs(processed_path, exist_ok=True)
        df_final.write.mode("overwrite").parquet(processed_path)
        print(f"✅ Transformed orders written to {processed_path}")
    except Exception as e:
        print(f"⚠️  Error transforming orders: {e}")
        import traceback
        traceback.print_exc()
        raise

def transform_inventory(spark: SparkSession, raw_path: str, processed_path: str) -> None:
    """Transform raw inventory data.

    Args:
        spark: Spark session.
        raw_path: Path to raw parquet data.
        processed_path: Output path for processed data.
    """
    try:
        print(f"Reading inventory from: {raw_path}")
        
        if not os.path.exists(raw_path):
            print(f"⚠️  No files found at {raw_path}")
            return
        
        df = spark.read.parquet(raw_path)
        print(f"✅ Loaded {df.count()} inventory items")
        
        df_final = df.withColumn("processed_at", current_timestamp())
        
        os.makedirs(processed_path, exist_ok=True)
        df_final.write.mode("overwrite").parquet(processed_path)
        print(f"✅ Transformed inventory written to {processed_path}")
    except Exception as e:
        print(f"⚠️  Error transforming inventory: {e}")
        raise

def main() -> None:
    """Orchestrate data transformation from S3, process with Spark, upload back."""
    spark = create_spark_session()

    S3_RAW_BUCKET = os.getenv('S3_RAW_BUCKET', '').strip()
    S3_PROCESSED_BUCKET = os.getenv('S3_PROCESSED_BUCKET', '').strip()
    AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1').strip()
    
    print("=" * 70)
    print("🔄 Spark Data Transformation")
    print("=" * 70)
    print("\n🔍 Configuration:")
    print(f"   S3_RAW_BUCKET: {'✅ SET' if S3_RAW_BUCKET else '❌ NOT SET'}")
    print(f"   S3_PROCESSED_BUCKET: {'✅ SET' if S3_PROCESSED_BUCKET else '❌ NOT SET'}")
    
    try:
        if S3_RAW_BUCKET and S3_PROCESSED_BUCKET:
            print("\n🔄 Using S3 for data transformation (boto3 + local processing)...\n")
            s3_client = boto3.client('s3', region_name=AWS_REGION)
            
            # Download and transform orders
            raw_orders_key = "raw/orders/"
            orders_file = download_from_s3(s3_client, S3_RAW_BUCKET, raw_orders_key)
            if orders_file:
                try:
                    transform_orders(spark, orders_file, "data/processed/orders")
                    # Upload processed orders
                    result = subprocess.run(['find', 'data/processed/orders', '-name', 'part-*.parquet'], 
                                          capture_output=True, text=True)
                    if result.stdout.strip():
                        processed_file = result.stdout.strip().split('\n')[0]
                        upload_to_s3(s3_client, S3_PROCESSED_BUCKET, processed_file, "processed/orders/orders.parquet")
                except Exception as e:
                    print(f"⚠️  Error with orders: {e}")
                finally:
                    if os.path.exists(orders_file):
                        os.remove(orders_file)
            
            # Download and transform products (saved as inventory)
            raw_products_key = "raw/products/"
            products_file = download_from_s3(s3_client, S3_RAW_BUCKET, raw_products_key)
            if products_file:
                try:
                    # For products, we just add timestamp
                    df_products = spark.read.parquet(products_file)
                    print(f"✅ Loaded {df_products.count()} products")
                    df_products_final = df_products.withColumn("processed_at", current_timestamp())
                    os.makedirs("data/processed/products", exist_ok=True)
                    df_products_final.write.mode("overwrite").parquet("data/processed/products")
                    print("✅ Transformed products written to data/processed/products")

                    # Upload processed products
                    result = subprocess.run(
                        ["find", "data/processed/products", "-name", "part-*.parquet"], 
                                          capture_output=True, text=True)
                    if result.stdout.strip():
                        processed_file = result.stdout.strip().split('\n')[0]
                        upload_to_s3(s3_client, S3_PROCESSED_BUCKET, processed_file, "processed/products/products.parquet")
                except Exception as e:
                    print(f"⚠️  Error transforming products: {e}")
                finally:
                    if os.path.exists(products_file):
                        os.remove(products_file)
        
        else:
            print("\n🔄 Using local filesystem for data transformation...\n")
            transform_orders(
                spark,
                "data/raw/orders/orders.parquet",
                "data/processed/orders"
            )
            transform_inventory(
                spark,
                "data/raw/inventory/inventory.csv",
                "data/processed/inventory"
            )
        
        print("\n" + "=" * 70)
        print("✨ Data transformation complete!")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Transformation failed: {e}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
