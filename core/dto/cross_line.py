class CrossLine:
    def __init__(self, width: float = None, color: str = None, opacity: float = None) -> None:
        self.width: float = width if width else 2.0
        self.color: str = color if color else "#00FF00"
        self.opacity: float = opacity if opacity else 0.5

    def set_style(self, width: float, color: str, opacity: float) -> None:
        self.width = width
        self.color = color
        self.opacity = opacity

    def __str__(self):
        return f"CrossLine(width={self.width}, color={self.color}, opacity={self.opacity})"
