import requests

def connect_to_stream():
    url = "http://localhost:8000/stream/jobs"

    with requests.get(url, stream=True) as response:
        if response.status_code != 200:
            print(f"Failed to connect: {response.status_code}")
            return

        print("Connected to /stream/jobs. Listening for events...\n")

        buffer = ""
        for line in response.iter_lines(decode_unicode=True):
            if line == "":
                # End of one event block
                if buffer.startswith("data:"):
                    print(f"Raw event data: {buffer[5:].strip()}\n")
                buffer = ""
            elif line.startswith(":"):
                # Comment / keep-alive line (starts with colon)
                continue
            else:
                buffer += line + "\n"

if __name__ == "__main__":
    try:
        connect_to_stream()
    except KeyboardInterrupt:
        print("\nDisconnected.")
