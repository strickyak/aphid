from . import flag

WatchdogFile = flag.String('watchdog_file', '', 'File to watch for updates.')
WatchdogSeconds = flag.String('watchdog_seconds', 300, 'How often to check for updates.')

def StartFileWatcher():
  "Call this to create a goroutine to watch thie file, and die if it ceases to update."

def RunTasks():
  "Try the tasks, and if they all succeed, update the file."
