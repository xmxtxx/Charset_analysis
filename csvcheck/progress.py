from __future__ import annotations
import time
from .colors import Colors


def format_time(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds/60)}m {int(seconds%60)}s"
    return f"{int(seconds/3600)}h {int((seconds%3600)/60)}m"


class ProgressBar:
    """Simple progress bar for terminal output."""

    def __init__(self, total: int, width: int = 50, title: str = "Progress"):
        self.total = total
        self.width = width
        self.title = title
        self.current = 0
        self.start_time = time.time()

    def update(self, current: int, item_name: str = "") -> None:
        self.current = current
        if self.total == 0:
            return
        progress = self.current / self.total
        filled = int(self.width * progress)
        elapsed = time.time() - self.start_time
        if self.current > 0:
            avg_time = elapsed / self.current
            remaining = avg_time * (self.total - self.current)
            time_str = f"ETA: {format_time(remaining)}"
        else:
            time_str = "Calculating..."
        total_time_str = f"Elapsed: {format_time(elapsed)}"
        bar = '█' * filled + '░' * (self.width - filled)
        max_item_len = 40
        if len(item_name) > max_item_len:
            item_name = item_name[: max_item_len - 3] + "..."
        print(
            f"\r{Colors.CYAN}{self.title}:{Colors.NC} "
            f"[{Colors.GREEN}{bar}{Colors.NC}] "
            f"{Colors.YELLOW}{self.current}/{self.total}{Colors.NC} "
            f"({progress*100:.1f}%) {Colors.DIM}{time_str}{Colors.NC} "
            f"{Colors.DIM}{total_time_str}{Colors.NC} "
            f"{Colors.BLUE}{item_name}{Colors.NC}",
            end="",
            flush=True,
        )
        if self.current == self.total:
            print()

    def finish(self) -> None:
        self.update(self.total, "Complete!")