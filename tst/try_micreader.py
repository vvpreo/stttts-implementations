import threading

from micreader import MicReader

if __name__ == '__main__':
    mr = MicReader()

    mr.start()

    for chunk in mr.listen():
        print(f'CHUNK ({len(chunk)}): {chunk[:60]}')
