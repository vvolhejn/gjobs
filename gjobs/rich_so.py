# [
#     Segment('└──────────────────────────┘', Style()),
#     Segment('                                                                         ',)
# ]

# [
#     Segment(
#         '
# ',
#     )
# ]

# [
#     Segment('│', Style()),
#     Segment(' ', Style()),
#     Segment(
#         '37',
#         Style(color=Color('cyan', ColorType.STANDARD, number=6), bold=True, italic=False)
#     ),
#     Segment('                      ', Style()),
#     Segment(' ', Style()),
#     Segment('│', Style()),
#     Segment('                                                                         ',)
# ]

# console.print(layout)

from collections import deque
import os
import time
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.console import Console


def generate_table(rows):
    layout = Layout()
    console = Console()

    table = Table()
    table.add_column('Time')
    table.add_column('Message')

    rows = list(rows)

    # This would also get the height:
    # render_map = layout.render(console, console.options)
    # render_map[layout].region.height
    n_rows = os.get_terminal_size()[1]

    while n_rows >= 0:
        table = Table()
        table.add_column('Time')
        table.add_column('Message')

        for row in rows[-n_rows:]:
            table.add_row(*row)

        layout.update(table)

        render_map = layout.render(console, console.options)

        if len(render_map[layout].render[-1]) > 2:
            # The table is overflowing (see explanation below)
            n_rows -= 1
        else:
            break

    return table


width, height = os.get_terminal_size()
messages = deque(maxlen=height-4)  # save space for header and footer

with Live(generate_table(messages), refresh_per_second=5) as live:
    for i in range(100):
        time.sleep(0.2)
        messages.append((time.asctime(), f'Event {i:03d}'))
        live.update(generate_table(messages))