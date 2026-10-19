"""Integration tests for the chat server's message relay.

Starts the compiled ./server binary (port 2000) and talks to it over TCP.
Run with `make test`.
"""
import os
import queue
import socket
import subprocess
import threading
import time
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_BIN = os.path.join(REPO_ROOT, "server")
HOST, PORT = "127.0.0.1", 2000
TIMEOUT = 2.0


class ServerRelayTest(unittest.TestCase):
    def setUp(self):
        # stdbuf makes the server's stdout line-buffered so we can sync on its log lines.
        self.proc = subprocess.Popen(
            ["stdbuf", "-oL", SERVER_BIN],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.lines = queue.Queue()
        threading.Thread(target=self._pump_stdout, daemon=True).start()
        self._wait_for_log("Server socket was established successfully.")
        self.clients = []

    def tearDown(self):
        for c in self.clients:
            c.close()
        self.proc.kill()
        self.proc.wait()
        self.proc.stdout.close()

    def _pump_stdout(self):
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\n"))

    def _wait_for_log(self, text):
        deadline = time.monotonic() + TIMEOUT
        while time.monotonic() < deadline:
            try:
                line = self.lines.get(timeout=deadline - time.monotonic())
            except queue.Empty:
                break
            if text in line:
                return
        self.fail(f"server never logged {text!r} (exit code: {self.proc.poll()})")

    def connect(self):
        sock = socket.create_connection((HOST, PORT), timeout=TIMEOUT)
        self.clients.append(sock)
        self._wait_for_log("Client connection was successful")
        return sock

    def disconnect(self, sock):
        sock.close()
        self.clients.remove(sock)
        self._wait_for_log("Client connection has been closed.")

    def recv_exactly(self, sock, n):
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def assert_nothing_received(self, sock, wait=0.3):
        sock.settimeout(wait)
        try:
            data = sock.recv(4096)
        except socket.timeout:
            return
        finally:
            sock.settimeout(TIMEOUT)
        self.fail(f"unexpected {len(data)} bytes received: {data[:40]!r}")

    def test_message_is_relayed_to_all_other_clients(self):
        sender, a, b = self.connect(), self.connect(), self.connect()
        sender.sendall(b"alice :hello")
        self.assertEqual(self.recv_exactly(a, 12), b"alice :hello")
        self.assertEqual(self.recv_exactly(b, 12), b"alice :hello")

    def test_sender_does_not_receive_its_own_message(self):
        sender, other = self.connect(), self.connect()
        sender.sendall(b"alice :echo?")
        self.assertEqual(self.recv_exactly(other, 12), b"alice :echo?")
        self.assert_nothing_received(sender)

    def test_relayed_message_contains_only_the_sent_bytes(self):
        sender, other = self.connect(), self.connect()
        sender.sendall(b"hi")
        self.assertEqual(self.recv_exactly(other, 2), b"hi")
        self.assert_nothing_received(other)

    def test_consecutive_messages_arrive_in_order(self):
        sender, other = self.connect(), self.connect()
        expected = b""
        for i in range(5):
            msg = f"bob :msg{i}".encode()
            sender.sendall(msg)
            expected += msg
            time.sleep(0.05)
        self.assertEqual(self.recv_exactly(other, len(expected)), expected)
        self.assert_nothing_received(other)

    def test_relay_continues_after_a_client_disconnects(self):
        sender, leaver, stayer = self.connect(), self.connect(), self.connect()
        self.disconnect(leaver)
        sender.sendall(b"carol :still here?")
        self.assertEqual(self.recv_exactly(stayer, 18), b"carol :still here?")
        self.assertIsNone(self.proc.poll(), "server exited after a client disconnected")

    def test_client_connecting_later_receives_new_messages(self):
        sender = self.connect()
        late = self.connect()
        sender.sendall(b"dave :welcome")
        self.assertEqual(self.recv_exactly(late, 13), b"dave :welcome")


if __name__ == "__main__":
    unittest.main()
