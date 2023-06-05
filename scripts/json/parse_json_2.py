import base64
import json
import gzip


def transformLogEvent(log_event):
    if isinstance(log_event, str):
        return {'message': log_event.rstrip('\n')}
    else:
        return log_event


def lambda_handler(event, context):
    processed_records = []

    for record in event['records']:
        data = json.loads(gzip.decompress(base64.b64decode(record['data'])))
        recId = record['recordId']
        result = {
            'recordId': recId
        }

        if data['messageType'] == 'CONTROL_MESSAGE':
            result['result'] = 'Dropped'
        elif data['messageType'] == 'DATA_MESSAGE':
            joinedJsonStr = ''.join(transformLogEvent(
                e)['message'] for e in data['logEvents'] if isinstance(e, str))
            dataBytes = joinedJsonStr.encode("utf-8")
            encodedData = base64.b64encode(dataBytes).decode('utf-8')
            result['data'] = encodedData
            result['result'] = 'Ok'
        else:
            result['result'] = 'ProcessingFailed'

        processed_records.append(result)

    print('Successfully processed {} records.'.format(len(event['records'])))

    response = {
        'records': processed_records,
        'result': 'Success'  # Add the 'result' field to the response
    }

    result = {
        'result': 'Success',  # Update the overall result based on the processing
        'records': processed_records
    }

    return response
