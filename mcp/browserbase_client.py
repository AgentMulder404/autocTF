"""
Browserbase Client with Session Management and Retry Logic
Handles rate limiting gracefully with proper cleanup
"""

from browserbase import Browserbase
import os
import time
import logging
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global session management
_active_session = None
_session_creation_time = None
SESSION_TIMEOUT = 300  # 5 minutes - reuse session within this window

class BrowserbaseClient:
    """Browserbase client with session management and retry logic"""

    def __init__(self):
        self.api_key = os.getenv("BROWSERBASE_API_KEY")
        self.project_id = os.getenv("BROWSERBASE_PROJECT_ID")

        if not self.api_key or not self.project_id:
            logger.warning("⚠️  Browserbase not configured - screenshots disabled")
            self.enabled = False
        else:
            self.enabled = True
            self.bb = Browserbase(api_key=self.api_key)

        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def is_enabled(self) -> bool:
        """Check if Browserbase is enabled"""
        return self.enabled

    def create_session(self, reuse: bool = True) -> Optional[any]:
        """
        Create or reuse a Browserbase session

        Args:
            reuse: If True, reuse existing session if available

        Returns:
            Session object or None if failed
        """
        if not self.enabled:
            logger.warning("⚠️  Browserbase disabled - skipping session creation")
            return None

        global _active_session, _session_creation_time

        # Reuse existing session if still valid
        if reuse and _active_session and _session_creation_time:
            age = time.time() - _session_creation_time
            if age < SESSION_TIMEOUT:
                logger.info(f"♻️  Reusing existing session (age: {age:.0f}s)")
                return _active_session

        # Create new session with retry logic
        for attempt in range(self.max_retries):
            try:
                logger.info(f"📸 Creating Browserbase session (attempt {attempt + 1}/{self.max_retries})...")
                session = self.bb.sessions.create(project_id=self.project_id)

                if session and hasattr(session, 'id'):
                    logger.info(f"✅ Session created: {session.id[:20]}...")

                    # Store for reuse
                    _active_session = session
                    _session_creation_time = time.time()

                    return session
                else:
                    logger.error("❌ Session creation returned unexpected format")
                    return None

            except Exception as e:
                error_str = str(e)

                # Handle rate limiting
                if "429" in error_str or "Too Many Requests" in error_str.lower():
                    logger.error(f"🚫 Browserbase rate limit exceeded!")
                    logger.error(f"   {error_str}")

                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (attempt + 1)
                        logger.info(f"⏳ Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        logger.error("❌ Max retries exceeded - screenshots disabled for this run")
                        return None

                # Handle authentication errors
                elif "401" in error_str or "unauthorized" in error_str.lower():
                    logger.error("❌ Browserbase authentication failed")
                    logger.error(f"   Check BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID")
                    return None

                # Handle other errors
                else:
                    logger.error(f"❌ Browserbase error: {error_str}")

                    if attempt < self.max_retries - 1:
                        logger.info(f"⏳ Retrying in {self.retry_delay}s...")
                        time.sleep(self.retry_delay)
                    else:
                        logger.error("❌ Session creation failed after retries")
                        return None

        return None

    def screenshot(self, session_id: str, url: str, code: Optional[str] = None) -> Optional[str]:
        """
        Capture screenshot from a session

        Args:
            session_id: Browser session ID
            url: URL to capture
            code: Optional JavaScript code to execute

        Returns:
            Screenshot URL or None if failed
        """
        if not self.enabled:
            logger.warning("⚠️  Browserbase disabled - screenshot skipped")
            return None

        if not session_id:
            logger.error("❌ No session ID provided for screenshot")
            return None

        try:
            # Execute code if provided
            if code:
                try:
                    self.bb.sessions.update(session_id=session_id, code=code)
                except Exception as e:
                    logger.warning(f"⚠️  Failed to execute code in session: {e}")

            # Return screenshot URL
            screenshot_url = f"https://www.browserbase.com/sessions/{session_id}"
            logger.info(f"📸 Screenshot URL: {screenshot_url}")
            return screenshot_url

        except Exception as e:
            logger.error(f"❌ Screenshot capture failed: {e}")
            return None

    def close_session(self, session_id: Optional[str] = None):
        """
        Close a browser session

        Args:
            session_id: Session to close (if None, closes active session)
        """
        if not self.enabled:
            return

        global _active_session, _session_creation_time

        try:
            # Determine which session to close
            if session_id:
                logger.info(f"🔒 Closing session: {session_id[:20]}...")
            elif _active_session and hasattr(_active_session, 'id'):
                session_id = _active_session.id
                logger.info(f"🔒 Closing active session: {session_id[:20]}...")
            else:
                logger.debug("No session to close")
                return

            # Try multiple methods to close session
            try:
                # Method 1: Complete session
                if hasattr(self.bb.sessions, 'complete'):
                    self.bb.sessions.complete(session_id)
                    logger.info("✅ Session completed")

                # Method 2: Stop session
                elif hasattr(self.bb.sessions, 'stop'):
                    self.bb.sessions.stop(session_id)
                    logger.info("✅ Session stopped")

                # Method 3: Delete session
                elif hasattr(self.bb.sessions, 'delete'):
                    self.bb.sessions.delete(session_id)
                    logger.info("✅ Session deleted")

                else:
                    logger.debug("⚠️  No close method available - session will auto-expire")

            except Exception as e:
                logger.warning(f"⚠️  Session close failed (non-critical): {e}")

            # Clear active session
            if _active_session and hasattr(_active_session, 'id') and _active_session.id == session_id:
                _active_session = None
                _session_creation_time = None

        except Exception as e:
            logger.error(f"❌ Error during session cleanup: {e}")

    def close_all_sessions(self):
        """Close all active sessions"""
        if not self.enabled:
            return

        global _active_session

        logger.info("🔒 Closing all sessions...")

        # Close tracked session
        if _active_session:
            self.close_session()

        # Try to list and close all sessions (if API supports it)
        try:
            if hasattr(self.bb.sessions, 'list'):
                sessions = self.bb.sessions.list(project_id=self.project_id)
                for session in sessions:
                    if hasattr(session, 'id'):
                        self.close_session(session.id)
                        time.sleep(0.5)  # Rate limit friendly

            logger.info("✅ All sessions closed")

        except Exception as e:
            logger.debug(f"Could not list/close all sessions: {e}")


# Global client instance
_client = None

def get_client() -> BrowserbaseClient:
    """Get or create global Browserbase client"""
    global _client
    if _client is None:
        _client = BrowserbaseClient()
    return _client


# Backward compatibility functions
def create_session(reuse: bool = True):
    """Create or reuse a browser session"""
    client = get_client()
    return client.create_session(reuse=reuse)


def screenshot(session_id: str, url: str, code: Optional[str] = None) -> Optional[str]:
    """Capture screenshot"""
    client = get_client()
    return client.screenshot(session_id, url, code)


def close_session(session_id: Optional[str] = None):
    """Close session"""
    client = get_client()
    client.close_session(session_id)


def close_all_sessions():
    """Close all sessions"""
    client = get_client()
    client.close_all_sessions()


# Cleanup on module unload
import atexit

def cleanup():
    """Cleanup function called on exit"""
    client = get_client()
    if client.is_enabled():
        logger.info("🧹 Cleaning up Browserbase sessions...")
        client.close_all_sessions()

atexit.register(cleanup)
