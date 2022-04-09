import boto3
import json
import os
import urllib.request

BUCKETS_TO_CLEAR = {
    os.environ["BeatSaverDownloadZipsBucketName"]
}


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

    # Ignore the request if it is from CloudFormation and it isn't a resource delete.
    # This will happen when a resource is being created or updated.
    if "RequestType" in event.keys() and event["RequestType"] != "Delete":
        sendCloudFormationSuccess(event, context)
        return {
            "statusCode": 200,
            "body": "",
        }

    # Clear the S3 buckets.
    s3 = boto3.resource("s3")
    for bucketName in BUCKETS_TO_CLEAR:
        bucket = s3.Bucket(bucketName)
        bucket.objects.all().delete()

    # Respond to CloudFormation that the event completed.
    if "ResponseURL" in event.keys():
        sendCloudFormationSuccess(event, context)

    # Return the response.
    return {
        "statusCode": 200,
        "body": "",
    }