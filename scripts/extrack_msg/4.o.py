import base64
import gzip
import json


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        data = json.loads(gzip.decompress(base64.b64decode(record['data'])))

        if data['messageType'] == 'DATA_MESSAGE':
            processed_logs = []

            for log_event in data['logEvents']:
                message = log_event['message']

                processed_data = {
                    'mount_status': message
                }

                processed_data_str = json.dumps(processed_data)
                processed_logs.append(processed_data_str)

            # Join processed logs with new lines
            log_bundle = '\n'.join(processed_logs)

            output_record = {
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(log_bundle.encode('utf-8')).decode('utf-8')
            }

            output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': output}
