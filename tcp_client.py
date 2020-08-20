import argparse
import socket
import subprocess
import sys
import atexit


class TCPClient:
    def __init__(self, host, port, strategy):
        # start strategy
        self.process = subprocess.Popen(strategy, shell=True, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        # connect to server
        self.conn = socket.create_connection((host, port))
        self.buffer = b''

        atexit.register(self.on_exit)

    def write_to_process(self, msg):
        print(msg)
        self.process.stdin.write(msg)
        self.process.stdin.flush()

    def read_message(self):
        while True:
            batch = self.conn.recv(1024)
            if batch:
                self.buffer += batch
                eol_index = self.buffer.rindex(b'\n')
                if eol_index != -1:
                    eol_index += 1
                    break
            else:
                sys.exit()

        msg = self.buffer[:eol_index]
        self.buffer = self.buffer[eol_index:]

        return msg

    def run(self):
        # receive config
        self.write_to_process(self.read_message())

        # game loop
        while True:
            # receive state
            self.write_to_process(self.read_message())

            # send command
            command = self.process.stdout.readline()
            self.conn.send(command)

    def on_exit(self):
        self.process.terminate()
        self.conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str)
    parser.add_argument('--port', type=str)
    parser.add_argument('--strategy', type=str)

    args = parser.parse_args()
    client = TCPClient(args.host, args.port, args.strategy)
    client.run()
