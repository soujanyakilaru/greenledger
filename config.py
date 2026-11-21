"""Central configuration. Change DATA_DIR to point at the case data folder."""
import os
DATA_DIR = os.environ.get('GREENLEDGER_DATA', os.path.join(os.path.dirname(__file__), '..', 'sprintd-basel-green-ai-data'))
