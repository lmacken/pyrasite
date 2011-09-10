import sys, traceback

for thread, frame in sys._current_frames().iteritems():
    print('Thread 0x%x' % thread)
    traceback.print_stack(frame)
