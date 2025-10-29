import importlib
import sys

mods = [
    'processing.pr',
    'models.logistic',
    'ingestion.kafka_producer',
]
failed = False
for m in mods:
    try:
        importlib.import_module(m)
        print(m + ' import OK')
    except Exception as e:
        print(m + ' import FAILED:', e)
        failed = True

if failed:
    sys.exit(2)
