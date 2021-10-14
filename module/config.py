import os


class Bunch(dict):
    def __getattribute__(self, key):
        try: 
            return self[key]
        except KeyError:
            return None
        
    def __setattr__(self, key, value): 
        self[key] = value


core = Bunch()
core.spacy_model = "fr_core_news_lg"
core.fasttext_path = "model.bin"
core.max_char = 1000
core.n_keyphrases = int(os.getenv("N_KEYPHRASES", "10"))

kafka = Bunch()
kafka.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
kafka.topic = os.getenv("KAFKA_TOPIC", "test")

elasticsearch = Bunch()
elasticsearch.host = os.getenv("ES_HOST", "localhost:9200")
elasticsearch.index = os.getenv("ES_INDEX", "quotes")
elasticsearch.output_interval = int(os.getenv("ES_OUTPUT_INTERVAL", "300"))

logger = Bunch()
logger.level = os.getenv("LOG_LEVEL", "INFO").upper()

config = Bunch()
config.core = core
config.kafka = kafka
config.es = elasticsearch
config.logger = logger