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

BUCKET_NAME = os.environ['bucket_name']
BUCKET_PREFIX = os.environ['bucket_prefix']


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

    # Convert the Arrow table to a GZip compressed stream
    compressed_stream = pa.BufferOutputStream()
    with gzip.GzipFile(fileobj=compressed_stream, mode='w') as f:
        pq.write_table(table, f)

    # Upload the Parquet file to S3
    s3 = boto3.client('s3')

    dt = datetime.now()
    year = dt.year
    month = dt.month
    day = dt.day
    hour = dt.hour
    path = f"{BUCKET_PREFIX}/year={year}/month={month}/day={day}/hour={hour}/{uuid.uuid4().__str__()}-gzip.parquet"
    print("type", type(compressed_stream.getvalue()))

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=path,
        Body=compressed_stream.getvalue().to_pybytes()
    )

    # Return the processed records as a list
    processed_records = [{"recordId": record["recordId"], "data": base64.b64encode(json.dumps(
        record).encode('utf-8')).decode('utf-8'), "result": "Ok"} for record in event['records']]

    # Return the processed records in the required format
    return {"records": processed_records}
