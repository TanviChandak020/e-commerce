# GitLab CI/CD Pipeline Setup Guide

## Overview

This document explains how to set up and run the e-commerce data pipeline using **GitLab CI/CD** instead of Apache Airflow.

## Pipeline Architecture

The GitLab CI/CD pipeline consists of 5 stages:

1. **Setup** - Initialize Python environment and install dependencies
2. **Ingest** - Fetch data from FakeStore API and generate inventory CSV
3. **Transform** - Process data with Apache Spark
4. **Load** - Load transformed data to Snowflake
5. **dbt** - Run dbt models and data quality tests

## Prerequisites

### 1. GitLab Repository Setup
- Push this project to a GitLab repository
- Ensure the `.gitlab-ci.yml` file is in the root directory

### 2. GitLab Runner
You need a GitLab Runner to execute the pipeline. Options:

#### Option A: Use Shared GitLab Runner
- No setup needed if your GitLab instance has shared runners
- Go to **Project > Settings > CI/CD > Runners** and enable

#### Option B: Install Self-Hosted Runner (Recommended for local development)
```bash
# Install GitLab Runner (macOS)
brew install gitlab-runner

# Register the runner
gitlab-runner register \
  --url https://gitlab.com/ \
  --registration-token <your-token> \
  --executor shell \
  --description "Local macOS Runner" \
  --tag-list "macos,local"

# Start the runner
gitlab-runner run
```

### 3. Environment Variables

Set these in **Project > Settings > CI/CD > Variables**:

**AWS Credentials:**
```
AWS_ACCESS_KEY_ID = <Your AWS Access Key>
AWS_SECRET_ACCESS_KEY = <Your AWS Secret Key>
AWS_DEFAULT_REGION = ap-south-1
S3_RAW_BUCKET = fake-store-raw-data--aps1-az1--x-s3
```

**Snowflake Credentials:**
```
SNOWFLAKE_USER = <Your Snowflake Username>
SNOWFLAKE_PASSWORD = <Your Snowflake Password>
SNOWFLAKE_ACCOUNT = qv97191.ap-southeast-1
SNOWFLAKE_WAREHOUSE = ECOM_WH
SNOWFLAKE_DATABASE = ECOM_DB
```

**dbt Profile Location:**
Create `~/.dbt/profiles.yml` with your Snowflake credentials (already configured locally).

## Pipeline Configuration

### Job Dependencies

```
setup:environment
    ↓
ingest:api_data ──┐
ingest:inventory ─┼─→ transform:spark
                  ↓
              load:snowflake
                  ↓
              dbt:run
                  ↓
              dbt:test
```

### Caching Strategy

- **Python dependencies** cached in `.cache/pip/`
- **Virtual environment** artifacts created after setup stage
- **dbt targets** preserved for 7 days to enable incremental runs

## Running the Pipeline

### Option 1: Push to GitLab (Automatic)
```bash
git push origin main
```
The pipeline triggers automatically on push.

### Option 2: Manual Trigger (GitLab UI)
1. Go to **Project > CI/CD > Pipelines**
2. Click **New Pipeline**
3. Select branch and run

### Option 3: Scheduled Runs (Optional)
1. Go to **Project > CI/CD > Schedules**
2. Click **New Schedule**
3. Configure frequency (e.g., daily at 2 AM)

## Pipeline Stages Explained

### Stage 1: Setup
- Creates Python 3.12 virtual environment
- Installs all dependencies from `requirements.txt`
- Caches for subsequent stages
- **Retry:** 2 attempts on failure

### Stage 2: Ingest (Parallel)
Two jobs run in parallel:

**ingest:api_data**
- Executes `pipeline/ingestion/fetch_api_data.py`
- Fetches products and carts from FakeStore API
- Uploads to S3 bucket

**ingest:inventory_csv**
- Executes `pipeline/ingestion/generate_inventory.py`
- Generates synthetic inventory data
- Uploads to S3 bucket

### Stage 3: Transform
**transform:spark**
- Executes `pipeline/spark/transform_data.py`
- Reads parquet from S3
- Performs Spark transformations
- Writes results back to S3

### Stage 4: Load
**load:snowflake**
- Connects to Snowflake using environment credentials
- Executes SQL from `pipeline/snowflake/copy_into.sql`
- Creates RAW and STAGING tables
- Only runs on `main` and `develop` branches

### Stage 5: dbt
**dbt:run**
- Executes `dbt run` to build data models
- Creates views in STAGING schema
- Creates tables in ANALYTICS schema

