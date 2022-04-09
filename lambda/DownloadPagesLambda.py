import boto3
import json
import os
import ssl
import urllib.request

PAGES_TO_DOWNLOAD = 25


def lambda_handler(event, context):
    """Handles the Lambda request.
    """

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
    return json.loads(downloadResponse["Payload"].read().decode("utf8"))
