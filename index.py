import os
import json
import io
import boto3
from boto3.dynamodb.conditions import Key
from markitdown import MarkItDown

# Safe fix for Windows DLL issues (ignored on Linux)
if not hasattr(os, "add_dll_directory"):
    os.add_dll_directory = lambda x: None

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.doc']

def lambda_handler(event, context):
    try:
        print("Lambda started!")

        # Get AWS account ID from Lambda context
        aws_account_id = context.invoked_function_arn.split(':')[4]
        print(f"AWS Account ID: {aws_account_id}")
        
        for record in event.get('Records', []):
            print("Processing SQS message...")
            message = json.loads(record['body'])

            # Extract metadata from message
            bucket = message['bucket']
            key = message['key']
            table = message['table']
            file_hash = key.split('/')[1]
            print(f"Fetching file from S3: s3://{bucket}/{key}")
            print(f"Table: {table}")
            print(f"File Hash: {file_hash}")

            # Download file from S3
            response = s3.get_object(Bucket=bucket, Key=key)
            file_bytes = response['Body'].read()
            content_type = response['ContentType']
            print(f"Downloaded file size: {len(file_bytes)} bytes")
            print(f"Detected MIME type: {content_type}")

            # Determine file extension
            file_extension = os.path.splitext(key)[1].lower()
            print(f"Detected file extension: {file_extension}")

            # Validate supported file types
            if file_extension in SUPPORTED_EXTENSIONS:
                print("Processing with MarkItDown...")
                file_stream = io.BytesIO(file_bytes)
                markitdown = MarkItDown()

                try:
                    markdown_result = markitdown.convert_stream(file_stream)
                    markdown = markdown_result.text_content
                    print(f"Markdown output length: {len(markdown)} characters")
                except Exception as e:
                    print(f"Error during conversion: {str(e)}")
                    raise e

            elif content_type.startswith("image/"):
                raise ValueError("Image files are not supported for Markdown conversion.")

            elif file_extension == '.document':
                raise ValueError(
                    "Unsupported file type '.document'. Please export Google Docs as .docx or .pdf before uploading."
                )

            else:
                raise ValueError(f"Unsupported file type: {file_extension} ({content_type})")

            # Update the DynamoDB table
            try:
                table_resource = dynamodb.Table(table)
                response = table_resource.update_item(
                    Key={'fileHash': file_hash},
                    UpdateExpression="SET textContent = :content, processingStatus = :status",
                    ExpressionAttributeValues={
                        ':content': markdown,
                        ':status': 'completed'
                    },
                    ReturnValues="UPDATED_NEW"
                )
                print("Successfully updated table with markdown content")

                # Publish to SNS topic
                topic_arn = os.environ.get('SNS_TOPIC_ARN')
                if not topic_arn:
                    raise ValueError("SNS_TOPIC_ARN environment variable is not set")
                    
                print(f"Publishing to SNS Topic ARN: {topic_arn}")
                
                sns_message = {
                    'fileHash': file_hash,
                    'status': 'completed',
                    'bucket': bucket,
                    'key': key
                }
                
                sns.publish(
                    TopicArn=topic_arn,
                    Message=json.dumps(sns_message)
                )
                print("Published to SNS topic successfully")

            except Exception as e:
                print(f"Error updating table or publishing to SNS: {str(e)}")
                raise e

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'All records processed.'})
        }

    except Exception as e:
        print("Exception occurred:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
