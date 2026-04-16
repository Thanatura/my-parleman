#!/usr/bin/env python3
import argparse
import socket


def main() -> int:
    parser = argparse.ArgumentParser(description="Check TCP connectivity")
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()

    sock = socket.socket()
    sock.settimeout(args.timeout)
    try:
        sock.connect((args.host, args.port))
    except OSError:
        return 1
    finally:
        sock.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
