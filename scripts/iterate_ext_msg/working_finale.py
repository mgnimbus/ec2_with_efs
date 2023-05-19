import base64
import gzip
import json


def transformLogEvent(log_event):
    return log_event['message'] + '\n'


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        data = json.loads(gzip.decompress(base64.b64decode(record['data'])))

        if data['messageType'] == 'DATA_MESSAGE':
            combined_json_str = ""
            for log_event in data['logEvents']:
                combined_json_str += transformLogEvent(log_event)

            message_data = {
                'mount_status': combined_json_str
            }

            processed_json_str = json.dumps(message_data)

            output_record = {
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(processed_json_str.encode('utf-8')).decode('utf-8')
            }

            output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': output}
