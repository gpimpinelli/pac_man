from dataclasses import dataclass


@dataclass(frozen=True)
class MinimapMetrics:
    size: int = 200
    padding: int = 50
    tile_size: int = 10
    sprite_offset: int = 5


@dataclass(frozen=True)
class MenuMetrics:
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
    heart_size: int = 16
    heart_spacing: int = 4
    line_height: int = 20
    offset_from_bottom: int = 20
    inner_padding_x: int = 10


@dataclass(frozen=True)
class ViewLayout:
    main_tile_size: int
    sprite_offset: int
    finish_sprite_w: int
    finish_sprite_h: int
    minimap: MinimapMetrics
    menu: MenuMetrics
    hud: HudMetrics

    @classmethod
    def from_window_size(
        cls, width: int, height: int, main_tile_size: int = 48
    ) -> "ViewLayout":
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