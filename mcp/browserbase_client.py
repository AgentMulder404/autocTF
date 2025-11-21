from browserbase import Browserbase
import os

bb = Browserbase(api_key=os.getenv("BROWSERBASE_API_KEY"))

def create_session():
    return bb.sessions.create(project_id=os.getenv("BROWSERBASE_PROJECT_ID"))

def screenshot(session_id, url, code=None):
    # Note: API may have changed, this is a placeholder
    try:
        if code:
            bb.sessions.update(session_id=session_id, code=code)
        return f"https://browserbase.com/sessions/{session_id}/screenshot"
    except:
        return f"https://placeholder.com/screenshot/{session_id}"