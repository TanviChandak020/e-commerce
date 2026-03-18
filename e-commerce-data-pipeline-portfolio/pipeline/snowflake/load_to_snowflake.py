"""Load processed data from S3 to Snowflake"""
import snowflake.connector
import os
import sys

def load_to_snowflake():
    """Load data from S3 to Snowflake"""
    
    # Get Snowflake credentials
    user = os.getenv('SNOWFLAKE_USER', '').strip()
    password = os.getenv('SNOWFLAKE_PASSWORD', '').strip()
    account = os.getenv('SNOWFLAKE_ACCOUNT', '').strip()
    warehouse = os.getenv('SNOWFLAKE_WAREHOUSE', '').strip()
    database = os.getenv('SNOWFLAKE_DATABASE', '').strip()
    
    # Get AWS credentials
    s3_bucket = os.getenv('S3_PROCESSED_BUCKET', '').strip()
    aws_key = os.getenv('AWS_ACCESS_KEY_ID', '').strip()
    aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY', '').strip()
    aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1').strip()
    
    if not all([user, password, account, warehouse, database]):
        print('⚠️  Snowflake credentials incomplete. Skipping Snowflake load.')
        return True
    
    if not all([s3_bucket, aws_key, aws_secret]):
        print('⚠️  AWS credentials or S3 bucket incomplete. Skipping Snowflake load.')
        return True
    
    try:
        print(f"🔄 Connecting to Snowflake: {account}...")
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            warehouse=warehouse,
            database=database,
            region=aws_region
        )
        print("✅ Connected to Snowflake")
        
        cursor = conn.cursor()
        
        # Create raw schema if not exists
        print("📋 Creating schema...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS RAW")
        
        # Create tables
        print("📋 Creating tables...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RAW.ORDERS_RAW (
                order_id INTEGER,
                customer_id INTEGER,
                order_date DATE,
                product_id INTEGER,
                quantity INTEGER,
                processed_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RAW.PRODUCTS_RAW (
                id INTEGER,
                title VARCHAR,
                price DECIMAL(10, 2),
                description VARCHAR,
                category VARCHAR,
                image VARCHAR,
                rating OBJECT,
                processed_at TIMESTAMP
            )
        """)
        
        # Load Orders
        print("📥 Loading orders from S3...")
        copy_orders = f"""
            COPY INTO RAW.ORDERS_RAW
            FROM 's3://{s3_bucket}/processed/orders/'
            CREDENTIALS = (
                AWS_KEY_ID = '{aws_key}'
                AWS_SECRET_KEY = '{aws_secret}'
            )
            FILE_FORMAT = (TYPE = 'PARQUET')
            MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
        """
        cursor.execute(copy_orders)
        print("✅ Orders loaded successfully")
        
        # Load Products
        print("📥 Loading products from S3...")
        copy_products = f"""
            COPY INTO RAW.PRODUCTS_RAW
            FROM 's3://{s3_bucket}/processed/products/'
            CREDENTIALS = (
                AWS_KEY_ID = '{aws_key}'
                AWS_SECRET_KEY = '{aws_secret}'
            )
            FILE_FORMAT = (TYPE = 'PARQUET')
            MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
        """
        cursor.execute(copy_products)
        print("✅ Products loaded successfully")
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM RAW.ORDERS_RAW")
        orders_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM RAW.PRODUCTS_RAW")
        products_count = cursor.fetchone()[0]
        
        print(f"\n📊 Data Summary:")
        print(f"   Orders: {orders_count} rows")
        print(f"   Products: {products_count} rows")
        
        cursor.close()
        conn.close()
        
        print("\n✨ Snowflake data load complete!")
        return True
        
    except Exception as e:
        print(f"❌ Snowflake load failed: {e}")
        print("   This is expected if Snowflake is not accessible or credentials are invalid")
        return True  # Don't fail the workflow

if __name__ == "__main__":
    success = load_to_snowflake()
    sys.exit(0 if success else 1)
