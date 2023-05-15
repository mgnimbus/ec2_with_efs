import base64
import gzip
import json


def lambda_handler(event, context):
    output = []
    for record in event['records']:
        print(record['recordId'])
        # Decode and decompress the log event data
        data = base64.b64decode(record['data'])
        decompressed_data = gzip.decompress(data).decode('utf-8')

        # Parse the JSON data and extract the message field
        parsed_data = json.loads(decompressed_data)

        # Extract the message field from the log event
        payload = parsed_data['logEvents'][0]['message']
        print(payload)

        # Convert payload to JSON using the lambda function
        json_payload = json.dumps({
            'timestamp': ' '.join(payload.split(' ')[0:5]),
            'length': int(payload.split("LENGTH : '")[1].split("'")[0]),
            'action': payload.split("ACTION :[7] '")[1].split("'")[0],
            'database_user': payload.split("DATABASE USER:[1] '")[1].split("'")[0],
            'privilege': payload.split("PRIVILEGE :[6] '")[1].split("'")[0],
            'client_user': payload.split("CLIENT USER:[5] '")[1].split("'")[0],
            'client_terminal': payload.split("CLIENT TERMINAL:[0] '")[1].split("'")[0].strip(),
            'status': payload.split("STATUS:[1] '")[1].split("'")[0],
            'dbid': int(payload.split("DBID:[10] '")[1].split("'")[0]),
            'sessionid': int(payload.split("SESSIONID:[10] '")[1].split("'")[0]),
            'userhost': payload.split("USERHOST:[13] '")[1].split("'")[0],
            'client_address': payload.split("CLIENT ADDRESS:[0] '")[1].split("'")[0].strip(),
            'action_number': int(payload.split("ACTION NUMBER:[3] '")[1].split("'")[0])
        })
        print(json_payload)

        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(json_payload.encode('utf-8')).decode('utf-8')
        }
        output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': output}
