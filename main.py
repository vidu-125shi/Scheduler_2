# Updated main.py
from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO
from scheduler import Scheduler
from process import DummyProcess
import threading

app = Flask(__name__)
socketio = SocketIO(app)

scheduler = None

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/add_process', methods=['POST'])
def add_process():
    global scheduler
    data = request.json
    pid = data['pid']
    burst = float(data['burst_time'])
    priority = int(data.get('priority', 0))
    arrival_time = float(data.get('arrival_time', 0))

    if scheduler is None:
        scheduler = Scheduler(algorithm=data['algorithm'])

    proc = DummyProcess(pid, burst, priority, arrival_time)
    scheduler.add_process(proc)
    socketio.emit('log', f"✅ Process {pid} added (Arrival: {arrival_time}, Burst: {burst}, Priority: {priority})")
    return jsonify({'status': 'ok'})

@app.route('/start', methods=['POST'])
@app.route('/start', methods=['POST'])
def start():
    global scheduler
    data = request.json
    if not scheduler or not scheduler.ready_queue:
        return jsonify({'error': 'No processes added'}), 400

    # Reset previous results
    scheduler.completed_processes = []

    scheduler.algorithm = data['algorithm']
    if scheduler.algorithm == "Round Robin":
        scheduler.time_quantum = int(data.get('quantum', 2))

    def run_scheduler():
        socketio.emit('clear_queue')
        scheduler.run()
        socketio.emit('scheduling_complete')
        socketio.emit('log', 'Scheduling completed')

    threading.Thread(target=run_scheduler).start()
    return jsonify({'status': 'started'})


@app.route('/results')
def results_data():
    if not scheduler or not scheduler.completed_processes:
        return jsonify({'error': 'No completed data'}), 400

    processes_info = []
    total_waiting, total_turnaround = 0, 0
    gantt_chart = []

    for p in scheduler.completed_processes:
        waiting_time = p.start_time - p.arrival_time
        turnaround_time = p.completion_time - p.arrival_time

        total_waiting += waiting_time
        total_turnaround += turnaround_time

        gantt_chart.append({'pid': p.pid, 'duration': p.burst_time})
        processes_info.append({
            'pid': p.pid,
            'arrival_time': p.arrival_time,
            'burst_time': p.burst_time,
            'priority': p.priority,
            'start_time': round(p.start_time, 2),
            'completion_time': round(p.completion_time, 2),
            'waiting_time': round(waiting_time, 2),
            'turnaround_time': round(turnaround_time, 2)
        })

    avg_waiting = total_waiting / len(processes_info)
    avg_turnaround = total_turnaround / len(processes_info)
    cpu_util = (sum(p.burst_time for p in scheduler.completed_processes) / max(p.completion_time for p in scheduler.completed_processes)) * 100

    return jsonify({
        'processes': processes_info,
        'avg_waiting_time': avg_waiting,
        'avg_turnaround_time': avg_turnaround,
        'cpu_utilization': cpu_util,
        'gantt_chart': gantt_chart
    })

@app.route('/reset', methods=['POST'])
def reset_scheduler():
    global scheduler
    scheduler = None
    return jsonify({'status': 'reset'})


@app.route('/result.html')
def result_html():
    return send_file('result.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)
