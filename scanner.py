import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from parsers import parse_file
from models import ImageRecord

def iter_paths(roots, recursive, cancel_event):
    for root in roots:
        if cancel_event.is_set():
            return
        if os.path.isfile(root):
            yield root
        elif os.path.isdir(root):
            if recursive:
                for current, dirs, names in os.walk(root):
                    if cancel_event.is_set():
                        return
                    dirs[:] = sorted(dirs)
                    for name in names:
                        if cancel_event.is_set():
                            return
                        yield os.path.join(current, name)
            else:
                try:
                    with os.scandir(root) as entries:
                        for entry in entries:
                            if cancel_event.is_set():
                                return
                            if entry.is_file(follow_symlinks=False):
                                yield entry.path
                except OSError:
                    continue

def scan(roots, recursive, cancel_event, on_batch, on_progress, batch_size=100):
    pending = []
    completed = 0
    with ThreadPoolExecutor(max_workers=min(8, max(2, os.cpu_count() or 2))) as pool:
        futures = {}
        for path in iter_paths(roots, recursive, cancel_event):
            if cancel_event.is_set():
                break
            futures[pool.submit(_process, path)] = path
            if len(futures) >= 128:
                done, _ = _wait_some(futures)
                for future in done:
                    futures.pop(future, None)
                    pending.append(future.result())
                    completed += 1
                    if len(pending) >= batch_size:
                        on_batch(pending)
                        pending = []
                    on_progress(completed)
        for future in list(futures):
            if cancel_event.is_set():
                future.cancel()
            if future.done() or not cancel_event.is_set():
                try:
                    pending.append(future.result())
                    completed += 1
                    if len(pending) >= batch_size:
                        on_batch(pending)
                        pending = []
                    on_progress(completed)
                except Exception:
                    pass
    if pending:
        on_batch(pending)
    return completed

def _wait_some(futures):
    from concurrent.futures import wait, FIRST_COMPLETED
    return wait(futures, return_when=FIRST_COMPLETED)

def _process(path):
    name = os.path.basename(path)
    try:
        data = parse_file(path)
    except Exception as e:
        data = {"format": "Не определён", "status": "Ошибка чтения", "details": str(e)}
    fields = {k: data.get(k) for k in ("format", "width", "height", "dpi_x", "dpi_y", "bits_per_pixel", "bits_per_channel", "compression", "status", "details")}
    return ImageRecord(name=name, path=path, **fields)
