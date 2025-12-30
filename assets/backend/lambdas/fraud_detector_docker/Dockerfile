FROM python:3.12-slim AS builder
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt -t /app/deps

FROM public.ecr.aws/lambda/python:3.12
WORKDIR ${LAMBDA_TASK_ROOT}

COPY --from=builder /app/deps ${LAMBDA_TASK_ROOT}

COPY . .

ENV PYTHONPATH=${LAMBDA_TASK_ROOT}

CMD [ "lambda_function.handler" ]
