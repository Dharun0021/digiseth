import asyncio
import websockets
import wave
import os
import signal

wav_filename = "sound_data.wav"
sample_rate = 44100  # Standard audio sample rate
channels = 1  # Mono audio
sample_width = 2  # 16-bit audio
running = True  # Flag to keep the server running

# Prepare .wav file
def prepare_wav_file():
    if os.path.exists(wav_filename):
        os.remove(wav_filename)
    return wave.open(wav_filename, 'wb')

async def handler(websocket, path):
    wav_file = prepare_wav_file()
    wav_file.setnchannels(channels)
    wav_file.setsampwidth(sample_width)
    wav_file.setframerate(sample_rate)

    print("WebSocket connected")
    try:
        async for message in websocket:
            try:
                # Convert message (string) to integer for audio data
                audio_data = int(message)
                # Ensure audio_data is in the range for 16-bit audio
                audio_data = max(-32768, min(32767, audio_data))  # Clamping

                # Pack data as bytes and write to .wav file
                wav_file.writeframes(audio_data.to_bytes(sample_width, 'little', signed=True))
                print(f"Received: {audio_data}")
            except ValueError:
                print("Invalid data received")
    finally:
        wav_file.close()  # Ensure the file is closed on exit
        print("WebSocket disconnected, file saved")

# Signal handler to stop the server
def signal_handler(sig, frame):
    global running
    running = False
    print("Stopping the server...")

# Start WebSocket server
async def main():
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    server = await websockets.serve(handler, "0.0.0.0", 8080)
    print("WebSocket server started")

    while running:
        await asyncio.sleep(1)  # Keep the server running

    server.close()  # Close the server
    await server.wait_closed()  # Wait for the server to close
    print("Server stopped")

# Run the WebSocket server
if __name__ == "__main__":
    asyncio.run(main())
