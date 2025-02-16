FROM python

# Install curl and Node.js
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g prettier@3.4.2 \
    && rm -rf /var/lib/apt/lists/*

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg  && apt-get install -y flac

RUN git config --global user.name "sawhneysatvik" && \
    git config --global user.email "satvik.sawhney2005@gmail.com"

WORKDIR /app

COPY . /app
#COPY ./requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

CMD uvicorn app:app --host 0.0.0.0 --port 8000 --reload --reload-exclude data --reload-exclude datagen.py