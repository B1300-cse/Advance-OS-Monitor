import psutil
import time
import threading
import datetime
from collections import deque
import tkinter as tk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pynput import keyboard

# ================= GLOBAL VARIABLES =================
typing_count = 0
last_activity = time.time()
cpu_history = deque(maxlen=30)

download, upload = 0, 0

# ================= KEYBOARD TRACKING =================
def on_press(key):
    global typing_count, last_activity
    typing_count += 1
    last_activity = time.time()

keyboard.Listener(on_press=on_press).start()

# ================= INTERNET SPEED =================
def speed_worker():
    global download, upload
    try:
        import speedtest
        st = speedtest.Speedtest()
        st.get_best_server()
        download = st.download() / 1_000_000
        upload = st.upload() / 1_000_000
    except:
        download, upload = 0, 0

threading.Thread(target=speed_worker, daemon=True).start()

# ================= TOP PROCESSES =================
def get_top_processes():
    processes = []
    for p in psutil.process_iter(['name', 'cpu_percent']):
        try:
            processes.append((p.info['name'], p.info['cpu_percent'] or 0))
        except:
            pass
    return sorted(processes, key=lambda x: x[1], reverse=True)[:5]

# ================= SCHEDULING ALGORITHMS =================
def fcfs():
    burst = [5, 3, 8]
    wait = [0]
    for i in range(1, len(burst)):
        wait.append(wait[i - 1] + burst[i - 1])
    return wait, sum(wait) / len(wait)

def rr():
    burst = [5, 3, 8]
    q = 2
    rem = burst[:]
    wt = [0, 0, 0]
    t = 0

    while True:
        done = True
        for i in range(len(burst)):
            if rem[i] > 0:
                done = False
                if rem[i] > q:
                    t += q
                    rem[i] -= q
                else:
                    t += rem[i]
                    wt[i] = t - burst[i]
                    rem[i] = 0
        if done:
            break

    return wt, sum(wt) / len(wt), q

# ================= SYSTEM HEALTH =================
def health(cpu, ram, disk):
    return max(0, 100 - int((cpu + ram + disk) / 3))

# ================= UI SETUP =================
root = tk.Tk()
root.title("🔥 ULTRA OS MONITOR PRO")
root.geometry("1000x780")
root.configure(bg="#0f0f0f")

title = tk.Label(
    root,
    text="🔥 ADVANCED OS MONITOR",
    fg="#00e5ff",
    bg="#0f0f0f",
    font=("Arial", 18, "bold")
)
title.pack()

info = tk.Label(
    root,
    fg="white",
    bg="#0f0f0f",
    font=("Consolas", 11),
    justify="left"
)
info.pack()

alert = tk.Label(
    root,
    fg="red",
    bg="#0f0f0f",
    font=("Consolas", 11, "bold")
)
alert.pack()

internet_lbl = tk.Label(root, fg="cyan", bg="#0f0f0f", font=("Consolas", 10))
internet_lbl.pack()

fcfs_lbl = tk.Label(root, fg="yellow", bg="#0f0f0f", font=("Consolas", 10))
fcfs_lbl.pack()

rr_lbl = tk.Label(root, fg="orange", bg="#0f0f0f", font=("Consolas", 10))
rr_lbl.pack()

proc = tk.Label(root, fg="#00ff88", bg="#0f0f0f", font=("Consolas", 10), justify="left")
proc.pack()

# ================= COLOR BARS =================
frame = tk.Frame(root, bg="#0f0f0f")
frame.pack(pady=10)

cpu_bar = tk.Canvas(frame, width=300, height=20, bg="#222")
ram_bar = tk.Canvas(frame, width=300, height=20, bg="#222")
disk_bar = tk.Canvas(frame, width=300, height=20, bg="#222")

cpu_bar.pack(pady=3)
ram_bar.pack(pady=3)
disk_bar.pack(pady=3)

def draw_bar(canvas, value, color):
    canvas.delete("all")
    width = int((value / 100) * 300)
    canvas.create_rectangle(0, 0, width, 20, fill=color, outline="")

# ================= GRAPH =================
fig, ax = plt.subplots(figsize=(5, 2))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# ================= UPDATE LOOP =================
def update():
    global last_activity

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("C:\\").percent
    idle = time.time() - last_activity

    cpu_history.append(cpu)

    # ================= HEALTH =================
    score = health(cpu, ram, disk)

    if cpu > 85:
        status = "🔥 CPU DANGER!"
    elif cpu > 60:
        status = "🟡 CPU LOAD"
    else:
        status = "🟢 CPU OK"

    # ================= TOP PROCESS WARNING =================
    top = get_top_processes()
    warning = ""
    if top and top[0][1] > 20:
        warning = f"⚠ {top[0][0]} using {top[0][1]:.1f}% CPU"

    # ================= INTERNET =================
    internet_lbl.config(
        text=f"🌐 INTERNET → ↓ {download:.2f} Mbps  ↑ {upload:.2f} Mbps"
    )

    # ================= FCFS =================
    w, avg = fcfs()
    fcfs_lbl.config(
        text=f"📊 FCFS → Wait: {w} Avg: {avg:.2f}"
    )

    # ================= RR =================
    w2, avg2, q = rr()
    rr_lbl.config(
        text=f"🔁 RR (Q={q}) → Wait: {w2} Avg: {avg2:.2f}"
    )

    # ================= MAIN INFO =================
    info.config(text=f"""
SYSTEM TIME: {datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')}

SYSTEM HEALTH: {score}/100 ⚡

CPU  : {cpu:.1f}%
RAM  : {ram:.1f}%
DISK : {disk:.1f}%

⌨ Typing: {typing_count}
⏳ Idle: {round(idle,2)} sec
""")

    alert.config(text=f"{status}   {warning}")

    # ================= PROCESS LIST =================
    txt = "TOP PROCESSES:\n"
    for n, c in top:
        txt += f"{n[:15]:15} {c:.1f}%\n"
    proc.config(text=txt)

    # ================= BARS =================
    draw_bar(cpu_bar, cpu, "#00e5ff")
    draw_bar(ram_bar, ram, "#b266ff")
    draw_bar(disk_bar, disk, "#ffd633")

    # ================= GRAPH =================
    ax.clear()
    ax.plot(list(cpu_history), color="#00e5ff")
    ax.set_ylim(0, 100)
    ax.set_title("CPU Usage History")
    canvas.draw()

    root.after(1000, update)

update()
root.mainloop()