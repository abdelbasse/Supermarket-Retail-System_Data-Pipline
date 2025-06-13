import os

class KafkaConfig:
    BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    INPUT_TOPIC = 'video-stream'
    OUTPUT_TOPIC = 'processed-video-frames'
    
    # Producer settings
    PRODUCER_CONFIG = {
        'bootstrap_servers': BOOTSTRAP_SERVERS,
        'value_serializer': lambda x: json.dumps(x).encode('utf-8'),
        'key_serializer': lambda x: x.encode('utf-8') if x else None,
        'acks': 'all',
        'retries': 3
    }
    
    # Consumer settings
    CONSUMER_CONFIG = {
        'bootstrap_servers': BOOTSTRAP_SERVERS,
        'group_id': 'video-processing-group',
        'auto_offset_reset': 'latest',
        'enable_auto_commit': True,
        'value_deserializer': lambda m: json.loads(m.decode('utf-8'))
    }