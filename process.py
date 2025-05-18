import threading
import time
import subprocess
import platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class DummyProcess:
    def __init__(self, pid, burst_time, priority=0, arrival_time=0):
        self.pid = pid
        self.burst_time = float(burst_time)
        self.remaining_time = self.burst_time
        self.priority = priority
        self.arrival_time = float(arrival_time)
        self.start_time = None
        self.completion_time = None
        self.state = "Ready"
        self.thread = None
        self.running = False
        self.driver = None
        self.port = 9222 + int(pid)

    def run(self):
        self._close_chrome_tab()
        self.state = "Running"
        self.running = True
        try:
            chrome_options = Options()
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get("chrome://newtab")
            print(f"Process {self.pid}: Chrome tab opened for {self.remaining_time}s")

            
            start_exec = time.time()
            while self.running and (time.time() - start_exec) < self.remaining_time:
                time.sleep(0.1)
            self._close_chrome_tab()
            self.running = False
            self.state = "Waiting"
            self.completion_time = time.time()
            print(f"Process {self.pid}: Burst complete, Chrome tab closed")
        except Exception as e:
            print(f"Error in process {self.pid}: {str(e)}")
        finally:
            if self.state != "Terminated":
                self.state = "Terminated"
                print(f"Process {self.pid} completed")

    def _get_chrome_path(self):
        system = platform.system()
        if system == "Windows":
            return "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        elif system == "Darwin":
            return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        elif system == "Linux":
            return "/usr/bin/google-chrome"
        return None

    def _close_chrome_tab(self):
        try:
            if self.driver:
                self.driver.quit()
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
            else:
                subprocess.run(["pkill", "-f", f"remote-debugging-port={self.port}"], capture_output=True)
            print(f"Process {self.pid}: Chrome tab closed")
        except Exception as e:
            print(f"Error closing Chrome tab: {e}")

    def start(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def pause(self):
        self.running = False
        self.state = "Waiting"
        self._close_chrome_tab()

    def resume(self):
        if not self.running and self.remaining_time > 0:
            self.running = True
            self.state = "Running"
            self.thread = threading.Thread(target=self.run)
            self.thread.start()
