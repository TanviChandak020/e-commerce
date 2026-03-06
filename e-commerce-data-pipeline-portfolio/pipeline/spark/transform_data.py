from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, to_date, explode
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, ArrayType
import os

def create_spark_session():
    return SparkSession.builder \
        .appName("EcommerceDataTransformation") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()

def transform_orders(spark, raw_path, processed_path):
    # Schema for FakeStoreAPI carts
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("userId", IntegerType(), True),
        StructField("date", StringType(), True),
        StructField("products", ArrayType(
            StructType([
                StructField("productId", IntegerType(), True),
                StructField("quantity", IntegerType(), True)
            ])
        ), True)
    ])
    
    df = spark.read.parquet(raw_path)
    
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
    df_final.write.mode("overwrite").parquet(processed_path)

def main():
    spark = create_spark_session()
    
    RAW_BUCKET = os.getenv('S3_RAW_BUCKET')
    PROCESSED_BUCKET = os.getenv('S3_PROCESSED_BUCKET')
    
    # Example paths
    transform_orders(
        spark, 
        f"s3a://{RAW_BUCKET}/raw/orders/*/*/*/*.parquet",
        f"s3a://{PROCESSED_BUCKET}/processed/orders/"
    )
    
    spark.stop()

if __name__ == "__main__":
    main()
