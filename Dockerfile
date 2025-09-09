FROM public.ecr.aws/lambda/python:3.11

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --only-binary=:all: "numpy>=1.24" && \
    pip install --prefer-binary -r requirements.txt

# Copy the Lambda function code
COPY index.py ./

# Command for AWS Lambda to run the handler
CMD ["index.lambda_handler"]
