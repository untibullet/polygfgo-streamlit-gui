import subprocess


class CLIProcess(subprocess.Popen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __del__(self):
        self.terminate()
        self.wait()