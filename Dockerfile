FROM public.ecr.aws/lambda/python:3.11

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the Lambda function code
COPY index.py ./

# Command for AWS Lambda to run the handler
CMD ["index.lambda_handler"]
