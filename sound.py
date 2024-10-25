import asyncio
import websockets
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import threading
import signal
import sys
import wave
import struct

sample_rate = 44100  # Standard audio sample rate
channels = 1  # Mono audio
sample_width = 2  # 16-bit audio
buffer_size = 1024  # Size of the buffer for visualization
running = True  # Flag to keep the server running
audio_data_buffer = np.zeros(buffer_size)

# Function to gracefully exit on Ctrl+C
def signal_handler(sig, frame):
    global running
    print("Stopping the Digital Stethoscope...")
    running = False
    root.quit()  # Exit Tkinter main loop
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Tkinter setup for the live plot
root = tk.Tk()
root.title("Digital Stethoscope")
root.geometry("800x600")

style = ttk.Style()
style.theme_use("clam")

main_frame = ttk.Frame(root, padding="10")
main_frame.pack(fill=tk.BOTH, expand=True)

title_label = ttk.Label(main_frame, text="Digital Stethoscope: Live Audio Data", font=("Helvetica", 16))
title_label.pack(pady=10)

control_frame = ttk.Frame(main_frame)
control_frame.pack(pady=10)

start_button = ttk.Button(control_frame, text="Start Server", command=lambda: print("Starting server..."))
start_button.grid(row=0, column=0, padx=5)

stop_button = ttk.Button(control_frame, text="Stop Server", command=lambda: print("Stopping server..."))
stop_button.grid(row=0, column=1, padx=5)

clear_button = ttk.Button(control_frame, text="Clear Data", command=lambda: clear_data())
clear_button.grid(row=0, column=2, padx=5)

current_value_label = ttk.Label(control_frame, text="Current Audio Value: N/A", font=("Helvetica", 12))
current_value_label.grid(row=1, columnspan=3, pady=5)

fig, ax = plt.subplots()
x = np.arange(0, buffer_size)
line, = ax.plot(x, audio_data_buffer)
ax.set_ylim([0, 1000])

canvas = FigureCanvasTkAgg(fig, master=main_frame)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

def clear_data():
    """Clears the audio data buffer."""
    global audio_data_buffer
    audio_data_buffer.fill(0)
    update_plot()

def update_plot():
    """Updates the plot with new data."""
    global audio_data_buffer
    
    line.set_ydata(audio_data_buffer)
    canvas.draw()
    current_value_label.config(text=f"Current Audio Value: {audio_data_buffer[-1]:.2f}")
    root.after(50, update_plot)

def generate_heartbeat_wav(data, filename="heartbeat.wav"):
    """Generates a heartbeat sound and saves it as a .wav file."""
    duration = 1.0  # seconds
    num_samples = int(sample_rate * duration)
    frequency = 100.0  # Frequency of heartbeat
    
    amplitude = 32767  # Max amplitude for 16-bit audio
    values = []

    for i in range(num_samples):
        value = int(amplitude * np.sin(2 * np.pi * frequency * i / sample_rate))
        packed_value = struct.pack('<h', value)  # 16-bit audio (little endian)
        values.append(packed_value)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setparams((channels, sample_width, sample_rate, num_samples, 'NONE', 'not compressed'))
        wav_file.writeframes(b''.join(values))
    
    print(f"Heartbeat audio saved as {filename}")

async def handler(websocket, path):
    global audio_data_buffer

    print("WebSocket connected")
    try:
        async for message in websocket:
            try:
                audio_data = int(message)
                audio_data = max(0, min(1000, audio_data))  # Clamping
                audio_data_buffer = np.roll(audio_data_buffer, -1)
                audio_data_buffer[-1] = audio_data

                # Generate a heartbeat sound based on audio_data
                if audio_data > 500:  # Simulate a threshold for generating a heartbeat sound
                    generate_heartbeat_wav(audio_data)
                
                print(f"Received: {audio_data}")
            except ValueError:
                print("Invalid data received")
    finally:
        print("WebSocket disconnected")

async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8080)
    print("WebSocket server started")
    while running:
        await asyncio.sleep(1)
    server.close()
    await server.wait_closed()
    print("Server stopped")

def run_asyncio_event_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

asyncio_loop = asyncio.new_event_loop()
asyncio_thread = threading.Thread(target=run_asyncio_event_loop, args=(asyncio_loop,))
asyncio_thread.start()

root.after(50, update_plot)
root.mainloop()

asyncio_loop.call_soon_threadsafe(asyncio_loop.stop)
asyncio_thread.join()
