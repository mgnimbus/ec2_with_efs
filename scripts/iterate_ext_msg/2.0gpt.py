import base64
import gzip
import json


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        data = json.loads(gzip.decompress(base64.b64decode(record['data'])))

        if data['messageType'] == 'DATA_MESSAGE':
            output_records = []
            for log_event in data['logEvents']:
                message = log_event['message']
                log_id = log_event['id']

                if not message.endswith('\n'):
                    message += '\n'

                dict1 = {'mount_status': message}
                output_records.append(json.dumps(dict1))

            output_record = {
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(','.join(output_records).encode('utf-8')).decode('utf-8')
            }
            output.append(output_record)

    return {'records': output}
