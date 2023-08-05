import re, uuid

def get_mac():
    mac = ""
    for i in re.findall('..', '%012x' % uuid.getnode()):
        mac += i
    return mac