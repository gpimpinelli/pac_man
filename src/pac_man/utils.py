def pixel_to_cell(x: int, y: int, offset_x: int, offset_y: int, tile_size: int) -> tuple[int, int]:
    return (
        int((x - offset_x) // tile_size),
        int((y - offset_y) // tile_size)
    )

def cell_to_pixel(
    cell_x: int,
    cell_y: int,
    offset_x: int,
    offset_y: int,
    tile_size: int
) -> tuple[int, int]:
    return (
        offset_x + cell_x * tile_size,
        offset_y + cell_y * tile_size
    )

def center_in_pixel(
    cx: int,
    cy: int,
    tile_size: int,
    size: int
) -> tuple[int, int]:
    return (
        cx + (tile_size - size) // 2,
        cy + (tile_size - size) // 2
    )

