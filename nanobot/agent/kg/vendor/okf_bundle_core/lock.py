"""Lock multi-processo do bundle via flock (POSIX) ou locking (Windows).

O predecessor (``nanobot.agent.memory.MemoryStore``) usa ``threading.Lock``,
que cobre só uma instância do agente dentro do MESMO processo. Quando P6
subir um servidor HTTP e P4 rodar ``memory_enrich`` simultaneamente — em
processos diferentes — ``threading.Lock`` não basta. Esta classe é
kernel-level, libera automaticamente se o processo morrer (``kill -9``),
e protege entre múltiplos processos. Decisão travada em P2 para evitar
migração cara depois.

The Windows backend serializes readers and writers (no shared byte-range
locking); POSIX retains the legacy flock semantics for on-disk compatibility.
"""

from __future__ import annotations

import errno
import os
import time
from pathlib import Path

if os.name == "nt":
    import msvcrt
else:
    import fcntl

from .paths import BundleLayout

# Reexporta constantes para que callers usem ``lock.LOCK_EX`` em vez de
# importar ``fcntl`` diretamente — fica fácil mockar em testes se preciso.
LOCK_EX = 2 if os.name == "nt" else fcntl.LOCK_EX
LOCK_SH = 1 if os.name == "nt" else fcntl.LOCK_SH
LOCK_NB = 4 if os.name == "nt" else fcntl.LOCK_NB
LOCK_UN = 8 if os.name == "nt" else fcntl.LOCK_UN


def _try_lock(fd: int, *, exclusive: bool) -> None:
    if os.name == "nt":
        # msvcrt locks from the current file position. It has no shared lock;
        # using exclusive locking for both modes is safe but less concurrent.
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(fd, (LOCK_EX if exclusive else LOCK_SH) | LOCK_NB)


def _unlock(fd: int) -> None:
    if os.name == "nt":
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fd, LOCK_UN)


class LockTimeout(Exception):
    """Levantada quando o lock não pôde ser adquirido dentro do timeout."""

    def __init__(self, path: Path, waited: float) -> None:
        super().__init__(f"timeout waiting {waited:.1f}s for lock: {path}")
        self.path = path
        self.waited = waited


class BundleLock:
    """Flock-based bundle-wide mutex.

    Uso típico::

        with BundleLock(root, layout, exclusive=True, timeout=30) as lock:
            ...  # critical section — escrita durável

    O lock é guardado em ``<root>/<layout.lock_file>`` — ``.memory.lock``
    no Collective Memory e ``.knowledge.lock`` no Acquired Knowledge.
    Implementação: ``fcntl.flock(LOCK_EX | LOCK_NB)`` em loop com
    ``retry_delay``, levantando ``LockTimeout`` ao esgotar ``timeout``.
    """

    def __init__(
        self,
        root: Path,
        layout: BundleLayout,
        *,
        exclusive: bool = True,
        timeout: float = 30.0,
        retry_delay: float = 0.05,
    ) -> None:
        self.root = Path(root)
        self.layout = layout
        self.path = self.root / layout.lock_file
        self.exclusive = exclusive
        self.timeout = timeout
        self.retry_delay = retry_delay
        self._fd: int | None = None
        self._held_exclusive: bool | None = None

    def _open(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        # O_CREAT para que o lock exista na primeira escrita — flock em fd
        # anônimo não protege entre processos. ``0o644`` é o padrão de
        # touch, suficiente para ``.memory.lock``.
        self._fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
        if os.name == "nt" and os.fstat(self._fd).st_size == 0:
            os.write(self._fd, b"\0")

    def acquire(self) -> None:
        """Bloqueia até adquirir o lock ou levantar ``LockTimeout``."""
        if self._fd is None:
            self._open()
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                _try_lock(self._fd, exclusive=self.exclusive)
                self._held_exclusive = self.exclusive
                return
            except OSError as exc:
                # ``LOCK_NB`` levanta EWOULDBLOCK/EAGAIN quando o lock já está
                # segurado por outro processo. Outros errnos são bugs (fd
                # inválido, etc.) e devem propagar.
                contention = (errno.EWOULDBLOCK, errno.EAGAIN)
                if os.name == "nt":
                    contention += (errno.EACCES, errno.EDEADLK)
                if exc.errno not in contention:
                    self.release()
                    raise
                if time.monotonic() >= deadline:
                    self.release()
                    raise LockTimeout(self.path, self.timeout) from None
                time.sleep(self.retry_delay)

    def release(self) -> None:
        """Libera o lock. Idempotente (no-op se já liberado)."""
        if self._fd is None:
            return
        try:
            try:
                if self._held_exclusive is not None:
                    _unlock(self._fd)
            except OSError:
                # fd já fechado por algum motivo — não propagar em release.
                pass
        finally:
            try:
                os.close(self._fd)
            except OSError:
                # fd pode ter sido fechado externamente (test, signal
                # handler, erro upstream). Para ``release`` ser
                # idempotente, swallow — ``release`` é cleanup, não
                # propagar erro de I/O que ninguém vai tratar. Fix
                # 2026-07-30 ocli-review-2.
                pass
            finally:
                self._fd = None
                self._held_exclusive = None

    def __enter__(self) -> BundleLock:
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()

    def __repr__(self) -> str:
        return (
            f"BundleLock(path={self.path!s}, exclusive={self.exclusive}, "
            f"held={self._held_exclusive})"
        )
