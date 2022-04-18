import boto3
import json
import os
import urllib.request
from botocore.errorfactory import ClientError
from io import BytesIO
from threading import Thread
from zipfile import ZipFile

MAX_DOWNLOADS_BEFORE_SPLIT = 10

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
    mapIds = []
    if "Records" in event.keys():
        for record in event["Records"]:
            mapIds.append(record["body"])
    elif "headers" in event.keys() and "content-type" in event["headers"] and event["headers"]["content-type"]:
        for entry in event["body"].split("&"):
            mapIds.append(entry.split("=")[1])
    else:
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
            baseKey = "beat-saver-maps/" + mapId
            s3Client = boto3.client("s3")

            try:
                # Read the info.dat file and add it as existing if it does not error.
                s3Client.head_object(Bucket=bucketName, Key=baseKey + "/info.dat")
                existingMaps.append(mapId)
            except ClientError:
                # Download the map if it does not exist.
                try:
                    # Get the download information and the download.
                    mapData = json.loads(urllib.request.urlopen("https://api.beatsaver.com/maps/id/" + mapId).read().decode("utf8"))
                    mapFile = urllib.request.urlopen(mapData["versions"][0]["downloadURL"]).read()

                    # Put the map files in S3.
                    # The files that aren't map data (covers and songs) are not saved.
                    zipFile = ZipFile(BytesIO(mapFile), "r")
                    for fileName in zipFile.namelist():
                        if fileName.endswith(".dat"):
                            s3Client.put_object(
                                Body = zipFile.open(fileName),
                                Bucket = bucketName,
                                Key = baseKey + "/" + fileName,
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
