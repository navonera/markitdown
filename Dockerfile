# Dockerfile

FROM public.ecr.aws/lambda/python:3.11

# Install dependencies
COPY requirements.txt .
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Copy the function code
COPY index.py ./

# Set the CMD to your handler
CMD ["index.lambda_handler"]
