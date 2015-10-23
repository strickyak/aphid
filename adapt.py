from go import io, os, time, log

def UnixToTime(a):
  if 0 <= a < 9999999999:  # Seconds.
    return time.Unix(a, 0)
  if 1000000000000 < a < 9999999999000:  # Milliseconds.
    return time.Unix(0, 1000000 * a)
  if 1000000000000000 < a < 9999999999000000:  # Microseconds.
    return time.Unix(0, 1000 * a)
  log.Panicf('UnixToTime cannot convert %v', a)

pass
