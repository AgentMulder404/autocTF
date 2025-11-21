import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'backend'))

from main import app
from mangum import Mangum

# Vercel serverless handler
handler = Mangum(app, lifespan="off")
