import boto3
import json
import os
import ssl
import urllib.request

PAGES_TO_DOWNLOAD = 25


def sendCloudFormationSuccess(event, context):
    """Sends a response to CloudFormation that the given operation completed.
    """

    try:
        request = urllib.request.Request(event["ResponseURL"], data=json.dumps({
            "Status": "SUCCESS",
            "PhysicalResourceId": context.log_stream_name,
            "StackId": event["StackId"],
            "RequestId": event["RequestId"],
            "LogicalResourceId": event["LogicalResourceId"],
        }).encode(), method="PUT")
        urllib.request.urlopen(request)
    except Exception:
        pass

def lambda_handler(event, context):
    """Handles the Lambda request.
    """

    # Ignore the request if it is from CloudFormation and it isn't a resource create.
    # This will happen when a resource is being deleted or updated.
    if "RequestType" in event.keys() and event["RequestType"] != "Create":
        sendCloudFormationSuccess(event, context)
        return {
            "statusCode": 200,
            "body": "",
            "isBase64Encoded": False,
        }

    # Create the SSL context.
    # For some reason, SSL errors occur despite the certificate being valid.
    sslContext = ssl.create_default_context()
    sslContext.check_hostname = False
    sslContext.verify_mode = ssl.CERT_NONE

    # Get the map ids to download.
    mapIds = []
    for i in range(0, PAGES_TO_DOWNLOAD):
        try:
            pageMaps = json.loads(urllib.request.urlopen("https://beatsaver.com/api/search/text/" + str(i) + "?sortOrder=Rating", context=sslContext).read().decode("utf8"))
            for mapData in pageMaps["docs"]:
                mapId = mapData["id"]
                if mapId not in mapIds:
                    mapIds.append(mapId)
        except Exception:
            pass

    # Download the maps.
    lambdaClient = boto3.client("lambda")
    downloadResponse = lambdaClient.invoke(
        FunctionName=os.environ["DownloadBeatSaverZipsLambda"],
        InvocationType="RequestResponse",
        Payload=json.dumps({
            "body": json.dumps(mapIds),
        }),
    )
    response = json.loads(downloadResponse["Payload"].read().decode("utf8"))

    # Respond to CloudFormation that the event completed.
    if "ResponseURL" in event.keys():
        sendCloudFormationSuccess(event, context)

    # Return the map response.
    return response
