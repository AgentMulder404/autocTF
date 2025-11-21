from browserbase import Browserbase
import os

bb = Browserbase(api_key=os.getenv("BROWSERBASE_API_KEY"),
                 project_id=os.getenv("BROWSERBASE_PROJECT_ID"))

def create_session():
    return bb.session.create()

def screenshot(session_id, url, code=None):
    if code:
        bb.session.append_script(session_id=session_id, code=code)
    return bb.session.screenshot(session_id=session_id, url=url)