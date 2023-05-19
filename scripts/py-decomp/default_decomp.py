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


def createReingestionRecord(isSas, originalRecord, data=None):
    if data is None:
        data = base64.b64decode(originalRecord['data'])
    r = {'Data': data}
    if isSas:
        r['PartitionKey'] = originalRecord['kinesisRecordMetadata']['partitionKey']
    return r


def loadJsonGzipBase64(base64Data):
    return json.loads(gzip.decompress(base64.b64decode(base64Data)))


def lambda_handler(event, context):
    isSas = 'sourceKinesisStreamArn' in event
    streamARN = event['sourceKinesisStreamArn'] if isSas else event['deliveryStreamArn']
    region = streamARN.split(':')[3]
    streamName = streamARN.split('/')[1]
    records = list(processRecords(event['records']))
    projectedSize = 0
    recordListsToReingest = []

    for idx, rec in enumerate(records):
        originalRecord = event['records'][idx]

        if rec['result'] != 'Ok':
            continue

    print('%d input records, %d returned as Ok or ProcessingFailed, %d split and re-ingested, %d re-ingested as-is' % (
        len(event['records']),
        len([r for r in records if r['result'] != 'Dropped']),
        len([l for l in recordListsToReingest if len(l) > 1]),
        len([l for l in recordListsToReingest if len(l) == 1])))

    return {'records': records}
