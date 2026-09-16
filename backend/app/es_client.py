from elasticsearch import Elasticsearch

from app.config import settings

es_client = Elasticsearch(settings.elasticsearch_url)