def get_uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
    return str(timedelta(seconds = round(uptime_seconds)))