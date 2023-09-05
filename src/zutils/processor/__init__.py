import time
import threading
from .kafka_processor import KafkaProcessor


def run_processors(Processor, cfg, workers=1):
    tasks = []
    for i in range(workers):
        t = Processor(cfg)
        tasks.append(t)
    for t in tasks:
        t.start()
    while threading.active_count() > 1:
        time.sleep(0.2)


__all__ = ['KafkaProcessor', 'run_processors']
