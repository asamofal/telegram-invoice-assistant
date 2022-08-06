FROM python:3.10.6-bullseye

RUN apt-get update && apt-get install --no-install-recommends -y \
    libreoffice-common \
    libreoffice-writer \
    libreoffice-java-common \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/invoice-assistant

COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
