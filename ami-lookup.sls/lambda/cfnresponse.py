import json
import requests

SUCCESS = "SUCCESS"
FAILED = "FAILED"


def send(event, context, responseStatus, responseData, physicalResourceId):  # noqa pylint: disable=C0103
    """Send response to CFN."""
    response_url = event['ResponseURL']

    print(response_url)

    response_body = {}
    response_body['Status'] = responseStatus
    response_body['Reason'] = ('See the details in CloudWatch Log Stream: ' +
                               context.log_stream_name)
    response_body['PhysicalResourceId'] = physicalResourceId or context.log_stream_name  # noqa
    response_body['StackId'] = event['StackId']
    response_body['RequestId'] = event['RequestId']
    response_body['LogicalResourceId'] = event['LogicalResourceId']
    response_body['Data'] = responseData

    json_response_body = json.dumps(response_body)

    print("Response body:\n" + json_response_body)

    headers = {
        'content-type': '',
        'content-length': str(len(json_response_body))
    }

    try:
        response = requests.put(response_url,
                                data=json_response_body,
                                headers=headers)
        print("Status code: " + response.reason)
    except Exception as e:  # pylint: disable=C0103,W0703
        print("send(..) failed executing requests.put(..): " + str(e))
