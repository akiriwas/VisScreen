import subprocess
import re
import os
import tempfile
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ScreenSession:
    id: str
    name: str
    time: str
    state: str  # Attached, Detached, Dead, etc.

class ScreenManager:
    @staticmethod
    def list_sessions() -> List[ScreenSession]:
        try:
            result = subprocess.run(['screen', '-list'], capture_output=True, text=True)
            output = result.stdout
        except FileNotFoundError:
            return []

        sessions = []
        # Pattern matches: \t12345.name\t(date time)\t(State)
        # Some versions might have slightly different spacing or formats.
        pattern = re.compile(r'^\t(\d+)\.(.*?)\t\((.*?)\)\t\((.*?)\)', re.MULTILINE)
        
        for match in pattern.finditer(output):
            sessions.append(ScreenSession(
                id=match.group(1),
                name=match.group(2),
                time=match.group(3),
                state=match.group(4)
            ))
            
        return sessions

    @staticmethod
    def get_session_snapshot(session_id: str) -> str:
        """Captures a text snapshot of the screen session using 'hardcopy'."""
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            temp_name = tf.name
        
        try:
            # screen -S <id> -X hardcopy <file>
            subprocess.run(['screen', '-S', session_id, '-X', 'hardcopy', temp_name], check=False)
            if os.path.exists(temp_name) and os.path.getsize(temp_name) > 0:
                with open(temp_name, 'r', errors='replace') as f:
                    content = f.read()
                return content
            return "No content available or session inactive."
        except Exception as e:
            return f"Error capturing snapshot: {str(e)}"
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)

    @staticmethod
    def rejoin(session_id: str, detach: bool = False):
        cmd = ['screen', '-d', '-r', session_id] if detach else ['screen', '-r', session_id]
        # Using os.execvp to replace the current process with screen
        import os
        os.execvp('screen', cmd)

    @staticmethod
    def create(name: Optional[str] = None):
        cmd = ['screen']
        if name:
            cmd += ['-S', name]
        import os
        os.execvp('screen', cmd)

    @staticmethod
    def kill(session_id: str):
        subprocess.run(['screen', '-X', '-S', session_id, 'quit'])
