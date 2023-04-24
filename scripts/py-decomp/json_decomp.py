import base64
import gzip
import json


def lambda_handler(event, context):
    print(event)
    print(context)
    for record in event['records']:
        data = base64.b64decode(record['data'])
        decompressed_data = gzip.decompress(data).decode('utf-8')
        parsed_data = json.loads(decompressed_data)
        print(str(parsed_data))
        processed_data_str = json.dumps(parsed_data)
        encoded_data = base64.b64encode(
            processed_data_str.encode('utf-8')).decode('utf-8')
        record['data'] = encoded_data
        record['result'] = 'OK'
    return {'records': event['records']}
