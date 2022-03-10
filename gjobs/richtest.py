import random
import time

from rich.live import Live
from rich.table import Table
from blessed import Terminal

term = Terminal()


def generate_table() -> Table:
    """Make a new table."""
    table = Table()
    table.add_column("ID")
    table.add_column("Value")
    table.add_column("Status")

    for row in range(random.randint(2, 6)):
        value = random.random() * 100
        table.add_row(
            f"{row}", f"{value:3.2f}", "[red]ERROR" if value < 50 else "[green]SUCCESS"
        )
    return table


with term.cbreak(), term.hidden_cursor():
    with Live(generate_table(), refresh_per_second=4, screen=True) as live:
        for _ in range(40):
            time.sleep(0.4)
            live.update(generate_table())
