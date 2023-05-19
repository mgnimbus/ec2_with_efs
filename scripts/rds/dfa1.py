import base64
import gzip
import json
import re


def transform_payload_to_json(payload):
    # Split the payload into lines
    lines = payload.split('\n')
    timestamp = lines[0]

    # Initialize variables
    fields = {}
    current_key = None
    current_value = ""

    # Process each line in the payload
    for line in lines[1:]:
        if line.startswith(" "):
            # Continuation of a multi-line value
            current_value += line.strip()
        else:
            # New key-value pair
            if current_key:
                # Save the previous key-value pair
                fields[current_key] = current_value.strip()

            # Extract the new key and value
            key, value = line.split(':', 1)
            current_key = key.strip().lower().replace(' ', '_')
            current_value = re.sub(r'\[[^\]]*\]', '', current_value).strip()
            current_value = current_value.strip("'")

    fields['timestamp'] = timestamp.strip()
    # Add the last key-value pair
    if current_key:
        fields[current_key] = current_value.strip()

    # Convert the dictionary to a JSON string
    return json.dumps(fields)


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        print(record['recordId'])
        data = base64.b64decode(record['data'])
        decompressed_data = gzip.decompress(data).decode('utf-8')
        parsed_data = json.loads(decompressed_data)

        log_events = parsed_data['logEvents']

        # Process each log event
        for log_event in log_events:
            # Extract the message field from the log event
            payload = log_event['message']
            # print(payload)

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
