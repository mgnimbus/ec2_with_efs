import base64
import json
import gzip


def transformLogEvent(log_event):
    return log_event['message'] + '\n'


def processRecords(records):
    processed_records = []
    for record in records:
        data = loadJsonGzipBase64(record['data'])
        recId = record['recordId']
        result = {}

        if data['messageType'] == 'CONTROL_MESSAGE':
            result['result'] = 'Dropped'

        elif data['messageType'] == 'DATA_MESSAGE':
            joinedJsonStr = ''.join(transformLogEvent(e)
                                    for e in data['logEvents'])
            result['data'] = base64.b64encode(
                joinedJsonStr.encode('utf-8')).decode('utf-8')
            result['result'] = 'Ok'
        else:
            result['result'] = 'ProcessingFailed'

        result['recordId'] = recId
        processed_records.append(result)

    return processed_records


def loadJsonGzipBase64(base64Data):
    return json.loads(gzip.decompress(base64.b64decode(base64Data)))


def lambda_handler(event, context):
    records = processRecords(event['records'])
    print('Successfully processed {} records.'.format(len(records)))
    return {'records': records}


'''
{
  "records": [
    {
      "recordId": "49578734086442259037497492980620233840400173390482112514000000",
      "data": "H4sIAAAAAAAA/3VRS2/bMAz+KwPP1irrSesWtFlRYL3U2WkuCtmiMgPxY5bTYgjy3wc7S9cddhEg8nuRPEFHKfk97X6NBA7uNrvNy+O2LDf3W8hgeOtpAgdSoDDIEa1EyOAw7O+n4TiCg9Snm2Ni5NPM8puPuJsdpbns09dhv2/7/YVWzhP5DhwU1nAbtWYFbwJTGiPzyuZMad0gYZGL6CGDdKxTM7Xj3A79l/Yw05TAfYfYTvRjSPRyGPZxLcPzqr99pX5eICdowxLcaotWSFRoRW4kl0YpaQrOc4WaF8pKi8YoywspdcFzFMrkSkEGc9tRmn03gssNao4otDHaZNeVgYNTBf0wt7Ft/JKwAneqru3HO10euwpcBSp4bHiteOCx4JF7TWij8rnkUYYGK8jeaQ9hpdRa5bVCZMJzzXTNJUOsFSM0QnFRxxjylTYPY9tspn5l+al3/i251Cf3fhX38Sru36tcJK6TrhqCC8m4ZsJ84ui4dBo/C6srOGcVBDq0rzT9ukx6/f3JLEOjm0ZLpkhEpouCMy+Js4LXhVA8l4HL1TBQmtv+urK/sQ++q4P/X/J47JuF4gI1QzdOlNKqNk7DaxtoeqI0Dn2iVfJUVRVc9J7o55HS/BCWklseFUxOhJwJRYopWSDzAQXLpZHe5tFaGxfc+ZL2jQ6HXdvRY6rASZNVkGY/H9PtEBYzwcX5vbaal99ub7dlWcEZzs/n38AINRRkAwAA",
      "approximateArrivalTimestamp": 1510254469499
    },
    {
      "recordId": "49578734086442259037497492980621442766219788363254202370000000",
      "data": "H4sIAAAAAAAA/3VRy27bMBD8lWLPYsOHKD5uRuIGAZpL5J6qIKDIpStAr4pSgsLwvxeS6zQ9FAQIcLgzO7N7gg5Tckc8/BoRLNztDruXx31Z7u73kMHw1uMEFgTXvNBUayU0ZNAOx/tpWEawkPp0sySCLs2E3Xysuzlgmss+fR2Ox6Y/XmjlPKHrwIILMhaF4sSjFyT3ShDNRUEQldaFE54yhAzSUic/NePcDP2Xpp1xSmC/Q2wm/DEkfGmHY9xgeN7096/Yz2vJCZqwGldSacV5zkRBmVJ5QYUwUlFDc5FLraRgRnMlZG4UVYZyneeGryHnpsM0u24EywotqdbMcEFFdh0ZWDhV0A9zExvvVocV2FN1/X68k+XSVWArEN5rRYMrcq63E7V23kVOY/AoTQXZO+0hbBTPXeFNDEQZ54k0TBMXakaMZIpRabh2eqPNw9j43dRvLDf11r0lm/pk37diP27F/ruVi8Q16abBKReESsKLT1RbKixln7mWFZyzCgK2zStOvy5Jr68/nhXnIcTAiCqwJpJiJLUTBdFC1Cwy9IxdogZMc9NfR/bXduu6Orj/OY9L71eKDeiHbpwwpU1tnIbXJuD0hGkc+oSb5KmqKrjoPeHPBdP8EFbIrpfneYg81sRFr0leG09cnTvCFGqpKGdCmrXufHH7hm17aDp8TBVYRk1WQZrdvKTbIazdOOXnd2zrXn67vd2XZQVnOD+ffwPG3X/HZQMAAA==",
      "approximateArrivalTimestamp": 1510254473773
    },
    {
      "recordId": "49578734086442259037497492980622651692039402992428908546000000",
      "data": "H4sIAAAAAAAA/3WRTW/bMAyG/8rAs7XSkmXRugVtVhRYL3V2motClujMQPwxy2kxBPnvg52l6w67CBDJ9+VD8gQdx+j2vPs1Mli42+w2L4/bstzcbyGB4a3nCSwoSTInJDKKIIHDsL+fhuMIFmIfb45RsIuzSG8+1t3sOM5lH78O+33b7y+ycp7YdWCBMLCUWS3YpE5kMjSi1qkREqmoyaQmZQMJxGMd/dSOczv0X9rDzFME+x2aduIfQ+SXw7Bv1jA8r/7bV+7npeQEbVjAjTZkpEKdZlIrIpS5Noh5qrMCCVVWSEpJKcqlVjI32qg00zkkMLcdx9l1I9g0J41EUmKBWXJdGVg4VdAPc9u03i2EFdhTdU0/3uny2FVgK8iCI491hgGbAht0msk0mUsVNip4qiB5lz2EVVJQnteojNBFgUI7koJST4J9CEoVuWKNq2wextZvpn5Vuam37i3a2Ef7fhX78Sr236tcLK6Trh4SpRKohcw/IVlUNqXPOeoKzkkFgQ/tK0+/LpNef3+YmwJR5pwKltIJnUsvnG9SYRzWRNLLWl6YA8e57a8r+4t9cF0d3P/Im2PvF4kN7IdunDjG1W2chtc28PTEcRz6yKvlqaoquPg98c8jx/khLCG7PFSHLHDtRfCSRMaNEoV3XuQ51syGZI1yqTtfaN/4cNi1HT/GCqxWSQVxdvMx3g5haSZRnt9ja/Py2+3ttiwrOMP5+fwbC+2STmQDAAA=",
      "approximateArrivalTimestamp": 1510254474027
    }
  ],
  "region": "us-east-1",
  "deliveryStreamArn": "arn:aws:firehose:us-east-1:123456789012:deliverystream/copy-cwl-lambda-invoke-input-151025436553-Firehose-8KILJ01Q5OBN",
  "invocationId": "a7234216-12b6-4bc0-96d7-82606c0e80cf"
}

[
  {
    "Name": "notification",
    "Type": "struct<messageMD5Sum:string,messageId:string,topicArn:string,timestamp:string>"
  },
  {
    "Name": "delivery",
    "Type": "struct<deliveryId:string,destination:string,providerResponse:string,dwellTimeMs:int,statusCode:int>"
  },
  {
    "Name": "status",
    "Type": "string"
  }
]

'''
