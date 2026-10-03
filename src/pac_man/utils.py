def pixel_to_cell(
    coords: tuple[float | int, float | int],
    offsets: tuple[int, int],
    tile_size: int,
) -> tuple[int, int]:
    return (
        int((coords[0] - offsets[0]) // tile_size),
        int((coords[1] - offsets[1]) // tile_size),
    )


def cell_to_pixel(
    coords: tuple[int, int],
    offsets: tuple[int, int],
    tile_size: int,
) -> tuple[int, int]:
    return (
        offsets[0] + coords[0] * tile_size,
        offsets[1] + coords[1] * tile_size,
    )


def center_in_pixel(
    coords: tuple[float | int, float | int], tile_size: int, size: int
) -> tuple[int, int]:
    return (
        int(coords[0] + (tile_size - size) // 2),
        int(coords[1] + (tile_size - size) // 2)
    )
