import os, signal, psutil

def kill_port(port):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    print(f"Killing PID {proc.info['pid']} listening on {port}")
                    os.kill(proc.info['pid'], signal.SIGTERM)
        except Exception:
            pass

kill_port(8000)
