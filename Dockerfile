ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./
CMD ["python", "main_down_kram.py"]