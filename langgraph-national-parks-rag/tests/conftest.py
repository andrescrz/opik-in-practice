import os

# Must be set before opik is imported so @opik.track becomes a pass-through in unit tests.
os.environ.setdefault("OPIK_TRACK_DISABLE", "true")
