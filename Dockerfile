FROM python:3.9-slim

LABEL maintainer="Marco Romanelli <marco.romanelli@epfl.ch>"

# Install git, required for pke and spacy models
RUN apt-get update
RUN apt-get install -y git

# Run with rootless user
RUN useradd -ms /bin/bash appuser
USER appuser

# Set working directory
RUN mkdir -p /home/appuser/app
WORKDIR /home/appuser/app

ENV PYTHONPATH=/home/appuser/app
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Upgrade pip
RUN pip install --upgrade pip

# Install packages from requirements.txt
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Install code dependancies
RUN python -m nltk.downloader stopwords

# Copy FastText model
COPY model.bin .

# Copy the current directory contents into the container at /app
COPY --chown=appuser:appuser module/ ./module/
COPY --chown=appuser:appuser main.py .

CMD ["python", "main.py"]