/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Cloud, 
  Workflow, 
  Code2, 
  FileText, 
  Layers, 
  ArrowRight, 
  Github, 
  ExternalLink,
  Terminal,
  Server,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  Menu,
  X
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Project File Content (Simulated for display)
const PROJECT_FILES = {
  'Ingestion: API': {
    path: 'pipeline/ingestion/fetch_api_data.py',
    language: 'python',
    content: `import requests
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
    temp_path = f"/tmp/{os.path.basename(key)}"
    df.to_parquet(temp_path, index=False)
    s3.upload_file(temp_path, bucket, key)
    os.remove(temp_path)

def main():
    S3_BUCKET = os.getenv('S3_RAW_BUCKET', 'my-ecommerce-raw-zone')
    date_str = datetime.now().strftime("%Y/%m/%d")
    
    products = fetch_fakestore_data('products')
    df_products = pd.DataFrame(products)
    upload_to_s3(df_products, S3_BUCKET, f"raw/products/{date_str}/products.parquet")`
  },
  'Transformation: Spark': {
    path: 'pipeline/spark/transform_data.py',
    language: 'python',
    content: `from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, to_date, explode

def transform_orders(spark, raw_path, processed_path):
    df = spark.read.parquet(raw_path)
    
    # Flatten products array and clean schema
    df_flattened = df.withColumn("product", explode(col("products"))) \\
        .select(
            col("id").alias("order_id"),
            col("userId").alias("customer_id"),
            to_date(col("date")).alias("order_date"),
            col("product.productId").alias("product_id"),
            col("product.quantity").alias("quantity")
        )
    
    df_final = df_flattened.withColumn("processed_at", current_timestamp())
    df_final.write.mode("overwrite").parquet(processed_path)`
  },
  'Warehouse: Snowflake': {
    path: 'pipeline/snowflake/setup.sql',
    language: 'sql',
    content: `-- 1. Create Warehouse
CREATE OR REPLACE WAREHOUSE ECOM_WH 
WITH WAREHOUSE_SIZE = 'XSMALL' 
AUTO_SUSPEND = 120;

-- 2. Create External Stage (S3)
CREATE OR REPLACE STAGE ECOM_DB.RAW.S3_PROCESSED_STAGE
URL = 's3://my-ecommerce-processed-zone/'
CREDENTIALS = (AWS_KEY_ID = 'XXXX' AWS_SECRET_KEY = 'XXXX');

-- 3. Load Orders via COPY INTO
COPY INTO ECOM_DB.RAW.ORDERS_RAW
FROM @ECOM_DB.RAW.S3_PROCESSED_STAGE/processed/orders/
FILE_FORMAT = (TYPE = 'PARQUET')
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;`
  },
  'Modeling: dbt': {
    path: 'pipeline/dbt/models/marts/fact_orders.sql',
    language: 'sql',
    content: `-- models/marts/fact_orders.sql
WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),
products AS (
    SELECT * FROM {{ ref('stg_products') }}
),
final AS (
    SELECT
        o.order_id,
        o.customer_id,
        o.order_date,
        o.product_id,
        o.quantity,
        p.price,
        p.category,
        (o.quantity * p.price) AS total_revenue
    FROM orders o
    LEFT JOIN products p ON o.product_id = p.product_id
)
SELECT * FROM final`
  },
  'Orchestration: Airflow': {
    path: 'pipeline/airflow/dags/ecommerce_pipeline_dag.py',
    language: 'python',
    content: `from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

with DAG('ecommerce_data_pipeline', schedule_interval='@daily') as dag:
    ingest_api = PythonOperator(task_id='ingest_api', python_callable=fetch_api)
    
    transform_spark = EmrAddStepsOperator(
        task_id='transform_spark',
        job_flow_id='J-123',
        steps=[spark_step]
    )
    
    load_snowflake = SnowflakeOperator(
        task_id='load_snowflake',
        sql='pipeline/snowflake/copy_into.sql'
    )
    
    ingest_api >> transform_spark >> load_snowflake`
  }
};

