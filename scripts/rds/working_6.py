import base64
import gzip
import json
import re


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        print(record['recordId'])
        data = json.loads(gzip.decompress(base64.b64decode(record['data'])))

        if data['messageType'] == 'DATA_MESSAGE':
            for log_event in data['logEvents']:
                message = log_event['message']
                print("Message:", message)

                # Extract relevant information from the message
                pattern = r"(\w{3} \w{3} \d{2} \d{2}:\d{2}:\d{2} \d{4} \+\d{2}:\d{2})\n" \
                          r"LENGTH : '(\d+)'\n" \
                          r"ACTION :.*\n([\s\S]*?)" \
                          r"DATABASE USER:\[\d+\] '(.*)'\n" \
                          r"PRIVILEGE :\[\d+\] '(.*)'\n" \
                          r"CLIENT USER:\[\d+\] '(.*)'\n" \
                          r"CLIENT TERMINAL:\[\d+\] '(.*)'\n" \
                          r"STATUS:\[\d+\] '(.*)'\n" \
                          r"DBID:\[\d+\] '(\d+)'\n" \
                          r"SESSIONID:\[\d+\] '(\d+)'\n" \
                          r"USERHOST:\[\d+\] '(.*)'\n" \
                          r"CLIENT ADDRESS:\[\d+\] '(.*)'\n" \
                          r"ACTION NUMBER:\[\d+\] '(\d+)'"
                match = re.search(pattern, message)
                if match:
                    timestamp = match.group(1)
                    length = int(match.group(2))
                    action = match.group(3)
                    database_user = match.group(4)
                    privilege = match.group(5)
                    client_user = match.group(6)
                    client_terminal = match.group(7)
                    status = match.group(8)
                    dbid = int(match.group(9))
                    sessionid = int(match.group(10))
                    userhost = match.group(11)
                    client_address = match.group(12)
                    action_number = int(match.group(13))

                    # Create the output record
                    output_record = {
                        'recordId': record['recordId'],  # Add the recordId key
                        'timestamp': timestamp,
                        'length': length,
                        'action': action,
                        'database_user': database_user,
                        'privilege': privilege,
                        'client_user': client_user,
                        'client_terminal': client_terminal,
                        'status': status,
                        'dbid': dbid,
                        'sessionid': sessionid,
                        'userhost': userhost,
                        'client_address': client_address,
                        'action_number': action_number
                    }
                    output.append(output_record)
                    print("Output record:", output_record)
                else:
                    print("No match found for the message:", message)

    print('Successfully processed {} records.'.format(len(event['records'])))

    # Prepare the output for return
    output_records = []
    for record in output:
        json_payload = json.dumps(record)
        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(json_payload.encode('utf-8')).decode('utf-8')
        }
        output_records.append(output_record)

    return {'records': output_records}
