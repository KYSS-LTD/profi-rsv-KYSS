from pathlib import Path

from jinja2 import Environment, FileSystemLoader


class PromptManager:
    """Грузит .j2-промпты и рендерит их с контекстом."""

    def __init__(self, prompts_dir: str | Path | None = None):
        prompts_dir = Path(prompts_dir) if prompts_dir else Path(__file__).parent / "prompts"
        self.env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, name: str, **ctx) -> str:
        return self.env.get_template(f"{name}.j2").render(**ctx)
