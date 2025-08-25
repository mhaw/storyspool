import ipaddress, socket, urllib.parse

PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

def validate_external_url(url: str):
    try:
        u = urllib.parse.urlparse(url)
        if u.scheme not in ("http","https"):
            return False, "scheme must be http/https"
        host = u.hostname
        if not host:
            return False, "missing hostname"
        for family in (socket.AF_INET, socket.AF_INET6):
            try:
                infos = socket.getaddrinfo(host, None, family, 0, 0, socket.AI_ADDRCONFIG)
            except socket.gaierror:
                continue
            for *_, sockaddr in infos:
                ip = ipaddress.ip_address(sockaddr[0])
                if any(ip in net for net in PRIVATE_RANGES):
                    return False, "private address not allowed"
        return True, None
    except Exception as e:
        return False, str(e)
