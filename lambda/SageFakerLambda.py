import json
import random
import boto3
import os
import re

S3_CLIENT = boto3.client("s3")
SNS_CLIENT = boto3.client("sns")
TRAINING_BUCKET_NAME = os.environ["BeatSaverDownloadZipsBucketName"]
SNS_ARN = os.environ["NotificationSystem]
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
    rand_note = {
      "_time": random.randint(1, 60),
      "_type": random.randint(0, 5),
      "_lineLayer": random.randint(0, 2),
      "_lineIndex": random.randint(0, 3),
      "_cutDirection": random.randint(0, 8)
    }
    rand_note.update(note)
    map.append(rand_note)
  sorted(map, key=lambda i: i["_time"])
  return map
  
def clean_event(event):
  body_list = json.dumps(event["body"]).split("&")
  ret = {
    "body": [],
    "email": ""
  }
  for el in body_list:
    pair = el.split("=")
    if (pair[0] == "email"):
      if (not(len(pair) < 2 or pair[1] == '')):
        ret["email"] = pair[1]
    else:
      index = 0
      if(len(re.findall('\d+', pair[0])) > 0):
        index = int(re.findall('\d+', pair[0])[0])
      while(len(ret["body"]) <= index):
        ret["body"].append({})
      if(not(len(pair) < 2 or pair[1] == '')):
        new_key = re.findall('([a-zA-Z_]*)\d*.*', pair[0])[0]
        ret["body"][index][new_key] = int(pair[1])
  return ret


def lambda_handler(event, context):
  # train() # Pulls in a number of maps to train with, currently not being utilized
  new_event = clean_event(event)
  body = random_fillings(new_event["body"])
  # use body["email"] with SNS
  subscribe_response = SNS_CLIENT.subscribe(
    TopicArn=SNS_ARN,
    Protocol='email',
    Endpoint=new_event["email"])
  publish_response = SNS_CLIENT.publish(
    TopicArn=SNS_ARN,
    Message="This is a test message",
    Subject="Test Notification")
  return {
    'statusCode': 200,
    'body': json.dumps(body)
  }
