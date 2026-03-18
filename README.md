# E-Commerce Data Pipeline

A fully automated end-to-end data pipeline for e-commerce analytics using GitHub Actions, Apache Spark, and Snowflake.

## 🏗️ Architecture

```
┌─────────────────────┐
│  Data Ingestion     │  DummyJSON/FakeStoreAPI → S3 Raw
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Data Storage       │  S3 Raw Data Layer
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Transformation     │  Spark ETL/Data Quality
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Data Storage       │  S3 Processed Data Layer
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Data Warehouse     │  Snowflake COPY INTO
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Data Modeling      │  dbt Transformations
└─────────────────────┘
```

## 📁 Project Structure

```
e-commerce/
├── .github/
│   └── workflows/
│       └── main.yml                    # GitHub Actions CI/CD pipeline
├── e-commerce-data-pipeline-portfolio/
│   ├── README.md                       # Project documentation
│   ├── pipeline/
│   │   ├── ingestion/
│   │   │   ├── fetch_api_data.py       # API data ingestion (DummyJSON fallback)
│   │   │   └── generate_inventory.py   # Inventory data generation
│   │   ├── spark/
│   │   │   └── transform_data.py       # PySpark transformations (ETL)
│   │   ├── snowflake/
│   │   │   ├── load_to_snowflake.py    # Snowflake data loading
│   │   │   └── copy_into.sql           # SQL templates
│   │   └── dbt/
│   │       ├── dbt_project.yml         # dbt project configuration
│   │       ├── profiles.yml            # Snowflake connection profile
│   │       ├── models/
│   │       │   ├── schema.yml          # Table documentation
│   │       │   ├── staging/            # Staging models
│   │       │   └── marts/              # Fact/dimension tables
│   │       └── README.md
├── .gitignore                          # Git ignore rules
├── requirements.txt                    # Python dependencies
└── README.md                           # This file
```

## 🚀 Getting Started

### Prerequisites

- **GitHub Repository** with Actions enabled
- **AWS Account** with S3 bucket and IAM credentials
- **Snowflake Account** with warehouse and database
- **Python 3.12+** (for local development)

### 1. Setup GitHub Secrets

Navigate to: **Repository → Settings → Secrets and variables → Actions**

Add these secrets:

```
# AWS Credentials
AWS_ACCESS_KEY_ID              # AWS IAM access key
AWS_SECRET_ACCESS_KEY          # AWS IAM secret key
AWS_DEFAULT_REGION             # AWS region (e.g., ap-south-1)

# S3 Buckets
S3_RAW_BUCKET                  # Bucket for raw data (e.g., my-ecom-raw)
S3_PROCESSED_BUCKET            # Bucket for processed data (e.g., my-ecom-processed)

# Snowflake Credentials
SNOWFLAKE_USER                 # Snowflake login username
SNOWFLAKE_PASSWORD             # Snowflake password
SNOWFLAKE_ACCOUNT              # Account ID (e.g., xy12345 - not xyz123.region)
SNOWFLAKE_WAREHOUSE            # Warehouse name (e.g., COMPUTE_WH)
SNOWFLAKE_DATABASE             # Database name (e.g., ECOM_DB)
```

### 2. Create S3 Buckets

```bash
aws s3 mb s3://my-ecom-raw --region ap-south-1
aws s3 mb s3://my-ecom-processed --region ap-south-1
```

### 3. Trigger the Pipeline

**Option A: Automatic**
- Push to `main` or `develop` branch
- Workflow runs automatically

**Option B: Manual**
- Go to **Actions tab → E-Commerce Data Pipeline**
- Click **Run workflow → Run workflow**

## 📊 Pipeline Stages

### Stage 1: Data Ingestion (2-3 min)
- **Job**: `ingest-api`, `ingest-inventory`
- **Input**: DummyJSON API / FakeStoreAPI
- **Output**: S3 raw data (products.parquet, orders.parquet)
- **Features**: 
  - Automatic API fallback (DummyJSON if FakeStore blocks)
  - Retry logic with exponential backoff
  - Local storage fallback if S3 unavailable

### Stage 2: Data Transformation (1-2 min)
- **Job**: `transform-spark`
- **Input**: S3 raw data
- **Output**: S3 processed data
- **Features**:
  - PySpark transformations
  - Data flattening and normalization
  - Schema detection (FakeStore vs DummyJSON formats)
  - Timestamp tracking

### Stage 3: Snowflake Loading (1-2 min)
- **Job**: `load-snowflake`
- **Input**: S3 processed data
- **Output**: Snowflake RAW schema tables
- **Features**:
  - Auto table creation
  - COPY INTO from S3
  - Data validation
  - Error handling and fallback

### Stage 4: Data Modeling (1 min)
- **Job**: `dbt-models`
- **Input**: Snowflake RAW tables
- **Output**: Snowflake TRANSFORMED tables
- **Features**:
  - dbt models and tests
  - Fact/dimension tables
  - Incremental loads
  - Documentation

## 📈 Data Models

### RAW Schema (Snowflake)
- **ORDERS_RAW**: Order transactions with flattened products
- **PRODUCTS_RAW**: Full product catalog

