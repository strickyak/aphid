from go import regexp

MATCH_HOST_IN_PATH = regexp.MustCompile('/@([-A-Za-z0-9.]+)@?($|/.*$)').FindStringSubmatch

def HostAndPath(r):
  host = r.Host
  path = r.URL.Path
  m = MATCH_HOST_IN_PATH(path)
  if m:
    return m[1], m[2]
  return host, path
