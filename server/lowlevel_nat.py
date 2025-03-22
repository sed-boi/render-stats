# server/lowlevel_nat.py
try:
    import miniupnpc
except ImportError:
    miniupnpc = None

def SetupMapping(port, ext_ip_buf, buf_size):
    if miniupnpc is None:
        print("miniupnpc module not available. Please install it.")
        return -1
    upnp = miniupnpc.UPnP()
    upnp.discoverdelay = 200
    ndevices = upnp.discover()
    if ndevices == 0:
        print("No UPnP devices discovered.")
        return -1
    upnp.selectigd()
    external_ip = upnp.externalipaddress()
    try:
        upnp.addportmapping(port, 'TCP', upnp.lanaddr, port, 'Blender Render Stats', '')
    except Exception as e:
        print("Error adding port mapping:", e)
        return -1
    if len(external_ip) + 1 > buf_size:
        return -1
    ext_ip_buf[:] = external_ip.encode('utf-8') + b'\x00'
    return 0

def RemoveMapping(port):
    if miniupnpc is None:
        print("miniupnpc module not available. Cannot remove mapping.")
        return -1
    upnp = miniupnpc.UPnP()
    upnp.discoverdelay = 200
    ndevices = upnp.discover()
    if ndevices == 0:
        return -1
    upnp.selectigd()
    try:
        upnp.deleteportmapping(port, 'TCP')
    except Exception as e:
        print("Error removing port mapping:", e)
        return -1
    return 0
