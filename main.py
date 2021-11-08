import json
import asyncio
from aiokafka import AIOKafkaConsumer
from elasticsearch import AsyncElasticsearch
from module import *
from module import keyphrases

async def kafka_handler(queue: asyncio.Queue) -> None:
    """Consume from a Kafka topic and push the messages
    into the queue.
    """
    logger.info("Kafka-handler: start")

    consumer = AIOKafkaConsumer(
        config.kafka.topic,
        bootstrap_servers=config.kafka.bootstrap_servers,
        group_id=None,
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
        #auto_offset_reset="earliest"
    )

    await consumer.start()
    logger.info("Kafka-handler: ready")

    try:
        # Consume messages
        async for msg in consumer:
            logger.debug("Consume message %d:%d at %o" % (msg.partition, msg.offset, msg.timestamp))
            
            article = msg.value
            a_id = article["submission_id"]

            # Basic filter for valid articles
            valid_article = ("text" in article) and len(article["text"]) > 10
            valid_article = valid_article and article["lang"] == "fr"
            if not valid_article:
                logger.debug("Kafka-handler: skip article %s" % a_id)
                continue
            
            logger.debug("Kafka-handler: put article %s in queue" % a_id)
            await queue.put(article)            

    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()
        logger.info("Kafka handler: stop")

async def processing(queue: asyncio.Queue, results: Storage) -> None:
    """Extract quotes and speakers and runs
    the classifier.
    """
    logger.info("Processing: start")

    # Instanciate models
    qa = QuotesExtract(spacy_model)
    ft = FastText()
    kp = KeyphrasesExtract(spacy_model)

    logger.info("Processing: ready")

    while True:
        article = await queue.get()
        a_id = article["submission_id"]
        text = article["text"]
        
        logger.debug("Processing: get article %s" % a_id)

        quotes = qa(text)

        if not quotes:
            logger.debug("Processing: no quotes, skipping")

        else: 
            logger.debug("Processing: found %d quotes" % len(quotes))

            label = ft(text)
            keyphrases = kp(text)
                
            for quote, speaker in quotes:          
                results.append({
                    "article_id": a_id,
                    "article_url": article["url"],
                    "article_publish_datetime": convert_datetime(article["publish_datetime"]),
                    "article_text": article["text"],
                    "article_keyphrases": keyphrases,
                    "quote": quote,
                    "speaker": speaker,
                    "classification": label
                })

        queue.task_done()

async def periodic_output(es: AsyncElasticsearch, results: Storage) -> None:
    """Manage the output process periodically (every `interval` seconds).
    NOTE: schedule is subject to drift over time.
    """
    logger.info("Periodic-output: start")
    
    while True:
        await asyncio.sleep(config.es.output_interval)

        logger.info("Periodic-output: active")

        # Flush results
        if results:
            logger.info(f"Periodic-output: sending {len(results)} results")
            await es_bulk(es, results.flush())
        else:
            logger.info("Periodic-output: no results, skipping")

        logger.info("Periodic-output: asleep")

async def main() -> None:    
    # Elasticsearch client
    es = AsyncElasticsearch(config.es.host)

    q = asyncio.Queue()

    # Results storage
    results = Storage()

    # Create producer task
    producer = asyncio.create_task(kafka_handler(q), name="kafka_handler")

    # Create consumer
    consumers = [
        asyncio.create_task(processing(q, results), name="processing"),
        asyncio.create_task(periodic_output(es, results), name="periodic_output"),
    ]

    # Register callbacks
    for task in consumers+[producer]:
        task.add_done_callback(asynciotask_handler)

    # with both producers and consumers running, wait for the producers to finish
    await producer

    # wait for the remaining tasks to be processed
    await q.join()

    # cancel the consumers, which are now idle
    for c in consumers:
        c.cancel()

    # clear ES
    await es.close()

if __name__ == "__main__":
    logger.info("Start")

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Receive keyboard interrupt")
    finally:
        loop.close()
        
    logger.info("Quit")