def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 5))
    ipv4 = s.getsockname()[0]
    s.close()
    return ipv4