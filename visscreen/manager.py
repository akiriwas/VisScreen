import subprocess
import re
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
