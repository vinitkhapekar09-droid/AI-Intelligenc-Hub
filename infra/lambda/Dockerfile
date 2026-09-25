FROM public.ecr.aws/lambda/python:3.11

COPY backend/requirements-lambda.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY backend/ ${LAMBDA_TASK_ROOT}/

# Override the handler in the Lambda function configuration for the digest:
# app.lambda_handler.digest_handler
CMD ["app.lambda_handler.api_handler"]
