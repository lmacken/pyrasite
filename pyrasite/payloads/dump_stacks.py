import sys
import traceback

for thread, frame in sys._current_frames().items():
    print("Thread 0x%x" % thread)
    traceback.print_stack(frame)
    print()
