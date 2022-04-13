import json
import random
import boto3
import os

S3_CLIENT = boto3.client("s3")
TRAINING_BUCKET_NAME = os.environ["BeatSaverDownloadZipsBucketName"]
MAP_TRAINING_COUNT = 3


def get_random_training_files(n=MAP_TRAINING_COUNT):
  response = S3_CLIENT.list_objects_v2(Bucket=TRAINING_BUCKET_NAME)
  s3_files = list(filter(
    lambda contents: contents["Key"].split("/")[-1].upper() != "INFO.DAT", 
    response["Contents"])
  )
  random.shuffle(s3_files)
  return s3_files[:n]

def train():
  s3_files = get_random_training_files()
  for s3_file in s3_files:
    file_content = json.loads(
      S3_CLIENT.get_object(Bucket=TRAINING_BUCKET_NAME, Key=s3_file["Key"])["Body"].read()
    )
    # use file_contents to inform fillings
    
def random_fillings(body):
  map = []
  for note in body:
    randNote = {
      "_time": random.randint(1, 60),
      "_type": random.randint(0, 5),
      "_lineLayer": random.randint(0, 2),
      "_lineIndex": random.randint(0, 3),
      "_cutDirection": random.randint(0, 8)
    }
    randNote.update(note)
    map.append(randNote)
  sorted(map, key=lambda i: i["_time"])
  return map


def lambda_handler(event, context):
  # train() # Pulls in a number of maps to train with, currently not being utilized
  return {
    'statusCode': 200,
    'body': json.dumps(random_fillings(json.loads(event["body"])))
  }
