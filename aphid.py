import flag, launch

def main(args):
  args = flag.Munch(args)
  quit = rye_chan(1)
  launch.LaunchConfigFiles(quit=quit, filenames=args)

  say 'WAITING'
  quit.Recv()
  say 'QUITTING'
