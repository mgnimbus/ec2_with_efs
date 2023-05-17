import base64
import gzip
import json


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        data = gzip.decompress(base64.b64decode(
            record['data'])).decode('utf-8')
        data = json.loads(data)

        if data['messageType'] == 'DATA_MESSAGE':
            output_records = [
                json.dumps({'mount_status': log_event['message']}) + '\n'
                for log_event in data['logEvents']
            ]

            output_record = {
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(''.join(output_records).encode('utf-8')).decode('utf-8')
            }
            output.append(output_record)

    return {'records': output}
