FROM python:alpine3.18
WORKDIR /

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY monitor-access.py .
RUN chmod +x monitor-access.py
CMD /monitor-access.py
