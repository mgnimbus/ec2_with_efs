import base64
import gzip
import json


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        data = base64.b64decode(record['data'])
        decompressed_data = gzip.decompress(data).decode('utf-8')
        parsed_data = json.loads(decompressed_data)

        # Extract the message field from the log event
        message = parsed_data['logEvents'][0]['message']

        # Process the message field as desired
        processed_message = message.upper()

        # Replace the message field with the processed message
        parsed_data['logEvents'][0]['message'] = processed_message

        # Encode the modified JSON object and append it to the output
        processed_data_str = json.dumps(parsed_data)
        encoded_data = base64.b64encode(
            processed_data_str.encode('utf-8')).decode('utf-8')
        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': encoded_data
        }
        output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': output}
