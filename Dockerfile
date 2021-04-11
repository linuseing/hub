FROM python:3.8 as base

WORKDIR /app


FROM base as builder

RUN pip install poetry==1.0.10

COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output /requirements.txt
RUN ls

FROM base as final

COPY --from=builder /requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

COPY ./src .
RUN ls

CMD ["python3", "./main.py"]
