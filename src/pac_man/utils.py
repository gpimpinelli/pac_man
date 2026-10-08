"""Utility coordinate transformation functions for grid and pixel positions."""


def pixel_to_cell(
    coords: tuple[float | int, float | int],
    offsets: tuple[int, int],
    tile_size: int,
) -> tuple[int, int]:
    """Convert screen pixel coordinates to grid cell coordinates.

    Args:
        coords: Tuple of (x, y) pixel coordinates.
        offsets: Tuple of (offset_x, offset_y) grid screen offsets.
        tile_size: Size of a single grid tile in pixels.

    Returns:
        tuple[int, int]: Corresponding (col, row) grid coordinates.
    """
    return (
        int((coords[0] - offsets[0]) // tile_size),
        int((coords[1] - offsets[1]) // tile_size),
    )


def cell_to_pixel(
    coords: tuple[int, int],
    offsets: tuple[int, int],
    tile_size: int,
) -> tuple[int, int]:
    """Convert grid cell coordinates to screen pixel coordinates.

    Args:
        coords: Tuple of (col, row) grid coordinates.
        offsets: Tuple of (offset_x, offset_y) grid screen offsets.
        tile_size: Size of a single grid tile in pixels.

    Returns:
        tuple[int, int]: Corresponding (x, y) pixel coordinates.
    """
    return (
        offsets[0] + coords[0] * tile_size,
        offsets[1] + coords[1] * tile_size,
    )


def center_in_pixel(
    coords: tuple[float | int, float | int], tile_size: int, size: int
) -> tuple[int, int]:
    """Center an entity sprite within a tile cell.

    Args:
        coords: Tuple of (x, y) tile pixel coordinates.
        tile_size: Tile dimensions in pixels.
        size: Entity sprite dimensions in pixels.

    Returns:
        tuple[int, int]: Centered (x, y) pixel coordinates.
    """
    return (
        int(coords[0] + (tile_size - size) // 2),
        int(coords[1] + (tile_size - size) // 2),
    )
