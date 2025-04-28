import requests
import threading
import time
import json
import wave

# --- Configuration ---
URL = "http://localhost:5005/v1/audio/speechByStream" # Or your server's IP/port
# Define sample rate (must match the server's output)
# Ideally, get this from config, but hardcode for the script
SAMPLE_RATE = 24000 
CHANNELS = 1
SAMPLE_WIDTH_BYTES = 2 # Corresponds to 16-bit PCM

HEADERS = {"Content-Type": "application/json", "Accept": "audio/wav"}
NUM_REQUESTS = 4
REQUEST_DATA_TEMPLATE = {
    "input": "This is test request number {i}. Certainly! Here's a long and laugh-filled joke for you: Why did the tomato turn red? Because it saw the salad dressing! Now, imagine this scenario: One fine day in a bustling kitchen, a tomato was sitting on a shelf, peacefully minding its own business. Suddenly, a gust of wind blew through, carrying with it the tantalizing aroma of freshly made salad dressing. The tomato, curious and slightly envious, leaned forward to catch a whiff. Just as the tomato's",
    "voice": "tara",
    "stream": True # Make sure stream is true for the correct endpoint
}
# --------------------

# Store results/errors
results = {}

def make_request(req_num):
    """Function to send a single request and store result/error."""
    start_time = time.time()
    payload = REQUEST_DATA_TEMPLATE.copy()
    payload["input"] = payload["input"].format(i=req_num)
    print(f"[Req {req_num}] Sending request...")
    try:
        # Use stream=True for requests library to handle streaming response
        response = requests.post(
            URL,
            headers=HEADERS,
            json=payload,
            stream=True, # Important for streaming endpoint
            timeout=150 # Set a reasonable timeout
        )

        # Consume the stream to ensure it completes or errors
        audio_data = b""
        chunk_count = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                audio_data += chunk
                chunk_count += 1

        response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)

        # --- Save the audio data to a file using the wave module --- 
        output_filename = f"stress_test_output_{req_num}.wav"
        if audio_data:
            try:
                with wave.open(output_filename, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(SAMPLE_WIDTH_BYTES)
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes(audio_data)
                print(f"[Req {req_num}] Audio saved to {output_filename}")
            except Exception as e: # Catch wave errors too
                print(f"[Req {req_num}] FAILED to save audio file {output_filename} using wave module: {e}")
        else:
             print(f"[Req {req_num}] No audio data received, cannot save file.")
        # ----------------------------------------------------------

        end_time = time.time()
        results[req_num] = {
            "status": response.status_code,
            "duration": end_time - start_time,
            "chunks": chunk_count,
            "size_bytes": len(audio_data),
            "error": None
         }
        print(f"[Req {req_num}] Success! Status: {response.status_code}, Duration: {results[req_num]['duration']:.2f}s, Chunks: {chunk_count}")

    except requests.exceptions.RequestException as e:
        end_time = time.time()
        results[req_num] = {
             "status": "Error",
             "duration": end_time - start_time,
             "chunks": 0,
             "size_bytes": 0,
             "error": str(e)
        }
        print(f"[Req {req_num}] FAILED! Error: {e}, Duration: {results[req_num]['duration']:.2f}s")

# --- Create and start threads ---
threads = []
print(f"Starting {NUM_REQUESTS} concurrent requests...")
overall_start = time.time()
for i in range(NUM_REQUESTS):
    thread = threading.Thread(target=make_request, args=(i + 1,))
    threads.append(thread)
    thread.start()

# --- Wait for all threads to complete ---
for thread in threads:
    thread.join()

overall_end = time.time()
print(f"\n--- Test Complete ---")
print(f"Overall Duration: {overall_end - overall_start:.2f}s")

# --- Summarize results ---
success_count = 0
fail_count = 0
for i in range(1, NUM_REQUESTS + 1):
    if i in results and results[i]["error"] is None:
        success_count += 1
        # print(f"Request {i}: Success ({results[i]['duration']:.2f}s, {results[i]['size_bytes']} bytes)")
    elif i in results:
        fail_count += 1
        print(f"Request {i}: FAILED ({results[i]['duration']:.2f}s, Error: {results[i]['error']})")
    else:
         fail_count += 1
         print(f"Request {i}: FAILED (No result recorded)")

print(f"\nSummary: {success_count} succeeded, {fail_count} failed.")