**dbt:test**
- Executes `dbt test` for data quality checks
- Runs 4 predefined tests
- **Fails pipeline** if tests fail (allow_failure: false)

## Environment Variables in Pipeline

The `.gitlab-ci.yml` uses:
- `PYTHON_VERSION`: 3.12
- `PIP_CACHE_DIR`: `.cache/pip` for dependency caching
- `VENV_PATH`: Location of virtual environment
- `PYTHONPATH`: Includes pipeline directory for imports

## Logging and Artifacts

### Logs
- Accessible in **Project > CI/CD > Pipelines > [Pipeline ID]**
- Each job shows real-time logs
- Failures show error stack traces

### Artifacts
- **Setup**: `.venv/` (cached for reuse)
- **Transform**: Spark outputs
- **dbt**: `pipeline/dbt/target/` (7 day retention)
- **All stages**: Environment files for next stages

## Error Handling

**Automatic Retries:**
- Ingestion: 2 retries on runner system failure
- Transform: 2 retries on runner system failure
- Load: 2 retries (Snowflake connection timeout)
- dbt: 2 retries (transient Snowflake issues)

**Failure Conditions:**
- ❌ Setup fails → entire pipeline stops
- ❌ Both ingestion jobs fail → transform skipped
- ❌ Transform fails → load is blocked
- ❌ Load fails → dbt stages skipped
- ❌ dbt:test fails → **pipeline fails** (data quality guaranteed)

## Monitoring Pipeline Health

### By Status
- **Green** (✅ Passed): All stages succeeded
- **Red** (❌ Failed): One or more stages failed
- **Blue** (⏳ Running): Pipeline in progress
- **Gray** (⏸ Skipped): Conditional stages not met

### Performance Metrics
- **Setup**: ~30-60 seconds
- **Ingest**: ~45-90 seconds (parallel)
- **Transform**: ~60-120 seconds
- **Load**: ~30-60 seconds
- **dbt run**: ~60-90 seconds
- **dbt test**: ~30-45 seconds

**Total Time**: ~5-8 minutes for full pipeline

## Comparing to Airflow

| Aspect | GitLab CI | Airflow |
|--------|-----------|---------|
| **Definition** | YAML config | Python DAG |
| **Trigger** | Git push, schedule, manual | Scheduler, sensor, API |
| **Monitoring** | GitLab UI | Airflow UI |
| **Cost** | No infrastructure needed | Requires server |
| **Dependencies** | Git + Runner | Airflow + DB |
| **Scalability** | Via runners | Via workers |
| **Retry Policy** | Built-in | Task-level |
| **Parallelization** | Native | Task dependencies |

## Troubleshooting

### Issue: "401 Unauthorized" on S3
**Solution:** Verify AWS credentials in CI/CD Variables

### Issue: "Role TRANSFORMER not granted" on Snowflake
**Solution:** Use `ACCOUNTADMIN` role or contact Snowflake admin

### Issue: "Python package not found"
**Solution:** Add package to `requirements.txt`, commit, and push

### Issue: Pipeline timeout
**Solution:** Increase timeout in `.gitlab-ci.yml` or optimize code

### Local Testing Without GitLab
```bash
# Install GitLab Runner for local execution
gitlab-runner exec shell ingest:api_data
gitlab-runner exec shell transform:spark
```

## Best Practices

1. **Always test locally** before pushing to GitLab
2. **Use protected branches** for main/develop
3. **Set up branch rules** requiring CI to pass
4. **Monitor pipeline metrics** in Project > Analytics > CI/CD
5. **Keep secrets** in CI/CD Variables (never in code)
6. **Archive artifacts** for long-term retention
7. **Set up notifications** for failed pipelines

## Next Steps

1. Commit `.gitlab-ci.yml` to repository
2. Configure GitLab Runner (self-hosted or shared)
3. Add CI/CD variables to project settings
4. Push to main branch
5. Monitor first pipeline run in **CI/CD > Pipelines**
6. Verify all stages Pass ✅

## Additional Resources

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [GitLab Runner Installation](https://docs.gitlab.com/runner/)
- [GitLab CI/CD YAML Reference](https://docs.gitlab.com/ee/ci/yaml/)
- [Scheduling Pipeline Runs](https://docs.gitlab.com/ee/ci/pipelines/schedules.html)

---

**Pipeline Status:** Ready for deployment 🚀
