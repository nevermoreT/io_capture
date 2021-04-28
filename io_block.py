import contextlib
import sys
from io import StringIO
from typing import Generator, Optional

sys_io_name = {0: "stdin", 1: "stdout", 2: "stderr"}


class IOCapture:
    """The capture manager.

    Capture all stdout & stderr to a buffer.
    Use this Class to block IO in some scenario，
    like collecting test cases IO.
    """

    def __init__(self):
        self._capture: Optional[IOManager] = None

    def start_capturing(self) -> None:
        assert self._capture is None
        self._capture = IOManager(out=StdCapture(1), err=StdCapture(2))
        self._capture.start()

    def stop_capturing(self) -> None:
        if self._capture is not None:
            self._capture.finish()
            self._capture = None

    def resume_capture(self) -> None:
        if self._capture is not None:
            self._capture.resume()

    def read_capture(self):
        assert self._capture is not None
        return self._capture.read()

    def suspend_capture(self) -> None:
        self._capture.suspend()

    @contextlib.contextmanager
    def capture(self, out_buf: dict) -> Generator[None, None, None]:
        self.resume_capture()
        try:
            yield
        finally:
            self.suspend_capture()

        out, err = self.read_capture()
        out_buf['out'] = out
        out_buf['err'] = err


class StdCapture:

    def __init__(self, fd):
        assert fd in (1, 2)
        name = sys_io_name[fd]
        self.name = name
        self._old = getattr(sys, name)
        self.tmp_io = StringIO()

    def start(self) -> None:
        setattr(sys, self.name, self.tmp_io)

    def finish(self) -> None:
        setattr(sys, self.name, self._old)
        self.tmp_io.close()

    def suspend(self) -> None:
        setattr(sys, self.name, self._old)

    def resume(self) -> None:
        setattr(sys, self.name, self.tmp_io)

    def snap(self):
        self.tmp_io.seek(0)
        res = self.tmp_io.read()
        self.tmp_io.seek(0)
        self.tmp_io.truncate()
        return res


class IOManager:
    def __init__(self, out: StdCapture, err: StdCapture):
        self._out = out
        self._err = err

    def start(self) -> None:
        self._out.start()
        self._err.start()

    def finish(self) -> None:
        self._out.finish()
        self._err.finish()

    def suspend(self) -> None:
        self._out.suspend()
        self._err.suspend()

    def resume(self) -> None:
        self._out.resume()
        self._err.resume()

    def read(self):
        out = self._out.snap()
        err = self._err.snap()

        return out, err


def test_capture():
    io_capture = IOCapture()
    result_dict = dict()

    io_capture.start_capturing()

    with io_capture.capture(result_dict):
        print("hello")
        print("world")
        sys.stderr.write("hello world again\n")

    print(result_dict)

    io_capture.stop_capturing()
    print(result_dict['out'])
    sys.stderr.write(result_dict['err'])


if __name__ == "__main__":
    test_capture()
