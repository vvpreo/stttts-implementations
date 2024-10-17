import queue
import threading
from typing import Iterable

import sounddevice
from devbooster import InterruptHandler


class MicReaderAbstract(InterruptHandler, threading.Thread):
    def __init__(self):
        InterruptHandler.__init__(self)
        threading.Thread.__init__(self)
        self.sample_rate_hertz: int = 8000
        self.invocations_per_second: int = 50
        self.bytes_per_frame: int = 2

    def run(self):
        def callback(indata, frames, time, status):
            if status:
                print(status)
            # Преобразуем данные в байты и отправляем на сервер
            buf = indata.tobytes()  # AI why 640 bytes?
            self._put_to_q(buf)

        dtype = f'int{int(self.bytes_per_frame * 8)}'
        print(f'dtype={dtype}')

        print(self.sample_rate_hertz)
        print(self.bytes_per_frame)
        print(self.invocations_per_second)

        blocksize = int(self.sample_rate_hertz * self.bytes_per_frame / self.invocations_per_second)
        print(f'blocksize={blocksize}')

        with sounddevice.InputStream(
                samplerate=self.sample_rate_hertz,
                channels=1,
                dtype=dtype,
                blocksize=blocksize,
                callback=callback,
        ):
            print("Capturing audio stream...")
            while self.not_interrupted():
                sounddevice.sleep(int(1000 / self.invocations_per_second))  # Поддерживаем поток открытым
            print("Stopped capturing audio.")
            sounddevice.stop()

    def _put_to_q(self, data: bytes):
        raise NotImplementedError()

    def listen(self):
        raise NotImplementedError()


class MicReader(MicReaderAbstract):
    def __init__(self):
        super().__init__()
        self._queue: queue.Queue[bytes] = queue.Queue()

    def _put_to_q(self, data: bytes):
        self._queue.put_nowait(data)

    def listen(self) -> Iterable[bytes]:
        try:
            while next_chunk := self._queue.get(timeout=1):
                yield next_chunk
        except queue.Empty:
            pass
