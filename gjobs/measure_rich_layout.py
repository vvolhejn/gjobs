from rich.console import Console
import rich
from rich.highlighter import ReprHighlighter
from rich.layout import Layout
from rich import print as pprint
from rich.panel import Panel

console = Console()

content_layout = Layout()

top = rich.layout.Layout(name="foo")
bot = rich.layout.Layout(name="bar", ratio=2)

content_layout.split_column(top, bot)
pprint(content_layout)

rm = content_layout.render(console, console.options)
pprint(rm[top].region)
pprint(rm[bot].region.width)


text = "a" * 272

highlighted = ReprHighlighter()(text)
panel = Panel(highlighted)

print(panel.__rich_measure__(console, console.options))

print(console.measure(
                highlighted, options=console.options.update_width(console.width - 2)
            ))

lines = console.render_lines(highlighted, console.options.update_width(console.width - 2))
print(len(lines))