FROM ubuntu:22.04


RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*


RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs


COPY . /app/
WORKDIR /app/


RUN pip3 install --no-cache-dir --upgrade -r requirements.txt


CMD ["bash", "start"]
