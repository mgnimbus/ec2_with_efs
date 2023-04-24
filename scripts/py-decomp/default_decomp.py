# Copyright 2014, Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#  http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

"""
For processing data sent to Firehose by Cloudwatch Logs subscription filters.

Cloudwatch Logs sends to Firehose records that look like this:

{
  "messageType": "DATA_MESSAGE",
  "owner": "123456789012",
  "logGroup": "log_group_name",
  "logStream": "log_stream_name",
  "subscriptionFilters": [
    "subscription_filter_name"
  ],
  "logEvents": [
    {
      "id": "01234567890123456789012345678901234567890123456789012345",
      "timestamp": 1510109208016,
      "message": "log message 1"
    },
    {
      "id": "01234567890123456789012345678901234567890123456789012345",
      "timestamp": 1510109208017,
      "message": "log message 2"
    }
    ...
  ]
}

The data is additionally compressed with GZIP.

The code below will:

1) Gunzip the data
2) Parse the json
3) Set the result to ProcessingFailed for any record whose messageType is not DATA_MESSAGE, thus redirecting them to the
   processing error output. Such records do not contain any log events. You can modify the code to set the result to
   Dropped instead to get rid of these records completely.
4) For records whose messageType is DATA_MESSAGE, extract the individual log events from the logEvents field, and pass
   each one to the transformLogEvent method. You can modify the transformLogEvent method to perform custom
   transformations on the log events.
5) Concatenate the result from (4) together and set the result as the data of the record returned to Firehose. Note that
   this step will not add any delimiters. Delimiters should be appended by the logic within the transformLogEvent
   method.
6) Any individual record exceeding 6,000,000 bytes in size after decompression, processing and base64-encoding is marked
   as Dropped, and the original record is split into two and re-ingested back into Firehose or Kinesis. The re-ingested
   records should be about half the size compared to the original, and should fit within the size limit the second time
   round.
7) When the total data size (i.e. the sum over multiple records) after decompression, processing and base64-encoding
   exceeds 6,000,000 bytes, any additional records are re-ingested back into Firehose or Kinesis.
8) The retry count for intermittent failures during re-ingestion is set 20 attempts. If you wish to retry fewer number
   of times for intermittent failures you can lower this value.
"""

import base64
import json
import gzip
import boto3


def transformLogEvent(log_event):
    """Transform each log event.

    The default implementation below just extracts the message and appends a newline to it.

    Args:
    log_event (dict): The original log event. Structure is {"id": str, "timestamp": long, "message": str}

    Returns:
    str: The transformed log event.
    """
    return log_event['message'] + '\n'


def processRecords(records):
    for r in records:
        data = loadJsonGzipBase64(r['data'])
        recId = r['recordId']
        # CONTROL_MESSAGE are sent by CWL to check if the subscription is reachable.
        # They do not contain actual data.
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


def splitCWLRecord(cwlRecord):
    """
    Splits one CWL record into two, each containing half the log events.
    Serializes and compreses the data before returning. That data can then be
    re-ingested into the stream, and it'll appear as though they came from CWL
    directly.
    """
    logEvents = cwlRecord['logEvents']
    mid = len(logEvents) // 2
    rec1 = {k: v for k, v in cwlRecord.items()}
    rec1['logEvents'] = logEvents[:mid]
    rec2 = {k: v for k, v in cwlRecord.items()}
    rec2['logEvents'] = logEvents[mid:]
    return [gzip.compress(json.dumps(r).encode('utf-8')) for r in [rec1, rec2]]


def putRecordsToFirehoseStream(streamName, records, client, attemptsMade, maxAttempts):
    failedRecords = []
    codes = []
    errMsg = ''
    # if put_record_batch throws for whatever reason, response['xx'] will error out, adding a check for a valid
    # response will prevent this
    response = None
    try:
        response = client.put_record_batch(
            DeliveryStreamName=streamName, Records=records)
    except Exception as e:
        failedRecords = records
        errMsg = str(e)

    # if there are no failedRecords (put_record_batch succeeded), iterate over the response to gather results
    if not failedRecords and response and response['FailedPutCount'] > 0:
        for idx, res in enumerate(response['RequestResponses']):
            # (if the result does not have a key 'ErrorCode' OR if it does and is empty) => we do not need to re-ingest
            if not res.get('ErrorCode'):
                continue

            codes.append(res['ErrorCode'])
            failedRecords.append(records[idx])

        errMsg = 'Individual error codes: ' + ','.join(codes)

    if failedRecords:
        if attemptsMade + 1 < maxAttempts:
            print(
                'Some records failed while calling PutRecordBatch to Firehose stream, retrying. %s' % (errMsg))
            putRecordsToFirehoseStream(
                streamName, failedRecords, client, attemptsMade + 1, maxAttempts)
        else:
            raise RuntimeError('Could not put records after %s attempts. %s' % (
                str(maxAttempts), errMsg))


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
