# Use an official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.10-x86_64

# Copy all your ML code and models
COPY predict.py .
COPY models/ ./models/
COPY ml_requirements.txt .

# Install all dependencies
RUN pip install -r ml_requirements.txt

# Set the command to run the lambda handler
# (We will create this file in the next step)
COPY lambda_handler.py .
CMD [ "lambda_handler.handler" ]