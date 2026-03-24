import dataclasses
import textwrap
from datetime import datetime, timedelta

seed_id = 0


def next_id():
    global seed_id
    seed_id += 1
    return f'id_{seed_id}'


spacer = "    "


@dataclasses.dataclass
class Diagram:
    pass


@dataclasses.dataclass
class DiagramItem:
    title: str
    id: str = dataclasses.field(default_factory=next_id)
    next: list[('DiagramItem', str | None)] = dataclasses.field(default_factory=list)

    def add_next(self, node: 'DiagramItem', label: str = None) -> 'DiagramItem':
        self.next.append((node, label))
        return self

    def render_id(self) -> str:
        ...

    def render_body(self) -> [str]:
        return self._render_nodes(self.next)

    def _render_nodes(self, nodes) -> [str]:
        lines = []
        for node, label in nodes:
            lines.append(node.render_id())
            if label:
                lines.append(f'{self.id} -->|"{label}"| {node.id}')
            else:
                lines.append(f'{self.id} --> {node.id}')
            lines.extend(node.render_body())
        return lines


@dataclasses.dataclass
class FCCondition(DiagramItem):
    false_nodes: list[(DiagramItem, str | None)] = dataclasses.field(default_factory=list)

    def add_next(self, node: 'DiagramItem', label: str = None) -> 'DiagramItem':
        self.next.append((node, label or "True"))
        return self

    def render_id(self) -> str:
        return f'{self.id}{{\""{self.title}"\"}}'

    def render_body(self) -> [str]:
        lines = []
        lines.extend(self._render_nodes(self.false_nodes))
        lines.extend(self._render_nodes(self.next))
        return lines


@dataclasses.dataclass
class FCEdge(DiagramItem):

    def render_id(self) -> str:
        return f'{self.id}["{self.title}"]'


@dataclasses.dataclass
class Flowchart(FCEdge):
    end: DiagramItem = None

    def __post_init__(self):
        self.end = FCEdge(title="End")

    def to_graph(self) -> str:
        lines = ['flowchart TD', self.render_id()]
        lines.extend(self.render_body())
        return '\n'.join(lines)


@dataclasses.dataclass
class FlowchartBuilder:
    title: str
    nodes: list[DiagramItem] = dataclasses.field(default_factory=list)
    flowchart: Flowchart = None

    def __post_init__(self):
        self.flowchart = Flowchart(title=self.title)
        self.nodes.append(self.flowchart)

    def push(self, node: DiagramItem) -> 'FlowchartBuilder':
        self.nodes.append(node)
        return self

    def pop(self) -> 'FlowchartBuilder':
        if len(self.nodes) > 1:
            self.nodes.pop()
        return self

    def peek(self) -> DiagramItem:
        return self.nodes[-1]

    def add_edge(self, edge, link_label=None) -> 'FlowchartBuilder':
        self.peek().add_next(edge, link_label)
        self.push(edge)
        return self

    def create_edge(self, title, link_label=None) -> 'FlowchartBuilder':
        edge = FCEdge(title=title)
        return self.add_edge(edge, link_label)

    def push_condition(self, title, link_label=None) -> 'FlowchartBuilder':
        edge = FCCondition(title=title)
        edge.false_nodes.append((self.flowchart.end, "False"))

        self.peek().add_next(edge, link_label)
        self.push(edge)
        return self


@dataclasses.dataclass
class GanttTask:
    name: str
    start_datetime: datetime
    duration: timedelta
    id: str = dataclasses.field(default_factory=next_id)
    link: str = None
    active: bool = True
    done: bool = False
    critical: bool = False
    milestone: bool = False

    def to_lines(self) -> [str]:
        tags = ["crit"] if self.critical else []

        if self.milestone:
            tags.append("milestone")

        if self.done:
            tags.append("done")
        elif self.active:
            tags.append("active")
        tags = ",".join(tags)

        if tags:
            tags += ","

        lines = [f"{self.name}  :{tags} {self.id}, {self.start_datetime.isoformat()}, {self.duration.total_seconds()}s"]
        if self.link:
            lines.append(f'click {self.id} href "{self.link}"')
        return lines


@dataclasses.dataclass
class GanttSection:
    name: str
    parent: 'GanttDiagram' = None
    tasks: list[GanttTask] = dataclasses.field(default_factory=list)
    link: str = None

    def add_task(self, name: str, start_datetime: datetime, duration: timedelta, link: str = None,
                 active: bool = True, done: bool = False, critical: bool = False, milestone=False) -> 'GanttSection':
        self.tasks.append(
            GanttTask(name, start_datetime, duration, link=link, active=active,
                      done=done, critical=critical, milestone=milestone)
        )
        return self

    def to_lines(self) -> [str]:
        lines = [f"section {self.name}"]

        for task in self.tasks:
            lines.extend([f'{spacer}{line}' for line in task.to_lines()])

        if self.link:
            lines.append(f'click {self.name} href "{self.link}"')
        return lines

    def close(self):
        return self.parent


@dataclasses.dataclass
class GanttDiagram(Diagram):
    title: str
    display_mode_compact: bool = False
    sections: list = dataclasses.field(default_factory=list)
    today_marker: bool = True

    def append_section(self, section: GanttSection):
        section.parent = self
        self.sections.append(section)
        return section

    def add_section(self, name: str) -> GanttSection:
        return self.append_section(GanttSection(name=name))

    def to_graph(self) -> str:
        graph = "\n"
        if self.display_mode_compact:
            graph = """
            ---
            displayMode: compact
            ---
            """
            graph = f'\n{textwrap.dedent(graph).strip()}\n'

        graph += "gantt\n"
        graph += f"{spacer}title {self.title}\n"
        if self.today_marker:
            graph += f"{spacer}todayMarker on\n"
        for section in self.sections:
            graph += "\n"
            for line in section.to_lines():
                graph += f"{spacer}{line}\n"
        return graph
