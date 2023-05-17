import base64
import gzip
import json


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        data = json.loads(gzip.decompress(base64.b64decode(record['data'])))

        if data['messageType'] == 'DATA_MESSAGE':
            processed_data = []

            for log_event in data['logEvents']:
                message = log_event['message']

                message_data = {
                    'mount_status': message
                }

                processed_json_str = json.dumps(message_data)
                processed_data.append(processed_json_str)

            # Join processed logs with new lines
            processed_logs = '\n'.join(processed_data)

            output_record = {
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(processed_logs.encode('utf-8')).decode('utf-8')
            }

            output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': output}
