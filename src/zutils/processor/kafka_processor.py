import time
import json
import ssl
from datetime import date, datetime
from threading import Event, Thread
from kafka import KafkaConsumer,KafkaProducer
from omegaconf import OmegaConf
from .. import Object


class Consumer(Object, Thread):
    def __init__(self, topic, **kwargs):
        Object.__init__(self)
        Thread.__init__(self, daemon=True)
        self._stop = Event()
        self.consumer = KafkaConsumer(topic, **kwargs)

    def stop(self):
        self._stop.set()

    def is_stopped(self):
        return self._stop.is_set()

    def run(self):
        while not self.is_stopped():
            try:
                batches = self.consumer.poll(timeout_ms=0, max_records=200)
                if not batches:
                    time.sleep(0.01)
                for tp,records in batches.items():
                    for idx,r in enumerate(records):
                        try:
                            self.on_message(r.value)
                        except Exception as e:
                            self.log.exception(e)
            except Exception as e:
                self.log.exception(e)

    def on_message(self, body):
        pass


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, bytes):
            return obj.decode('utf8')
        else:
            return json.JSONEncoder.default(self, obj)


class Producer(object):
    def __init__(self, **kwargs):
        Object.__init__(self)
        self.producer = KafkaProducer(**kwargs)

    def push(self, topic, message, key=None, flush=True):
        if isinstance(message, (dict, list)):
            body = json.dumps(message, cls=JsonEncoder, ensure_ascii=False)
        else:
            body = '{}'.format(message)
        if isinstance(body, str):
            body = body.encode('utf8')
        if isinstance(key, str):
            key = key.encode('utf8')
        self.producer.send(topic, body, key=key)
        if flush:
            self.producer.flush()


class KafkaProcessor(Consumer):
    def __init__(self, cfg):
        self.cfg = cfg
        kwargs = {k:v for k,v in OmegaConf.to_object(cfg.input).items() if k not in 
                ['topic', 'ssl_certfile', 'ssl_keyfile']}
        if cfg.input.security_protocol == 'SASL_SSL':
            context = ssl.create_default_context()
            context.load_cert_chain(certfile=cfg.input.ssl_certfile, 
                    keyfile=cfg.input.ssl_keyfile, password='')
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            kwargs['ssl_context'] = context
        Consumer.__init__(self, self.cfg.input.topic, **kwargs)
        
        kwargs = {k:v for k,v in OmegaConf.to_object(cfg.output).items() if k not in 
                ['topic', 'ssl_certfile', 'ssl_keyfile']}
        if cfg.output.security_protocol == 'SASL_SSL':
            context = ssl.create_default_context()
            context.load_cert_chain(certfile=cfg.output.ssl_certfile, 
                    keyfile=cfg.output.ssl_keyfile, password='')
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            kwargs['ssl_context'] = context
        self.producer = Producer(**kwargs)
        self.init()

    def init(self):
        pass

    def on_message(self, message):
        data = json.loads(message)
        self.log.info('on message: {}'.format(data))
        try:
            resp = self.process(data)
            self.producer.push(self.cfg.output.topic, resp)
        except Exception as e:
            self.log.exception(e)

    def process(self, data):
        pass
