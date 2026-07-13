"""Put pipeline/ on the import path so tests can import store, compile, ingest_* directly."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline"))
