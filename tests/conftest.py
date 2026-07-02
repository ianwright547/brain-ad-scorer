import os
import tempfile

# Point the app at a throwaway database before app.main is imported,
# so tests never touch the real cache/history.
os.environ["SCORER_DB"] = os.path.join(tempfile.mkdtemp(), "test_scorer.db")
