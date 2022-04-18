import boto3
import json
import os
import ssl
import urllib.request
import uuid

MAX_ENTRIES_FOR_BATCH = 10


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
        }

    # Create the SSL context.
    # For some reason, SSL errors occur despite the certificate being valid.
    sslContext = ssl.create_default_context()
    sslContext.check_hostname = False
    sslContext.verify_mode = ssl.CERT_NONE

    # Get the map ids to download.
    mapIds = []
    for i in range(0, int(os.environ["InitialDownloadPages"])):
        try:
            pageMaps = json.loads(urllib.request.urlopen("https://beatsaver.com/api/search/text/" + str(i) + "?sortOrder=Rating", context=sslContext).read().decode("utf8"))
            for mapData in pageMaps["docs"]:
                mapId = mapData["id"]
                if mapId not in mapIds:
                    mapIds.append(mapId)
        except Exception:
            pass

    # Add the maps to the queue to download.
    downloadEntries = []
    for mapId in mapIds:
        downloadEntries.append({
            "Id": str(uuid.uuid4()),
            "MessageBody": mapId,
        })
    sqsClient = boto3.client("sqs")
    for i in range(0, len(mapIds), MAX_ENTRIES_FOR_BATCH):
        sqsClient.send_message_batch(QueueUrl=os.environ["BeatSaverMapDownloadQueue"], Entries=downloadEntries[i:i + MAX_ENTRIES_FOR_BATCH])

    # Respond to CloudFormation that the event completed.
    if "ResponseURL" in event.keys():
        sendCloudFormationSuccess(event, context)

    # Return the map response.
    return {
        "statusCode": 200,
        "body": "Maps added to queue.",
    }
