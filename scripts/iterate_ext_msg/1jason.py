import base64
import gzip
import json


def lambda_handler(event, context):
    output = []
    output_records = []
    json_string = ""

    for record in event['records']:
        data = json.loads(gzip.decompress(base64.b64decode(record['data'])))
        if data['messageType'] == 'DATA_MESSAGE':
            for log_event in data['logEvents']:

                print(log_event)

                message = log_event['message']
                log_id = log_event['id']

                if not message.endswith('\n'):
                    message += '\n'

                dict1 = {}
                dict1["message"] = message

                output_records.append(dict1)
            for item in output_records:
                my_json_row = json.dumps(item)
                json_string += my_json_row

                print('json_string=', json_string)

            output_record = {
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(
                    json_string.encode('utf-8')).decode('utf-8')
            }
            output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))
    print(json.dumps(output))
    return {'records': output}