### TRANSFORMED Schema (dbt)
- **FACT_ORDERS**: Fact table (orders with denormalized product details)
- **FACT_PRODUCTS**: Product facts with aggregations
- **STG_ORDERS**: Staging layer for orders
- **STG_PRODUCTS**: Staging layer for products

## 🔧 Configuration Files

### requirements.txt
Python dependencies for the pipeline:
```
pandas>=2.1.0
boto3>=1.28.0
pyspark>=3.5.0
snowflake-connector-python>=3.0.0
dbt-core==1.7.8
dbt-snowflake==1.7.1
```

### .github/workflows/main.yml
GitHub Actions workflow definition with 7 jobs:
1. **setup** - Install dependencies, cache setup
2. **ingest-api** - Fetch API data
3. **ingest-inventory** - Generate inventory
4. **transform-spark** - Transform data
5. **load-snowflake** - Load to Snowflake
6. **dbt-models** - Run dbt models
7. **summary** - Pipeline summary

### dbt Configuration
- **profiles.yml**: Snowflake connection details (reads from env vars)
- **dbt_project.yml**: Project settings and model configurations

## ✅ Monitoring & Logs

### GitHub Actions Logs
1. Go to: **Actions → E-Commerce Data Pipeline → [Latest run]**
2. Expand each job to see:
   - ✅ Successful steps (green checkmarks)
   - ❌ Failed steps (red X)
   - 📋 Detailed output for debugging

### Key Log Indicators

**Data Ingestion Success:**
```
✅ Fetched 20 products
✅ Fetched 20 carts/orders
✅ Uploaded to S3: s3://bucket/raw/products/
```

**Transformation Success:**
```
✅ Loaded 20 orders
🔎 Detected DummyJSON format
✅ Transformed orders written
📤 Uploaded to S3: s3://bucket/processed/orders/
```

**Snowflake Success:**
```
✅ Connected to Snowflake
✅ Orders loaded successfully
✅ Products loaded successfully
📊 Orders: 20 rows
📊 Products: 20 rows
```

## 🐛 Troubleshooting

### API Blocking (403 Forbidden)
- **Cause**: FakeStoreAPI blocks GitHub Actions IPs
- **Solution**: Automatic fallback to DummyJSON API
- **Action**: None needed - pipeline handles automatically

### S3 Upload Fails (404 Not Found)
- **Cause**: Bucket name incorrect or doesn't exist
- **Solution**: 
  1. Verify bucket name in GitHub secrets `S3_RAW_BUCKET`
  2. Ensure bucket exists: `aws s3 ls | grep bucket-name`
  3. Verify AWS region matches

### Snowflake Connection Failed
- **Cause**: Invalid account ID format
- **Solution**:
  1. Get account ID from Snowflake URL (e.g., `xy12345` from `https://xy12345.us-east-1.snowflakecomputing.com`)
  2. Update `SNOWFLAKE_ACCOUNT` secret with ONLY the account ID
  3. Don't include region or domain

### Data Transform Error - Field Not Found
- **Cause**: Schema mismatch between FakeStore and DummyJSON
- **Solution**: Automatic in transform_data.py (detects format and adapts)

### dbt Model Fails
- **Cause**: Snowflake table doesn't exist or has different schema
- **Action**: Check Snowflake RAW tables were created and populated

## 📝 Development Workflow

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Test data ingestion
python e-commerce-data-pipeline-portfolio/pipeline/ingestion/fetch_api_data.py

# Test Spark transformation (requires spark-submit or local Spark)
python e-commerce-data-pipeline-portfolio/pipeline/spark/transform_data.py

# Test dbt models (requires Snowflake connection)
cd e-commerce-data-pipeline-portfolio/pipeline/dbt
dbt debug
dbt run
```

### Adding New Data Sources
1. Create new ingestion script in `pipeline/ingestion/`
2. Add new job in `.github/workflows/main.yml`
3. Configure GitHub secrets for credentials
4. Test locally before pushing

## 📊 Performance Metrics

Typical pipeline execution times:
- **Data Ingestion**: 2-3 minutes
- **Spark Transformation**: 1-2 minutes  
- **Snowflake Load**: 1-2 minutes
- **dbt Models**: 30 seconds - 1 minute
- **Total Runtime**: ~6-8 minutes

## 🔐 Security

### Secrets Management
- All credentials stored in GitHub Secrets (encrypted)
- Never commit `.env` files or credentials
- Environment variables read at runtime only

### Data Security
- S3 bucket policies restrict access
- Snowflake uses encrypted connection (TLS)
- Private GitHub repository (recommended)

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [dbt Documentation](https://docs.getdbt.com/)

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Push to branch: `git push origin feature/your-feature`
4. Create a Pull Request with description

## 📄 License

MIT License - See LICENSE file for details

## 👤 Author

**Tanvi Chandak**
- GitHub: [@TanviChandak020](https://github.com/TanviChandak020)
- Email: contact@example.com

## ✨ Acknowledgments

Built with:
- GitHub Actions for CI/CD
- Apache Spark for data processing
- Snowflake for cloud data warehouse
- dbt for data modeling
- DummyJSON & FakeStoreAPI for test data

---

**Last Updated**: March 18, 2026
**Status**: ✅ Production Ready
