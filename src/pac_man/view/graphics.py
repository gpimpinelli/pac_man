import os
import mlx
import time

# X11 Keycodes
KEY_ESC = 65307  # Escape key on Linux/X11

# X11 Event IDs and Masks
EVENT_DESTROY = 17          # DestroyNotify event
EVENT_CLIENT_MESSAGE = 33   # ClientMessage event (WM_DELETE_WINDOW from window manager)
STRUCTURE_NOTIFY_MASK = 1 << 17




def rgb_to_mlx(r: int, g: int, b: int) -> int:
    """Convert RGB (0-255) values to a 24-bit MLX integer color."""
    return (r << 16) | (g << 8) | b


def graphic_mlx() -> None:
    """Main graphics function: opens a window and draws using an image buffer."""
    # 1. Initialize MLX wrapper
    m = mlx.Mlx()

    # 2. Initialize display connection
    mlx_ptr = m.mlx_init()
    screen_width, screen_height = 400, 400

    # 3. Create window
    win_ptr = m.mlx_new_window(mlx_ptr, screen_width, screen_height, "Pac-Man 42")

    # 4. Create an off-screen image buffer (same size as the window)
    img = m.mlx_new_image(mlx_ptr, screen_width, screen_height)

    # 5. Get the raw pixel buffer from the image
    # Returns: (buffer, bits_per_pixel, size_line, endian)
    buffer, bpp, size_line, endian = m.mlx_get_data_addr(img)

    def put_pixel(x: int, y: int, color: int) -> None:
        """Write a single pixel into the image buffer at (x, y)."""
        # Bounds check: avoid writing outside the image
        if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
            return
        offset = (y * size_line) + (x * (bpp // 8))
        buffer[offset]     = color & 0xFF           # Blue channel
        buffer[offset + 1] = (color >> 8) & 0xFF    # Green channel
        buffer[offset + 2] = (color >> 16) & 0xFF   # Red channel
        buffer[offset + 3] = 0xFF                   # Alpha (fully opaque)

    def draw_line(x0: int, y0: int, x1: int, y1: int, color: int) -> None:
        """Draw a line using Bresenham's algorithm into the image buffer."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            put_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def draw_rect(x: int, y: int, width: int, height: int, color: int) -> None:
        """Draw a filled rectangle into the image buffer."""
        for row in range(y, y + height):
            for col in range(x, x + width):
                put_pixel(col, row, color)

    # 6. Clean exit callback
    def close_game(*args: object) -> None:
        print("Closing game...")
        m.mlx_destroy_window(mlx_ptr, win_ptr)
        os._exit(0)

    # 7. Keyboard callback
    def on_key(keycode: int, *args: object) -> None:
        print(f"Key pressed: {keycode}")
        if keycode in (KEY_ESC, 27, ord('q'), ord('Q')):
            close_game()

    # Hook the window close button ('X'):
    # - Event 17: DestroyNotify
    # - Event 33: ClientMessage / WM_DELETE_WINDOW (sent by WSLg window manager)
    m.mlx_hook(win_ptr, EVENT_DESTROY, 0, close_game, None)
    m.mlx_hook(win_ptr, EVENT_DESTROY, STRUCTURE_NOTIFY_MASK, close_game, None)
    m.mlx_hook(win_ptr, EVENT_CLIENT_MESSAGE, 0, close_game, None)
    m.mlx_hook(win_ptr, EVENT_CLIENT_MESSAGE, STRUCTURE_NOTIFY_MASK, close_game, None)

    # Hook keyboard events
    m.mlx_key_hook(win_ptr, on_key, None)
    # ========================================================
    # QUI DEFINISCI LO STATO DELL'ANIMAZIONE (prima di update_game)
    # ========================================================
    anim = {
        "x": 50.0,
        "y": 150.0,
        "size": 40,
        "vx": 180.0,      # velocità orizzontale (pixel/secondo)
        "vy": 120.0,      # velocità verticale (pixel/secondo)
        "last_time": time.time(),
        "color": rgb_to_mlx(255, 255, 0),
        "target_fps": 60,
    }


    def update_game(data: object) -> int:
        current_time = time.time()
        dt = current_time - anim["last_time"]

        frame_duration = 1.0 / anim["target_fps"]
        if dt < frame_duration:
            # Rilascia un attimo la CPU per non saturare X11
            time.sleep(0.001)
            return 0

        anim["last_time"] = current_time

        # 1. Aggiorna la posizione
        anim["x"] += anim["vx"] * dt
        anim["y"] += anim["vy"] * dt

        # 2. Gestione collisione con i bordi (rimbalzo)
        if anim["x"] <= 0:
            anim["x"] = 0
            anim["vx"] *= -1
        elif anim["x"] + anim["size"] >= screen_width:
            anim["x"] = screen_width - anim["size"]
            anim["vx"] *= -1

        if anim["y"] <= 0:
            anim["y"] = 0
            anim["vy"] *= -1
        elif anim["y"] + anim["size"] >= screen_height:
            anim["y"] = screen_height - anim["size"]
            anim["vy"] *= -1

        # 3. Pulisci il buffer (evita l'effetto scia)
        # Nota: invece di draw_rect puoi azzerare il buffer direttamente per velocità:
        # buffer[:] = b'\x00' * len(buffer)
        draw_rect(0, 0, screen_width, screen_height, 0x000000)

        # 4. Disegna l'oggetto nella nuova posizione
        draw_rect(int(anim["x"]), int(anim["y"]), anim["size"], anim["size"], anim["color"])

        # 5. Invia al server X11
        m.mlx_put_image_to_window(mlx_ptr, win_ptr, img, 0, 0)
        m.mlx_string_put(mlx_ptr, win_ptr, 10, 10, 0xFFFFFF, "PAC-MAN 42")
        return 0

    m.mlx_loop_hook(mlx_ptr, update_game, None)

    print("Window running. Press ESC, 'q', or click 'X' to exit.")
    m.mlx_loop(mlx_ptr)


if __name__ == "__main__":
    graphic_mlx()