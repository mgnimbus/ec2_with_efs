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
        fields = payload.split('\n')
        json_payload = {
            'timestamp': fields[0],
            'length': int(fields[1].split("LENGTH : '")[1].split("'")[0]),
            'action': fields[2].split("ACTION :[")[1].split("] '")[1].split("'")[0],
            'database_user': payload.split("DATABASE USER:[1] '")[1].split("'")[0],
            'privilege': fields[4].split("PRIVILEGE :[")[1].split("] '")[1].split("'")[0],
            # 'client_user': fields[5].split("CLIENT USER :[")[1].split("] '")[1].split("'")[0],
            # 'client_terminal': fields[6].split("CLIENT TERMINAL :[")[1].split("] '")[1].split("'")[0],
            'status': payload.split("STATUS:[1] '")[1].split("'")[0],
            'dbid': int(payload.split("DBID:[10] '")[1].split("'")[0]),
            # 'sessionid': int(payload.split("SESSIONID:[10] '")[1].split("'")[0]),
            # 'sessionid': fields[9].split("SESSIONID :[")[1].split("] '")[1],
            # 'userhost': fields[10].split("USERHOST :[")[1].split("] '")[1].split("'")[0],
            'userhost': payload.split("USERHOST:[13] '")[1].split("'")[0],
            'client_address': payload.split("CLIENT ADDRESS:[0] '")[1].split("'")[0].strip(),
            # 'action_number': fields[12].split("ACTION NUMBER :[")[1].split("] '")[1].split("'")[0],
        }
        print(json.dumps(json_payload))

        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(json.dumps(json_payload).encode('utf-8')).decode('utf-8')
        }
        output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))
