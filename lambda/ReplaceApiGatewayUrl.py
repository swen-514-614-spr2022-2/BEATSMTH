import boto3
import json
import os
import urllib.request

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

    # Read the index.html page file.
    s3Client = boto3.client("s3")
    indexHtmlFile = s3Client.get_object(
        Bucket=os.environ["BeatsmthFilesStorageBucketName"],
        Key="index.html",
    )["Body"].read().decode("UTF8")

    # Replace the URL and replace the file.
    indexHtmlFile = indexHtmlFile.replace("{BEATSMTH_API_GATEWAY_URL}", os.environ["ApiGatewayUrl"])
    s3Client.put_object(
        Body=indexHtmlFile.encode(),
        Bucket=os.environ["BeatsmthFilesStorageBucketName"],
        Key="index.html",
        ContentType="text/html",
    )

    # Respond to CloudFormation that the event completed.
    if "ResponseURL" in event.keys():
        sendCloudFormationSuccess(event, context)

    # Return an empty response.
    return {
        "statusCode": 200,
        "body": "",
    }