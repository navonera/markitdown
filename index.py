import os
import json
import io
import base64
from markitdown import MarkItDown

# Safe fix for Windows DLL issues (ignored on Linux)
if not hasattr(os, "add_dll_directory"):
    os.add_dll_directory = lambda x: None

def lambda_handler(event, context):
    try:
        print("Lambda started!")

        input_pdf_path = '/tmp/input.pdf'

        if 'body' not in event:
            print("No 'body' found in event!")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': "No 'body' field in event payload"})
            }

        print("Decoding base64 PDF...")
        pdf_content = base64.b64decode(event['body'])
        
        with open(input_pdf_path, 'wb') as f:
            f.write(pdf_content)

        print(f"PDF written to {input_pdf_path}")

        with open(input_pdf_path, 'rb') as f:
            pdf_bytes = f.read()
            print(f"PDF size in bytes: {len(pdf_bytes)}")
            pdf_stream = io.BytesIO(pdf_bytes)

        print("Converting PDF to Markdown...")
        markitdown = MarkItDown()
        markdown_result = markitdown.convert_stream(pdf_stream)

        print("Conversion done.")
        markdown = markdown_result.text_content
        print(f"Markdown output length: {len(markdown)} characters")
        

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/markdown',
            },
            'body': markdown
        }

    except Exception as e:
        print("Exception occurred:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }