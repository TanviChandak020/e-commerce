from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, to_date, explode
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, ArrayType
import os
import glob

def create_spark_session():
    return SparkSession.builder \
        .appName("EcommerceDataTransformation") \
        .config("spark.driver.memory", "2g") \
        .config("spark.executor.memory", "2g") \
        .getOrCreate()

def transform_orders(spark, raw_path, processed_path):
    """Transform raw orders data"""
    try:
        # Check if path exists
        if raw_path.startswith('s3a://'):
            print(f"Reading from S3: {raw_path}")
        else:
            # Local path
            if not os.path.exists(raw_path):
                # Try to find matching files
                glob_pattern = raw_path.replace('/*/*/*/', '/')
                matching_files = glob.glob(glob_pattern)
                if not matching_files:
                    print(f"⚠️  No files found at {raw_path}")
                    return
                raw_path = matching_files[0] if matching_files else raw_path
                print(f"Using local file: {raw_path}")
        
        df = spark.read.parquet(raw_path)
        print(f"✅ Loaded {df.count()} orders")
        
        # Flatten products array
        df_flattened = df.withColumn("product", explode(col("products"))) \
            .select(
                col("id").alias("order_id"),
                col("userId").alias("customer_id"),
                to_date(col("date")).alias("order_date"),
                col("product.productId").alias("product_id"),
                col("product.quantity").alias("quantity")
            )
        
        df_final = df_flattened.withColumn("processed_at", current_timestamp())
        
        # Create output directory if local
        if not processed_path.startswith('s3a://'):
            os.makedirs(processed_path, exist_ok=True)
        
        df_final.write.mode("overwrite").parquet(processed_path)
        print(f"✅ Transformed orders written to {processed_path}")
    except Exception as e:
        print(f"⚠️  Error transforming orders: {e}")
        raise

def transform_inventory(spark, raw_path, processed_path):
    """Transform raw inventory data"""
    try:
        if raw_path.startswith('s3a://'):
            print(f"Reading from S3: {raw_path}")
        else:
            # Local path
            if not os.path.exists(raw_path):
                glob_pattern = raw_path.replace('/*/*/*/', '/')
                matching_files = glob.glob(glob_pattern)
                if not matching_files:
                    print(f"⚠️  No files found at {raw_path}")
                    return
                raw_path = matching_files[0] if matching_files else raw_path
                print(f"Using local file: {raw_path}")
        
        df = spark.read.parquet(raw_path)
        print(f"✅ Loaded {df.count()} inventory items")
        
        df_final = df.withColumn("processed_at", current_timestamp())
        
        # Create output directory if local
        if not processed_path.startswith('s3a://'):
            os.makedirs(processed_path, exist_ok=True)
        
        df_final.write.mode("overwrite").parquet(processed_path)
        print(f"✅ Transformed inventory written to {processed_path}")
    except Exception as e:
        print(f"⚠️  Error transforming inventory: {e}")
        raise

def main():
    spark = create_spark_session()
    
    S3_RAW_BUCKET = os.getenv('S3_RAW_BUCKET', '').strip()
    S3_PROCESSED_BUCKET = os.getenv('S3_PROCESSED_BUCKET', '').strip()
    
    try:
        if S3_RAW_BUCKET and S3_PROCESSED_BUCKET:
            # Use S3 paths
            print("🔄 Using S3 for data transformation...")
            transform_orders(
                spark,
                f"s3a://{S3_RAW_BUCKET}/raw/orders/*/*/*/*.parquet",
                f"s3a://{S3_PROCESSED_BUCKET}/processed/orders/"
            )
            transform_inventory(
                spark,
                f"s3a://{S3_RAW_BUCKET}/raw/inventory/*/*/*/*.csv",
                f"s3a://{S3_PROCESSED_BUCKET}/processed/inventory/"
            )
        else:
            # Use local paths
            print("🔄 Using local filesystem for data transformation...")
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
        
        print("✅ Data transformation complete!")
    except Exception as e:
        print(f"❌ Transformation failed: {e}")
        raise
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
