FROM python:3.9

WORKDIR /app
COPY ./requirements.txt ./

RUN python3 -m venv .venv && \
    .venv/bin/pip3 install --no-cache-dir --upgrade pip && \
    .venv/bin/pip3 install --no-cache-dir -r requirements.txt

COPY ./ ./

EXPOSE 8000

ENTRYPOINT ["/app/.venv/bin/python3", "-m", "piper_recording_studio", "--host", "0.0.0.0"]
