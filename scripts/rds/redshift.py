import base64
import gzip
import json
import re


def lambda_handler(event, context):
    print("Received event:", event)
    output = []

    for record in event['records']:
        data = json.loads(gzip.decompress(base64.b64decode(record['data'])))
        print("Received record:", data)

        if data['messageType'] == 'DATA_MESSAGE':
            output_records = []
            for log_event in data['logEvents']:
                message = log_event['message']

                if message.endswith('\n'):
                    message = message.replace("\n", "")

                p = re.search(
                    r"(\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\dz) UTC \[ db=(\w+) user=(\w+) p userid=(\d+) xid=(\d+) \]' LOG: (.*)",
                    message)

                if p is None:
                    print("EVENT DIDN'T MATCH REGEX:", log_event)
                    continue

                dict1 = {
                    "recordtime": p.group(1),
                    "db": p.group(2),
                    "user": p.group(3),
                    "pid": p.group(4),
                    "userid": p.group(5),
                    "xid": p.group(6),
                    "query": p.group(7)
                }

                output_records.append(dict1)

            json_string = "\n".join(json.dumps(item)
                                    for item in output_records)
            output_record = {
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
            }
            output.append(output_record)

    print('Successfully returned event')
    return {'records': output}
