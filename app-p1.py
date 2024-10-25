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

sample_rate = 44100  # Standard audio sample rate
channels = 1  # Mono audio
sample_width = 2  # 16-bit audio
buffer_size = 1024  # Size of the buffer for visualization
running = True  # Flag to keep the server running

# Global variable to store incoming audio data
audio_data_buffer = np.zeros(buffer_size)

# Function to gracefully exit on Ctrl+C
def signal_handler(sig, frame):
    global running
    print("Stopping the Digital Stethoscope...")
    running = False
    root.quit()  # Exit Tkinter main loop
    sys.exit(0)

# Register signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# Tkinter setup for the live plot
root = tk.Tk()
root.title("Digital Stethoscope")
root.geometry("800x600")  # Set a default size

# Use ttk for modern style
style = ttk.Style()
style.theme_use("clam")

# Main frame for layout
main_frame = ttk.Frame(root, padding="10")
main_frame.pack(fill=tk.BOTH, expand=True)

# Title label
title_label = ttk.Label(main_frame, text="Digital Stethoscope: Live Audio Data", font=("Helvetica", 16))
title_label.pack(pady=10)

# Frame for controls and statistics
control_frame = ttk.Frame(main_frame)
control_frame.pack(pady=10)

# Start and Stop buttons
start_button = ttk.Button(control_frame, text="Start Server", command=lambda: print("Starting server..."))
start_button.grid(row=0, column=0, padx=5)

stop_button = ttk.Button(control_frame, text="Stop Server", command=lambda: print("Stopping server..."))
stop_button.grid(row=0, column=1, padx=5)

clear_button = ttk.Button(control_frame, text="Clear Data", command=lambda: clear_data())
clear_button.grid(row=0, column=2, padx=5)

# Current audio value 

current_value_label = ttk.Label(control_frame, text="Current Audio Value: N/A", font=("Helvetica", 12))
current_value_label.grid(row=1, columnspan=3, pady=5)

# Create a figure and axis for matplotlib plot
fig, ax = plt.subplots()
x = np.arange(0, buffer_size)
line, = ax.plot(x, audio_data_buffer)
ax.set_ylim([0, 1000])  # Set Y limits for the range 0 to 1000

# Tkinter canvas to embed the matplotlib figure
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

    # Update current value label with the latest data point
    current_value_label.config(text=f"Current Audio Value: {audio_data_buffer[-1]:.2f}")

    # Schedule the next update after 50ms
    root.after(50, update_plot)

async def handler(websocket, path):
    global audio_data_buffer

    print("WebSocket connected")
    try:
        async for message in websocket:
            try:
                # Convert message (string) to integer for audio data
                audio_data = int(message)
                # Ensure audio_data is in the range of 0 to 1000
                audio_data = max(0, min(1000, audio_data))  # Clamping

                # Append the data to the buffer
                audio_data_buffer = np.roll(audio_data_buffer, -1)
                audio_data_buffer[-1] = audio_data
                
                print(f"Received: {audio_data}")
            except ValueError:
                print("Invalid data received")
    finally:
        print("WebSocket disconnected")

# Start WebSocket server
async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8080)
    print("WebSocket server started")

    while running:
        await asyncio.sleep(1)  # Keep the server running

    server.close()  # Close the server
    await server.wait_closed()  # Wait for the server to close
    print("Server stopped")

# Function to run the asyncio event loop in the background
def run_asyncio_event_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

# Create a new asyncio event loop
asyncio_loop = asyncio.new_event_loop()

# Start the asyncio loop in a separate thread
asyncio_thread = threading.Thread(target=run_asyncio_event_loop, args=(asyncio_loop,))
asyncio_thread.start()

# Start the live plot updating loop in Tkinter
root.after(50, update_plot)

# Run the Tkinter main loop
root.mainloop()

# Once Tkinter main loop is finished, stop the asyncio event loop
asyncio_loop.call_soon_threadsafe(asyncio_loop.stop)
asyncio_thread.join()