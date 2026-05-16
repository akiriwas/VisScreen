import unittest
from unittest.mock import patch, MagicMock
from visscreen.manager import ScreenManager, ScreenSession

class TestScreenManager(unittest.TestCase):
    @patch('subprocess.run')
    def test_list_sessions_parsing(self, mock_run):
        # Sample output from screen -list
        mock_output = """There are screens on:
	1234.pts-0.hostname	(05/16/26 12:00:00)	(Detached)
	5678.mysession	(05/16/26 12:05:00)	(Attached)
2 Sockets in /run/screen/S-user.
"""
        mock_run.return_value = MagicMock(stdout=mock_output, text=True)
        
        sessions = ScreenManager.list_sessions()
        
        self.assertEqual(len(sessions), 2)
        
        self.assertEqual(sessions[0].id, "1234")
        self.assertEqual(sessions[0].name, "pts-0.hostname")
        self.assertEqual(sessions[0].state, "Detached")
        
        self.assertEqual(sessions[1].id, "5678")
        self.assertEqual(sessions[1].name, "mysession")
        self.assertEqual(sessions[1].state, "Attached")

    @patch('subprocess.run')
    def test_list_sessions_empty(self, mock_run):
        mock_output = "No Sockets found in /run/screen/S-user.\n"
        mock_run.return_value = MagicMock(stdout=mock_output, text=True)
        
        sessions = ScreenManager.list_sessions()
        self.assertEqual(len(sessions), 0)

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="Snapshot content")
    @patch('os.remove')
    def test_get_session_snapshot(self, mock_remove, mock_open, mock_getsize, mock_exists, mock_run):
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        
        content = ScreenManager.get_session_snapshot("1234")
        
        self.assertEqual(content, "Snapshot content")
        mock_run.assert_called_once()
        self.assertIn("hardcopy", mock_run.call_args[0][0])
        mock_remove.assert_called_once()

if __name__ == '__main__':
    unittest.main()
