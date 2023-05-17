import base64
import gzip
import json
import re


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
            # Remove square brackets and their contents from the value
            value = re.sub(r'\[[^\]]*\]', '', value).strip()
            # Remove single quotes from the value
            value = value.strip("'")
            fields[key] = value

    # Add the timestamp to the dictionary
    fields['timestamp'] = timestamp.strip()

    # Convert the dictionary to a JSON string
    return json.dumps(fields)


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        print(record['recordId'])
        data = json.loads(gzip.decompress(base64.b64decode(record['data'])))

        if data['messageType'] == 'DATA_MESSAGE':

            for log_event in data['logEvents']:
                message = log_event['message']

                # Transform the payload to JSON format
                json_payload = transform_payload_to_json(message)
                print(json_payload)

                output_record = {
                    'recordId': record['recordId'],
                    'result': 'Ok',
                    'data': base64.b64encode(json_payload.encode('utf-8')).decode('utf-8')
                }
                output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': output}
