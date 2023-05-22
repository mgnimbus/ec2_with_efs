import base64
import gzip
import json
import re


def transformLogEvent(log_event):
    return log_event['message'] + '\n'


def lambda_handler(event, context):
    output = {}
    messages = {}

    for record in event['records']:
        data = json.loads(gzip.decompress(base64.b64decode(record['data'])))

        if data['messageType'] == 'DATA_MESSAGE':
            if record['recordId'] not in messages:
                messages[record['recordId']] = []

            for log_event in data['logEvents']:
                messages[record['recordId']].append(
                    transformLogEvent(log_event))

    for record_id, message_list in messages.items():
        combined_message = ''.join(message_list)

        match = re.search(r"(\w{3} \w{3} \d{2} \d{2}:\d{2}:\d{2} \d{4} [\+\-]\d{2}:\d{2})\n"
                          r"LENGTH : '(\d+)'\n"
                          r"ACTION :\[\d+\] '([^']+)'\n"
                          r"DATABASE USER:\[\d+\] '(.*)'\n"
                          r"PRIVILEGE :\[\d+\] '(.*)'\n"
                          r"CLIENT USER:\[\d+\] '(.*)'\n"
                          r"CLIENT TERMINAL:\[\d+\] '(.*)'\n"
                          r"STATUS:\[\d+\] '(.*)'\n"
                          r"DBID:\[\d+\] '(\d+)'\n"
                          r"SESSIONID:\[\d+\] '(\d+)'\n"
                          r"USERHOST:\[\d+\] '(.*)'\n"
                          r"CLIENT ADDRESS:\[\d+\] '(.*)'\n"
                          r"ACTION NUMBER:\[\d+\] '(\d+)'", combined_message)

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

            output_record = {
                'recordId': record_id,
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
            output[record_id] = output_record
            print("Output record:", output_record)
        else:
            print("No match found for the messages with record ID:", record_id)
            # Add the unmatched record to the output
            output[record_id] = {'recordId': record_id}

    print('Successfully processed {} records.'.format(len(event['records'])))

    output_records = []
    for record_id, record_data in output.items():
        json_payload = json.dumps(record_data)
        output_record = {
            'recordId': record_id,
            'result': 'Ok',
            'data': base64.b64encode(json_payload.encode('utf-8')).decode('utf-8')
        }
        output_records.append(output_record)

    return {'records': output_records}
