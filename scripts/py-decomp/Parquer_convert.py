import json
import uuid
import os
import datetime
from datetime import datetime
import base64
import gzip
import sys
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3


class DataTransform(object):
    def __init__(self):
        pass

    def error_handler(func, exit_flag=False):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                print(f"INFO: {func.__name__} -> SUCCESSFUL")
                return result
            except Exception as e:
                print(f"ERROR: {func.__name__} -> UNSUCCESSFUL : {str(e)}")
                if exit_flag:
                    sys.exit(1)

        return wrapper

    @error_handler
    def flatten_dict(self, data, parent_key="", sep="_"):
        """Flatten data into a single dict"""
        items = []
        for key, value in data.items():
            new_key = parent_key + sep + key if parent_key else key
            if type(value) == dict:
                items.extend(self.flatten_dict(
                    value, new_key, sep=sep).items())
            else:
                items.append((new_key, value))
        return dict(items)

    @error_handler
    def dict_clean(self, items):
        result = {}
        for key, value in items.items():
            if value is None:
                value = "n/a"
            if value == "None":
                value = "n/a"
            if value == "null":
                value = "n/a"
            if len(str(value)) < 1:
                value = "n/a"
            result[key] = str(value)
        return result


def lambda_handler(event, context):
    data_transform = DataTransform()

    processed_messages = []
    for record in event['records']:
        data = base64.b64decode(record['data'])
        decompressed_data = gzip.decompress(data).decode('utf-8')
        parsed_data = json.loads(decompressed_data)
        print(str(parsed_data))
        clean_flatten_record = data_transform.dict_clean(
            data_transform.flatten_dict(parsed_data))
        processed_messages.append(clean_flatten_record)

    print("processed_messages")
    print(processed_messages)

    df = pd.DataFrame(data=processed_messages)
    print("df", df.head())

    # Convert the Pandas dataframe to an Arrow table
    table = pa.Table.from_pandas(df)

    # Write the Arrow table to a Parquet file in memory
    parquet_bytes = pa.BufferOutputStream()
    pq.write_table(table, parquet_bytes)

    # Upload the Parquet file to S3
    s3 = boto3.client('s3')

    dt = datetime.now()
    year = dt.year
    month = dt.month
    day = dt.day
    path = f"raw/table_name=sample/year={year}/month={month}/day={day}/{uuid.uuid4().__str__()}.parquet"
    print("type", type(parquet_bytes.getvalue()))

    s3.put_object(
        Bucket="temp-conv-bucky",
        Key=path,
        Body=parquet_bytes.getvalue().to_pybytes()
    )

    return {
        'statusCode': 200,
        'body': 'Parquet file uploaded to S3'
    }
