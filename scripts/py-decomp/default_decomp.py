import base64
import json
import gzip


def transformLogEvent(log_event):
    return log_event['message'] + '\n'


def processRecords(records):
    for r in records:
        data = loadJsonGzipBase64(r['data'])
        recId = r['recordId']
        if data['messageType'] == 'CONTROL_MESSAGE':
            yield {
                'result': 'Dropped',
                'recordId': recId
            }
        elif data['messageType'] == 'DATA_MESSAGE':
            joinedData = ''.join([transformLogEvent(e)
                                 for e in data['logEvents']])
            dataBytes = joinedData.encode("utf-8")
            encodedData = base64.b64encode(dataBytes).decode('utf-8')
            yield {
                'data': encodedData,
                'result': 'Ok',
                'recordId': recId
            }
        else:
            yield {
                'result': 'ProcessingFailed',
                'recordId': recId
            }


def loadJsonGzipBase64(base64Data):
    return json.loads(gzip.decompress(base64.b64decode(base64Data)))


def lambda_handler(event, context):
    records = list(processRecords(event['records']))

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': records}
