import base64
import json
import gzip


def transformLogEvent(log_event):
    return log_event['message'] + '\n'


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
            joinedJsonStr = ''.join(transformLogEvent(e)
                                    for e in data['logEvents'])
            dataBytes = joinedJsonStr.encode("utf-8")
            encodedData = base64.b64encode(dataBytes).decode('utf-8')
            result['data'] = encodedData
            result['result'] = 'Ok'
        else:
            result['result'] = 'ProcessingFailed'

        processed_records.append(result)

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': processed_records}
