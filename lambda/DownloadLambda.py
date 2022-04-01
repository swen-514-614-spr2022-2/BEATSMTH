import boto3
import json
import os
import urllib.request
from botocore.errorfactory import ClientError
from threading import Thread

MAX_DOWNLOADS_BEFORE_SPLIT = 3

lambdaClient = None
lambdaFunctionName = os.environ["AWS_LAMBDA_FUNCTION_NAME"]
bucketName = os.environ["BeatSaverDownloadZipsBucketName"]

def get_add_result_function(mapIds, downloadedMaps, existingMaps, failedMaps):
    """Returns a function to be run in a thread for downloading maps.
    """

    def function():
        # Run the lambda.
        downloadResponse = lambdaClient.invoke(
            FunctionName = lambdaFunctionName,
            InvocationType = "RequestResponse",
            Payload = json.dumps({
                "body": json.dumps(mapIds),
            }),
        )

        # Add the results.
        results = json.loads(json.loads(downloadResponse["Payload"].read().decode("utf8"))["body"])
        downloadedMaps.extend(results["downloadedMaps"])
        existingMaps.extend(results["existingMaps"])
        failedMaps.extend(results["failedMaps"])

    return function

def lambda_handler(event, context):
    """Handles the Lambda request.
    """

    # Prepare the results of the maps.
    downloadedMaps = []
    existingMaps = []
    failedMaps = []
    mapIds = json.loads(event["body"])

    if len(mapIds) > MAX_DOWNLOADS_BEFORE_SPLIT:
        # Start the Lambda client.
        global lambdaClient
        lambdaClient = boto3.client("lambda")

        # Split the downloads into multiple lambdas.
        threads = []
        for i in range(0, len(mapIds), MAX_DOWNLOADS_BEFORE_SPLIT):
            threads.append(Thread(target=get_add_result_function(mapIds[i:i + MAX_DOWNLOADS_BEFORE_SPLIT], downloadedMaps, existingMaps, failedMaps)))

        # Start all threads
        for x in threads:
            x.start()

        # Wait for all of them to finish
        for x in threads:
            x.join()
    else:
        # Download the maps.
        for mapId in mapIds:
            key = "beat-saver-zips/" + mapId + ".zip"
            s3Client = boto3.client("s3")

            try:
                # Read the file and add it as existing if it does not error.
                s3Client.head_object(Bucket=bucketName, Key=key)
                existingMaps.append(mapId)
            except ClientError:
                # Download the map if it does not exist.
                try:
                    # Get the download information and the download.
                    mapData = json.loads(urllib.request.urlopen("https://api.beatsaver.com/maps/id/" + mapId).read().decode("utf8"))
                    mapFile = urllib.request.urlopen(mapData["versions"][0]["downloadURL"]).read()

                    # Download the map.
                    s3Client.put_object(
                        Body = mapFile,
                        Bucket = bucketName,
                        Key = key,
                    )
                    downloadedMaps.append(mapId)
                except:
                    # Add the map as failed.
                    failedMaps.append(mapId)

    # Return the response.
    return {
        "statusCode": 200,
        "body": json.dumps({
            "downloadedMaps": downloadedMaps,
            "existingMaps": existingMaps,
            "failedMaps": failedMaps,
        }),
        "headers": {
            "Content-Type": "application/json"
        },
        "isBase64Encoded": False,
    }
