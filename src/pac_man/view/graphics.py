import os
import time
import ctypes
import mlx

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
    buffer, bpp, size_line, endian = m.mlx_get_data_addr(img)

    # Calcoliamo la dimensione totale del buffer
    buffer_size = screen_height * size_line
    
    # Creiamo un "Puntatore C" che punta alla stessa memoria del bytearray Python.
    # Facendolo qui, lo calcoliamo UNA SOLA VOLTA (massime prestazioni).
    c_buffer = (ctypes.c_char * buffer_size).from_buffer(buffer)

    def put_pixel(x: int, y: int, color: int) -> None:
        """Write a single pixel into the image buffer at (x, y)."""
        if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
            return
        offset = (y * size_line) + (x * (bpp // 8))
        buffer[offset]     = color & 0xFF           # Blue channel
        buffer[offset + 1] = (color >> 8) & 0xFF    # Green channel
        buffer[offset + 2] = (color >> 16) & 0xFF   # Red channel
        buffer[offset + 3] = 0xFF                   # Alpha (fully opaque)

    def clear_screen() -> None:
        """Azzera la memoria video istantaneamente usando il puntatore C."""
        ctypes.memset(c_buffer, 0, buffer_size)

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

    # Hook the window close button
    m.mlx_hook(win_ptr, EVENT_DESTROY, 0, close_game, None)
    m.mlx_hook(win_ptr, EVENT_DESTROY, STRUCTURE_NOTIFY_MASK, close_game, None)
    m.mlx_hook(win_ptr, EVENT_CLIENT_MESSAGE, 0, close_game, None)
    m.mlx_hook(win_ptr, EVENT_CLIENT_MESSAGE, STRUCTURE_NOTIFY_MASK, close_game, None)

    # Hook keyboard events
    m.mlx_key_hook(win_ptr, on_key, None)

    # ========================================================
    # STATO DELL'ANIMAZIONE
    # ========================================================
    anim = {
        "x": 50.0,
        "y": 150.0,
        "size": 40,
        "vx": 180.0,      
        "vy": 120.0,      
        "last_time": time.time(),
        "color": rgb_to_mlx(255, 255, 0),
        "target_fps": 60,
    }

    def update_game(data: object) -> int:
        current_time = time.time()
        dt = current_time - anim["last_time"]
        frame_duration = 1.0 / anim["target_fps"]

        # Limita i FPS per evitare di sovraccaricare X11 e causare sfarfallio
        if dt < frame_duration:
            time.sleep(0.001)
            return 0

        anim["last_time"] = current_time

        # 1. Movimento basato sul Delta Time
        anim["x"] += anim["vx"] * dt
        anim["y"] += anim["vy"] * dt

        # 2. Rimbalzi
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

        # 3. Pulisci il buffer istantaneamente tramite ctypes
        clear_screen()

        # 4. Disegna l'oggetto nella nuova posizione
        draw_rect(int(anim["x"]), int(anim["y"]), anim["size"], anim["size"], anim["color"])

        # 5. Flush a video
        m.mlx_put_image_to_window(mlx_ptr, win_ptr, img, 0, 0)
        
        # 6. Disegno del testo (chiamato DOPO il put_image per ridurre il tremolio)
        m.mlx_string_put(mlx_ptr, win_ptr, 10, 10, 0xFFFFFF, "PAC-MAN 42")
        return 0

    # Avvia il loop
    m.mlx_loop_hook(mlx_ptr, update_game, None)

    print("Window running. Press ESC, 'q', or click 'X' to exit.")
    m.mlx_loop(mlx_ptr)


if __name__ == "__main__":
    graphic_mlx()