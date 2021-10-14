curl -X PUT "${ES_HOST:-localhost:9200}/${INDEX:-quotes}?pretty" -H 'Content-Type: application/json' -d'
{
    "mappings": {
      "properties": {
        "article_id": { "type": "keyword" },
        "article_url":  { "type": "keyword" },
        "article_publish_datetime":  { "type": "date" },
        "article_text":  { "type": "text", "analyzer": "french" },
        "article_keyphrases":  { "type": "keyword" },
        "quote": { "type": "text", "analyzer": "french" },
        "speaker": {
          "type": "text", "analyzer": "french",
          "fields": {
            "keyword": { "type": "keyword" }
          }
        },
        "classification": { "type": "keyword" }
      }
    }
}
'