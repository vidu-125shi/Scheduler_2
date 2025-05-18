from process import DummyProcess
import time

class Scheduler:
    def __init__(self, algorithm="FCFS", time_quantum=2):
        self.algorithm = algorithm
        self.time_quantum = time_quantum
        self.ready_queue = []
        self.running_process = None
        self.completed_processes = []

    def add_process(self, process):
        self.ready_queue.append(process)

    def fcfs(self):
        self.ready_queue.sort(key=lambda x: x.arrival_time)
        current_time = 0
        while self.ready_queue:
            process = self.ready_queue.pop(0)
            if current_time < process.arrival_time:
                current_time = process.arrival_time

            process.start_time = current_time
            process.start()
            process.thread.join()  # Still executes in real time

            current_time += process.burst_time
            process.completion_time = current_time

            self.completed_processes.append(process)

    def sjf(self):
        self.ready_queue.sort(key=lambda x: (x.arrival_time, x.burst_time))
        self.fcfs()

    def round_robin(self):
        self.ready_queue.sort(key=lambda x: x.arrival_time)
        time_now = 0
        queue = self.ready_queue[:]
        self.ready_queue.clear()
        first_start = {}

        while queue:
            process = queue.pop(0)
            if time_now < process.arrival_time:
                time_now = process.arrival_time

            if process.start_time is None:
                process.start_time = time_now
                first_start[process.pid] = time_now

            process.start()
            start_tick = time.time()
            exec_time = min(self.time_quantum, process.remaining_time)

            while (time.time() - start_tick) < exec_time and process.thread.is_alive():
                time.sleep(0.05)

            process.pause()

            actual_time = time.time() - start_tick
            process.remaining_time -= actual_time
            time_now += actual_time

            if process.remaining_time > 0:
                queue.append(process)
            else:
                process.completion_time = time_now
                self.completed_processes.append(process)

    def priority_scheduling(self):
        self.ready_queue.sort(key=lambda x: (x.arrival_time, x.priority))
        self.fcfs()

    def run(self):
        if self.algorithm == "FCFS":
            self.fcfs()
        elif self.algorithm == "SJF":
            self.sjf()
        elif self.algorithm == "Round Robin":
            self.round_robin()
        elif self.algorithm == "Priority":
            self.priority_scheduling()