const ARCHITECTURE_STEPS = [
  { id: 'ingest', title: 'Ingestion', icon: Cloud, color: 'text-blue-500', bg: 'bg-blue-50', desc: 'Python scripts fetching from FakeStoreAPI & CSV' },
  { id: 'raw', title: 'Raw Storage', icon: Database, color: 'text-orange-500', bg: 'bg-orange-50', desc: 'Amazon S3 partitioned by YYYY/MM/DD' },
  { id: 'spark', title: 'Transformation', icon: Terminal, color: 'text-purple-500', bg: 'bg-purple-50', desc: 'PySpark on EMR for cleaning & schema enforcement' },
  { id: 'snowflake', title: 'Warehouse', icon: Server, color: 'text-cyan-500', bg: 'bg-cyan-50', desc: 'Snowflake COPY INTO from S3 Parquet' },
  { id: 'dbt', title: 'Modeling', icon: Layers, color: 'text-emerald-500', bg: 'bg-emerald-50', desc: 'dbt for Star Schema (Staging → Marts)' },
  { id: 'airflow', title: 'Orchestration', icon: Workflow, color: 'text-red-500', bg: 'bg-red-50', desc: 'Airflow DAG chaining the entire flow' },
];

export default function App() {
  const [activeFile, setActiveFile] = useState(Object.keys(PROJECT_FILES)[0]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex flex-col font-sans text-slate-900">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-600 p-2 rounded-lg">
            <Database className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-xl tracking-tight">E-Commerce Data Pipeline</h1>
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Portfolio Project • Data Engineering</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <a href="#" className="flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">
            <Github className="w-4 h-4" />
            Source Code
          </a>
          <button className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-indigo-700 transition-colors flex items-center gap-2">
            View Architecture
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className={`bg-white border-r border-slate-200 transition-all duration-300 ${isSidebarOpen ? 'w-80' : 'w-0'} overflow-hidden flex flex-col`}>
          <div className="p-6 flex-1 overflow-y-auto">
            <div className="mb-8">
              <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Pipeline Layers</h2>
              <div className="space-y-1">
                {Object.keys(PROJECT_FILES).map((key) => (
                  <button
                    key={key}
                    onClick={() => setActiveFile(key)}
                    className={`w-full text-left px-4 py-3 rounded-xl flex items-center gap-3 transition-all ${activeFile === key ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-sm' : 'text-slate-600 hover:bg-slate-50'}`}
                  >
                    <Code2 className={`w-4 h-4 ${activeFile === key ? 'text-indigo-600' : 'text-slate-400'}`} />
                    <span className="text-sm">{key}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-8">
              <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Architecture Flow</h2>
              <div className="space-y-4">
                {ARCHITECTURE_STEPS.map((step, idx) => (
                  <div key={step.id} className="relative">
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${step.bg}`}>
                        <step.icon className={`w-4 h-4 ${step.color}`} />
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-slate-800">{step.title}</h3>
                        <p className="text-xs text-slate-500 leading-relaxed">{step.desc}</p>
                      </div>
                    </div>
                    {idx < ARCHITECTURE_STEPS.length - 1 && (
                      <div className="absolute left-4 top-10 w-0.5 h-6 bg-slate-100" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          <div className="p-6 border-t border-slate-100 bg-slate-50/50">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                <span className="text-indigo-700 font-bold text-xs">TS</span>
              </div>
              <div>
                <p className="text-sm font-bold text-slate-800">Tanuj Nitesh</p>
                <p className="text-xs text-slate-500">Ex-Goldman Sachs • DE</p>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-5xl mx-auto">
            {/* Hero Section */}
            <div className="mb-12">
              <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full text-xs font-bold mb-6">
                <CheckCircle2 className="w-3 h-3" />
                Production Ready Pipeline
              </div>
              <h2 className="text-4xl font-extrabold text-slate-900 tracking-tight mb-4">
                End-to-End E-Commerce Data Pipeline
              </h2>
              <p className="text-lg text-slate-600 max-w-3xl leading-relaxed">
                A robust data engineering project showcasing a modern data stack. 
                Ingesting data from REST APIs and CSVs, processing with PySpark on AWS, 
                storing in Snowflake, and modeling with dbt.
              </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
              {[
                { label: 'Data Sources', value: 'API + CSV', icon: Cloud },
                { label: 'Processing', value: 'PySpark', icon: Terminal },
                { label: 'Warehouse', value: 'Snowflake', icon: Server },
                { label: 'Orchestration', value: 'Airflow', icon: Workflow },
              ].map((stat, i) => (
                <div key={i} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                  <stat.icon className="w-5 h-5 text-indigo-600 mb-3" />
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">{stat.label}</p>
                  <p className="text-lg font-bold text-slate-900">{stat.value}</p>
                </div>
              ))}
            </div>

            {/* Code Viewer Section */}
            <div className="bg-white rounded-3xl border border-slate-200 shadow-xl overflow-hidden mb-12">
              <div className="bg-[#1e1e1e] px-6 py-4 flex items-center justify-between border-b border-white/5">
                <div className="flex items-center gap-4">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500" />
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                  </div>
                  <div className="h-4 w-px bg-white/10 mx-2" />
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-slate-400" />
                    <span className="text-xs font-mono text-slate-300">{PROJECT_FILES[activeFile as keyof typeof PROJECT_FILES].path}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{PROJECT_FILES[activeFile as keyof typeof PROJECT_FILES].language}</span>
                  <button className="text-slate-400 hover:text-white transition-colors">
                    <Github className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="relative">
                <SyntaxHighlighter
                  language={PROJECT_FILES[activeFile as keyof typeof PROJECT_FILES].language}
                  style={atomDark}
                  customStyle={{
                    margin: 0,
                    padding: '2rem',
                    fontSize: '13px',
                    lineHeight: '1.6',
                    backgroundColor: '#1e1e1e',
                  }}
                  showLineNumbers={true}
                >
                  {PROJECT_FILES[activeFile as keyof typeof PROJECT_FILES].content}
                </SyntaxHighlighter>
              </div>
            </div>

            {/* Analytical Goals Section */}
            <div className="mb-12">
              <h3 className="text-2xl font-bold text-slate-900 mb-8 flex items-center gap-3">
                <BarChart3 className="text-indigo-600" />
                Analytical Output Goals
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[
                  { title: 'Revenue by Category', desc: 'Weekly trends analyzed via fact_orders to identify high-performing segments.' },
                  { title: 'Stockout Risk', desc: 'Predictive alerting by joining real-time inventory levels with sales velocity.' },
                  { title: 'Customer Lifetime Value', desc: 'Ranking customers by total historical spend to drive loyalty programs.' },
                  { title: 'Fulfillment Delay', desc: 'Monitoring the gap between order placement and shipping timestamps.' },
                ].map((goal, i) => (
                  <div key={i} className="group bg-white p-8 rounded-3xl border border-slate-200 hover:border-indigo-300 transition-all hover:shadow-lg">
                    <div className="w-12 h-12 bg-indigo-50 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-indigo-600 transition-colors">
                      <ChevronRight className="w-6 h-6 text-indigo-600 group-hover:text-white transition-colors" />
                    </div>
                    <h4 className="text-lg font-bold text-slate-900 mb-3">{goal.title}</h4>
                    <p className="text-slate-600 leading-relaxed">{goal.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Footer CTA */}
            <div className="bg-indigo-900 rounded-[2rem] p-12 text-center text-white relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-white rounded-full blur-[100px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-400 rounded-full blur-[100px]" />
              </div>
              <h3 className="text-3xl font-bold mb-4">Ready to build your next pipeline?</h3>
              <p className="text-indigo-200 mb-8 max-w-xl mx-auto">
                This project is open-source and ready for deployment. Follow the setup instructions in the README to get started.
              </p>
              <div className="flex items-center justify-center gap-4">
                <button className="bg-white text-indigo-900 px-8 py-4 rounded-2xl font-bold hover:bg-indigo-50 transition-all flex items-center gap-2">
                  Get Started
                  <ArrowRight className="w-5 h-5" />
                </button>
                <button className="bg-indigo-800 text-white px-8 py-4 rounded-2xl font-bold hover:bg-indigo-700 transition-all">
                  Contact Me
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
