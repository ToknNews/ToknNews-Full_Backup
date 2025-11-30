import json, os, fcntl, time

HEARTBEAT = "/var/www/toknnews/data/heartbeat.json"

def update_field(key, value):
    # atomic update so multiple writers don't clash
    with open(HEARTBEAT, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        data = json.load(f)
        data[key] = value
        data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()
        fcntl.flock(f, fcntl.LOCK_UN)
