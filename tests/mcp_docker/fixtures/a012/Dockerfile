FROM python:3.12-alpine3.24

COPY --chmod=0444 server.py /server.py
USER 65532:65532
ENTRYPOINT ["python3", "/server.py"]
