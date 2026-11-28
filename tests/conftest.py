import os
import sys

# Allow `import app` / `import models` from the repository-level tests folder.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
