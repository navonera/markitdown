import os
import json
import io
import base64
import boto3
from boto3.dynamodb.conditions import Key
from markitdown import MarkItDown

# Safe fix for Windows DLL issues (ignored on Linux)
if not hasattr(os, "add_dll_directory"):
    os.add_dll_directory = lambda x: None

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        print("Lambda started!")

        for record in event.get('Records', []):
            print("Processing SQS message...")
            message = json.loads(record['body'])

            # Extract metadata from message
            bucket = message['bucket']
            key = message['key']
            table = message['table']
            # Extract hash from the key (assuming format like "hash/filename.pdf")
            file_hash = key.split('/')[1]
            print(f"Fetching PDF from S3: s3://{bucket}/{key}")
            print(f"Table: {table}")
            print(f"File Hash: {file_hash}")

            # Download PDF from S3
            response = s3.get_object(Bucket=bucket, Key=key)
            pdf_bytes = response['Body'].read()
            print(f"Downloaded PDF size: {len(pdf_bytes)} bytes")

            # Convert to markdown
            pdf_stream = io.BytesIO(pdf_bytes)
            markitdown = MarkItDown()
            markdown_result = markitdown.convert_stream(pdf_stream)
            markdown = markdown_result.text_content

            print(f"Markdown output length: {len(markdown)} characters")

            # Update the DynamoDB table with markdown content and set status to completed
            try:
                table_resource = dynamodb.Table(table)

                # Update the record directly using fileHash as the primary key
                response = table_resource.update_item(
                    Key={
                        'fileHash': file_hash
                    },
                    UpdateExpression="SET textContent = :content, processingStatus = :status",
                    ExpressionAttributeValues={
                        ':content': markdown,
                        ':status': 'completed'
                    },
                    ReturnValues="UPDATED_NEW"
                )
                print("Successfully updated table with markdown content")

            except Exception as e:
                print(f"Error updating table: {str(e)}")
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
