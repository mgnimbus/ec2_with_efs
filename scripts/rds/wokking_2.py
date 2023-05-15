import base64
import gzip
import json


def transform_payload_to_json(payload):
    # Split the payload into lines
    lines = payload.split('\n')

    # Extract the timestamp from the first line
    timestamp = lines[0]

    # Extract the fields from each line and create a dictionary
    fields = {}
    for line in lines[1:]:
        if ':' in line:
            key, value = line.split(':', 1)
            # Lower the key and replace spaces with underscores
            key = key.strip().lower().replace(' ', '_')
            fields[key] = value.strip()

    # Add the timestamp to the dictionary
    fields['timestamp'] = timestamp.strip()

    # Convert the dictionary to a JSON string
    return json.dumps(fields)


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        print(record['recordId'])
        data = base64.b64decode(record['data'])
        decompressed_data = gzip.decompress(data).decode('utf-8')
        parsed_data = json.loads(decompressed_data)

        # Extract the message field from the log event
        payload = parsed_data['logEvents'][0]['message']
        print(payload)

        # Transform the payload to JSON format
        json_payload = transform_payload_to_json(payload)
        print(json_payload)

        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(json_payload.encode('utf-8')).decode('utf-8')
        }
        output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': output}
