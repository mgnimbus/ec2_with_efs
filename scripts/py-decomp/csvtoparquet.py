import base64
import boto3
import io
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def lambda_handler(event, context):
    # Initialize the S3 client
    s3_client = boto3.client('s3')
    input_bucket = 'temp-conv-bucky'
    input_key = 'test-ec2-logs-2-2023-04-16-10-52-41-ec43f2ae-6c7b-49b9-aa30-da8e31ccb4ae'

    # Create an empty Pandas DataFrame to hold the data
    df = pd.DataFrame()

    # Load the file from S3 and parse it with Pandas
    file_object = s3_client.get_object(Bucket=input_bucket, Key=input_key)
    file_body = file_object['Body'].read().decode('utf-8')
    df = pd.read_csv(io.StringIO(file_body), header=None)

    # Convert the DataFrame to a PyArrow Table
    table = pa.Table.from_pandas(df)

    # Write the PyArrow Table to Parquet format and upload to S3
    pq.write_table(table, 's3://ec2-parquet-logs/parquet-ec2/test.parquet')
