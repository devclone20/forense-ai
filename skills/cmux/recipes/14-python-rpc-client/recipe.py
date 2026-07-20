#!/usr/bin/env python3
"""Minimal cmux JSON-RPC client. Usage: python3 recipe.py"""
import json, os, socket

SOCK = os.environ.get("CMUX_SOCKET_PATH", "/tmp/cmux.sock")

def rpc(method, params=None, req_id="1"):
    payload = {"id": req_id, "method": method, "params": params or {}}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(SOCK)
        s.sendall(json.dumps(payload).encode() + b"\n")
        return json.loads(s.recv(65536).decode())

if __name__ == "__main__":
    print("ping:", rpc("system.ping"))
    print("workspaces:", rpc("workspace.list"))
    print("notify:", rpc("notification.create", {"title": "Hi", "body": "From Python"}))
