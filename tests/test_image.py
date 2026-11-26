import socket
from importlib.metadata import distributions

import pytest


def test_the_image_has_neither_presidio_nor_spacy():
    names = {d.metadata["Name"].lower() for d in distributions()}
    assert [n for n in names if n.startswith("presidio") or n == "spacy"] == []


def test_a_socket_connect_to_1_1_1_1_port_53_fails():
    with pytest.raises(OSError):
        socket.create_connection(("1.1.1.1", 53), timeout=3)
