FROM python:3.10
WORKDIR /app
COPY ipcam-detector/requirements.txt .
RUN ls
RUN pip install --no-cache-dir -r requirements.txt
COPY ipcam-detector/main.py .

ENTRYPOINT ["python", "main.py"]
CMD ["<RTSP-Stream-URL>", "<Output-Folder>"]