TIME MEASUREMENTS
    % make gen_llvm
    total lines:
    2653
    % python -Om tool -tE @test_files.txt
    WARNING:MainThread:deco:21:wrap():started time counting
    WARNING:MainThread:deco:24:wrap():stopped time counting
    WARNING:MainThread:deco:28:wrap():total time in processing:1.601285 sec

    real	0m1.846s
    user	0m9.563s
    sys	0m8.903s

TRACING WITH llvm-project/9deb4fda30be47e4aea5671055a0f655a048afdc
    The memory consumption is dominated by `threading` library. Queue's `put` is #6.
    No matter whether its size is bound or unbound: Queue of size one consume the same
    amount of memory as Queue of unbound size, though this was measured on relatively
    small number of files.

    % make gen_llvm
    total lines:
    2653
    % time -- python -Om tool -tEM @test_files.txt
    WARNING:MainThread:deco:44:wrap():started tracing
    WARNING:MainThread:deco:21:wrap():started time counting
    WARNING:MainThread:deco:24:wrap():stopped time counting
    WARNING:MainThread:deco:28:wrap():total time in processing:0.507604 sec
    WARNING:MainThread:pretty:43:display_top():top 10 lines
    WARNING:MainThread:pretty:48:display_top():#1: …/lib/python3.15t/threading.py:998: 314.6 KiB
    WARNING:MainThread:pretty:57:display_top():	_start_joinable_thread(self._bootstrap, handle=self._os_thread_handle,
    WARNING:MainThread:pretty:48:display_top():#2: …/lib/python3.15t/subprocess.py:869: 80.5 KiB
    WARNING:MainThread:pretty:57:display_top():	def __init__(self, args, bufsize=-1, executable=None,
    WARNING:MainThread:pretty:48:display_top():#3: …/lib/python3.15t/subprocess.py:1878: 56.8 KiB
    WARNING:MainThread:pretty:57:display_top():	def _execute_child(self, args, executable, preexec_fn, close_fds,
    WARNING:MainThread:pretty:48:display_top():#4: …/lib/python3.15t/pathlib/__init__.py:969: 56.6 KiB
    WARNING:MainThread:pretty:57:display_top():	return io.open(self, mode, buffering, encoding, errors, newline)
    WARNING:MainThread:pretty:48:display_top():#5: …/lib/python3.15t/threading.py:985: 46.7 KiB
    WARNING:MainThread:pretty:57:display_top():	_limbo[self] = self
    WARNING:MainThread:pretty:48:display_top():#6: …/lib/python3.15t/queue.py:137: 42.2 KiB
    WARNING:MainThread:pretty:57:display_top():	def put(self, item, block=True, timeout=None):
    WARNING:MainThread:pretty:48:display_top():#7: …/lib/python3.15t/threading.py:1058: 35.0 KiB
    WARNING:MainThread:pretty:57:display_top():	def _bootstrap_inner(self):
    WARNING:MainThread:pretty:48:display_top():#8: …/lib/python3.15t/subprocess.py:2158: 33.2 KiB
    WARNING:MainThread:pretty:57:display_top():	def _wait(self, timeout):
    WARNING:MainThread:pretty:48:display_top():#9: …/lib/python3.15t/queue.py:177: 31.1 KiB
    WARNING:MainThread:pretty:57:display_top():	def get(self, block=True, timeout=None):
    WARNING:MainThread:pretty:48:display_top():#10: …/lib/python3.15t/subprocess.py:1774: 30.5 KiB
    WARNING:MainThread:pretty:57:display_top():	def _get_handles(self, stdin, stdout, stderr):
    WARNING:MainThread:pretty:62:display_top():231 other: 932.1 KiB
    WARNING:MainThread:pretty:67:display_top():total allocated size: 1659.3 KiB
    WARNING:MainThread:deco:62:wrap():stopping tracing
    WARNING:MainThread:deco:64:wrap():stopped tracing
