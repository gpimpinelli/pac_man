"""Layout metrics and geometry configurations for the user interface."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MinimapMetrics:
    """Metrics and pixel dimensions for rendering the minimap.

    Attributes:
        size (int): Dimension of minimap box.
        padding (int): Screen margin padding.
        tile_size (int): Pixel size for each minimap cell.
        sprite_offset (int): Centering offset for entity dots.
    """

    size: int = 200
    padding: int = 50
    tile_size: int = 10
    sprite_offset: int = 5


@dataclass(frozen=True)
class MenuMetrics:
    """Dimensions and spacing parameters for menu screens.

    Attributes:
        padding_x (int): Horizontal margin offset.
        padding_y (int): Vertical margin offset.
        btn_w (int): Button rectangle width.
        btn_h (int): Button rectangle height.
        gap (int): Spacing between menu items.
        line_h_normal (int): Line height for regular text.
        line_h_highscores (int): Line height for highscore lines.
        char_width_approx (int): Estimated monospace character width.
    """

    padding_x: int
    padding_y: int
    btn_w: int = 200
    btn_h: int = 50
    gap: int = 20
    line_h_normal: int = 20
    line_h_highscores: int = 30
    char_width_approx: int = 10


@dataclass(frozen=True)
class HudMetrics:
    """Positioning and spacing parameters for the game heads-up display.

    Attributes:
        heart_size (int): Width and height of life heart icon.
        heart_spacing (int): Gap between life icons.
        line_height (int): Text line vertical spacing.
        offset_from_bottom (int): Margin from bottom window border.
        inner_padding_x (int): Inner padding offset.
    """

    heart_size: int = 16
    heart_spacing: int = 4
    line_height: int = 20
    offset_from_bottom: int = 20
    inner_padding_x: int = 10


@dataclass(frozen=True)
class ViewLayout:
    """Consolidated UI layout geometry and metrics container.

    Attributes:
        main_tile_size (int): Size of primary maze grid tiles in pixels.
        sprite_offset (int): Visual centering sprite pixel offset.
        finish_sprite_w (int): Width of game over / banner sprite.
        finish_sprite_h (int): Height of game over / banner sprite.
        minimap (MinimapMetrics): Minimap layout metrics.
        menu (MenuMetrics): Menu layout metrics.
        hud (HudMetrics): Heads-up display metrics.
    """

    main_tile_size: int
    sprite_offset: int
    finish_sprite_w: int
    finish_sprite_h: int
    minimap: MinimapMetrics
    menu: MenuMetrics
    hud: HudMetrics

    @classmethod
    def from_window_size(
        cls, width: int, height: int, main_tile_size: int = 38
    ) -> "ViewLayout":
        """Compute responsive layout metrics based on window resolution.

        Args:
            width (int): Target window width in pixels.
            height (int): Target window height in pixels.
            main_tile_size (int): Primary tile dimension in pixels.

        Returns:
            ViewLayout: Computed layout structure.
        """
        return cls(
            main_tile_size=main_tile_size,
            sprite_offset=16,
            finish_sprite_w=300,
            finish_sprite_h=129,
            minimap=MinimapMetrics(),
            menu=MenuMetrics(
                padding_x=(width // 4) + 100,
                padding_y=(height // 4) - 50,
            ),
            hud=HudMetrics(),
        )
