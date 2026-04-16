# In-memory storage to replace Redis
# This is safe and resets every time you restart the server.

class ScanStorage:
    def __init__(self):
        self._data = {}

    def set(self, task_id, result):
        self._data[task_id] = result

    def get(self, task_id):
        return self._data.get(task_id)

scan_storage = ScanStorage()
