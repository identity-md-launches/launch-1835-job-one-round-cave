"""Descriptor-relative, no-follow workspace files for public RPC evidence (POSIX)."""
import argparse
import contextlib
import json
import os
import secrets
import stat
import sys

class FileBoundaryError(ValueError):
    pass

def parts(path):
    raw = os.fspath(path)
    if not isinstance(raw, str) or not raw or raw.startswith('/'):
        raise FileBoundaryError('use a relative workspace path')
    names = raw.split('/')
    if any(not name or name in ('.', '..') or name.startswith('.') for name in names):
        raise FileBoundaryError('hidden, empty and parent path components are refused')
    return names

@contextlib.contextmanager
def parent(path, create=False):
    names = parts(path)
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise FileBoundaryError('POSIX no-follow file descriptors are required')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open('.', flags)
    try:
        for name in names[:-1]:
            if create:
                try:
                    os.mkdir(name, mode=0o755, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(name, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd, names[-1]
    finally:
        os.close(fd)

def read_bytes(path, limit):
    if type(limit) is not int or limit < 0:
        raise FileBoundaryError('limit must be a nonnegative integer')
    with parent(path) as (directory, name):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=directory)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise FileBoundaryError('input must be a regular file')
            chunks, remaining = [], limit + 1
            while remaining:
                chunk = os.read(fd, min(65536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b''.join(chunks)
            if len(raw) > limit:
                raise FileBoundaryError('input exceeds byte limit')
            return raw
        finally:
            os.close(fd)

def write_bytes(path, raw, limit):
    if type(limit) is not int or limit < 0 or not isinstance(raw, bytes):
        raise FileBoundaryError('bytes and a nonnegative integer limit are required')
    if len(raw) > limit:
        raise FileBoundaryError('output exceeds byte limit')
    with parent(path, create=True) as (directory, name):
        # Never overwrite a pre-existing target, including a symlink/hard link.
        # Publish a complete file with an atomic no-clobber link in this directory.
        temporary = '.snapshot-' + secrets.token_hex(16)
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=directory)
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory,
                    follow_symlinks=False)
        finally:
            os.unlink(temporary, dir_fd=directory)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path')
    parser.add_argument('--limit', type=int, default=100000)
    args = parser.parse_args()
    try:
        raw = read_bytes(args.path, args.limit)
        print(json.dumps({'path': args.path, 'bytes': len(raw), 'regular_no_follow': True}))
        return 0
    except (OSError, FileBoundaryError) as exc:
        print('safe-snapshot-files: ' + str(exc), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
