import base64
import gzip
import json


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        data = json.loads(gzip.decompress(base64.b64decode(record['data'])))

        if data['messageType'] == 'DATA_MESSAGE':
            combined_message = '\n'.join(
                [log_event['message'] for log_event in data['logEvents']])

            message_data = {
                'mount_status': combined_message
            }

            output_record = {
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(json.dumps(message_data).encode('utf-8')).decode('utf-8')
            }

            output.append(output_record)

    print(f"Successfully processed {len(event['records'])} records.")

    return {'records': output}
