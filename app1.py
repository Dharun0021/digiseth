import asyncio
import websockets
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import threading

sample_rate = 44100  # Standard audio sample rate
channels = 1  # Mono audio
sample_width = 2  # 16-bit audio
buffer_size = 1024  # Size of the buffer for visualization
running = True  # Flag to keep the server running

# Global variable to store incoming audio data
audio_data_buffer = np.zeros(buffer_size)

# Tkinter setup for the live plot
root = tk.Tk()
root.title("Live Audio Plot")

# Create a figure and axis for matplotlib plot
fig, ax = plt.subplots()
x = np.arange(0, buffer_size)
line, = ax.plot(x, audio_data_buffer)
ax.set_ylim([0, 1000])  # Set Y limits for the range 0 to 1000

# Tkinter canvas to embed the matplotlib figure
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

def update_plot():
    """Updates the plot with new data."""
    global audio_data_buffer
    line.set_ydata(audio_data_buffer)
    canvas.draw()

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
