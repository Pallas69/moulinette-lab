import socket
import struct
import unittest
from moulinette.scope_protocol import MAX_MESSAGE, ScopeProtocolError, receive_object, send_object

class FragmentedSocket:
    def __init__(self, chunks): self.chunks = list(chunks)
    def recv(self, size):
        if not self.chunks: return b''
        value = self.chunks.pop(0)
        self.chunks.insert(0, value[size:]) if len(value) > size else None
        return value[:size]

class ScopeProtocolTests(unittest.TestCase):
    def test_socket_pair_round_trip(self):
        a, b = socket.socketpair()
        with a, b:
            a.settimeout(1); b.settimeout(1)
            send_object(a, {'phase': 'ready', 'scope': 'exemple'})
            self.assertEqual(receive_object(b), {'phase': 'ready', 'scope': 'exemple'})

    def test_fragmented_frame_is_read_fully(self):
        message = b'{"ok":true}'
        wire = struct.pack('!I', len(message)) + message
        self.assertEqual(receive_object(FragmentedSocket([wire[:1], wire[1:3], wire[3:6], wire[6:]])), {'ok': True})

    def test_short_oversized_or_invalid_messages_fail(self):
        cases = [b'', b'\x00\x00', struct.pack('!I', 0), struct.pack('!I', MAX_MESSAGE+1),
                 struct.pack('!I', 5) + b'{}', struct.pack('!I', 2) + b'[]',
                 struct.pack('!I', 3) + b'xxx', struct.pack('!I', 13) + b'{"a":1,"a":2}',
                 struct.pack('!I', 9) + b'{"a":NaN}']
        for wire in cases:
            with self.subTest(wire=wire):
                with self.assertRaises(ScopeProtocolError): receive_object(FragmentedSocket([wire]))

    def test_send_rejects_non_object_nan_and_oversized(self):
        a, b = socket.socketpair()
        with a, b:
            for bad in ([1], {'v': float('nan')}, {'v': 'x' * (MAX_MESSAGE + 1)}):
                with self.assertRaises(ScopeProtocolError): send_object(a, bad)

    def test_closed_or_timed_out_channels_fail(self):
        a, b = socket.socketpair()
        with a, b:
            a.settimeout(0.01)
            with self.assertRaises(ScopeProtocolError): receive_object(a)
            b.close()
            with self.assertRaises(ScopeProtocolError): send_object(a, {'phase': 'go'})

if __name__ == '__main__':
    unittest.main()
