import os
import time
import pathlib
import shutil


try:
    import ujson as json
except ImportError:
    import json

try:
    from log import logger
except ImportError:
    from atiny.log import logger


class DataFile:

    path: str
    exists: bool = False

    read_mode: str
    write_mode: str

    def __init__(self, file_path, json_module='json'):

        if os.path.islink(file_path):
            file_path = os.path.abspath(file_path)

        while os.path.isdir(file_path):
            file_path += '_'

        self.path = file_path

        if json_module == 'json':
            self.json_module = json
            self.read_mode = 'r'
            self.write_mode = 'w'

        pathlib.Path(
            os.path.dirname(self.path)
        ).mkdir(parents=True, exist_ok=True)

        if os.path.isfile(self.path):
            self.exists = True

        if os.path.islink(self.path) and not os.path.isdir(os.path.abspath(self.path)):
            self.exists = True

    def _loads(self, data):
        if self.json_module == json:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                ms_time = int(time.time_ns() / 1000)
                logger.info(f'json.JSONDecodeError, save bk in {self.path}.{ms_time}')
                shutil.copyfile(self.path, f'{self.path}.{ms_time}')
                return {}

    def _dumps(self, data):

        if self.json_module == json:
            return json.dumps(data)

    def update(self, data):
        if self.json_module == json:
            current_data = self.load()

            if current_data:
                data.update(current_data)

            return data

    def load(self):

        if self.exists:
            with open(self.path, self.read_mode) as rf:
                data = self._loads(rf.read())

            return data

        if self.json_module == json:
            return {}

    def save(self, data, update=False):

        if update:
            data = self.update(data)

        with open(self.path, self.write_mode) as wf:
            wf.write(
                self._dumps(data)
            )
