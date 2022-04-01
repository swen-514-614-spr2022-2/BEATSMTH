# BEATSMTH
Utilizes multiple AWS services to generate Beat Saber maps using artificial inteligence to build off user input.

Semester Project for SWEN-514 Engineering Cloud Software Systems

## /client
Static website for interacting with `BEATSMTH`, hosted on s3: http://beatsmth.s3-website-us-east-1.amazonaws.com/

## Setup
This project uses AWS CloudFormation for setup. There are a couple steps required.

### Lambda S3 Bucket
The CloudFormation template relies on creating AWS Lambdas. For development, you may need to set up your own
bucket with any modifications you make. To do this, create an S3 bucket and upload a ZIP containing the files
in the `lambda` directory. Note down the name of the bucket and the "key" (file name of the ZIP).

### CloudFormation Template
**Note: Roles use the LabRole instead of creating them due to permission issues. The LabRole id may also be incorrect for your session.*

Using AWS CloudFormation, use the prompts to create a stack from the template in the repository. Configure the
parameters from previous steps where applicable.