# quote-pipeline

## Usage

- Install dependancies

```[bash]
pip install -r requirements.txt
```

- Place FastText model in a file called `model.bin` under project root
  (or set your filepath with `config.core.fasttext_path`)

- Run

```bash
python main.py
```

For the configuration options, see [config.py](./module/config.py).

## Docker

```bash
docker build -t quote-pipeline .
docker run -d \
    -e KAFKA_BOOTSTRAP_SERVERS=<kafka-ip:port> \
    -e ES_HOST=<elasticsearch-ip:port> \
    quote-pipeline
```

Docker image is also available at [`lsirepfl/quote-pipeline`](https://hub.docker.com/r/lsirepfl/quote-pipeline).
