import os

log_path = 'backend/error.log'
if os.path.exists(log_path):
    # Try reading as utf-16le then printing as utf-8
    with open(log_path, 'rb') as f:
        content = f.read()
        try:
            text = content.decode('utf-16le')
            print(text[-2000:]) # Last 2000 chars
        except:
            # Fallback to utf-8
            print(content[-1000:].decode('utf-8', errors='ignore'))
else:
    print("Log not found")
