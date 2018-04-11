#!/usr/bin/env python3


if __name__ == '__main__':
    import sys
    sys.path.append("..")

    import activate
    activate.activate()

from base64 import b64encode
from hashlib import sha256
from sys import stdin

import bcrypt


def encode_pw(pw):
    return b64encode(sha256(pw.encode("utf-8")).digest())


def hashpw(pw, salt=None):
    if salt is None:
        salt = bcrypt.gensalt()
    return bcrypt.hashpw(encode_pw(pw), salt)


def checkpw(pw, hashed):
    return bcrypt.checkpw(encode_pw(pw), hashed)


if __name__ == '__main__':
    print(repr(hashpw(input("Password: "))))
