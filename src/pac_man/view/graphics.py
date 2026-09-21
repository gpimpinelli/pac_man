import os
import mlx
import time

# X11 Keycodes
KEY_ESC = 65307  # Escape key on Linux/X11

# --- EVENTI TASTIERA ---
EVENT_KEY_PRESS = 2         # Tasto premuto
EVENT_KEY_RELEASE = 3       # Tasto rilasciato
KEY_PRESS_MASK = 1 << 0     # Filtro per i tasti premuti
KEY_RELEASE_MASK = 1 << 1   # Filtro per i tasti rilasciati

# --- EVENTI FINESTRA (I tuoi originali) ---
EVENT_DESTROY = 17          # Finestra distrutta (clic sulla X)
EVENT_CLIENT_MESSAGE = 33   # Messaggio di chiusura dal sistema operativo
STRUCTURE_NOTIFY_MASK = 1 << 17

from enum import Enum, auto

class Direzione(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

MAPPA_TASTI = {
    65362: Direzione.UP,       # Freccia Su
    119:   Direzione.UP,       # w
    
    65364: Direzione.DOWN,      # Freccia Giù
    115:   Direzione.DOWN,      # s
    
    65361: Direzione.LEFT, # Freccia Sinistra
    97:    Direzione.LEFT, # a
    
    65363: Direzione.RIGHT,   # Freccia Destra
    100:   Direzione.RIGHT    # d
}

# ---------------------------------------------------------------------------------



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
    def on_key_press(keycode: int, *args: object) -> int:
        # Opzionale: per fare debug e vedere il codice nella console
        print(f"Key pressed: {keycode}")
        
        # 1. Controlla prima i tasti di uscita
        if keycode in (KEY_ESC, 27, ord('q'), ord('Q')):
            close_game()
            
        # 2. Se non è uscito, controlla se è un tasto di movimento
        action = MAPPA_TASTI.get(keycode)
        if action:
            anim["direction"] = action  # Cambia direzione
            anim["started"] = True      # Sblocca il gioco
            anim["last_time"] = time.time()
        return 0


    # ========================================================
    # QUI DEFINISCI LO STATO DELL'ANIMAZIONE (prima di update_game)
    # ========================================================
    anim = {
        "x": 50.0,
        "y": 150.0,
        "size": 40,
        "speed": 100.0,
        "last_key" : None,
        "started": False,
        "last_time": time.time(),
        "color": rgb_to_mlx(255, 255, 0),
        "target_fps": 59,
    }
    
    
    def update_game(data: object) -> int:
        if not anim["started"]:
            return 0
        current_time = time.time()
        dt = current_time - anim["last_time"]

        frame_duration = 1.0 / anim["target_fps"]
        if dt < frame_duration:
            # Rilascia un attimo la CPU per non saturare X11
            time.sleep(0.001)
            return 0

        anim["last_time"] = current_time

        # 1. Aggiorna la posizione in base a last_key
        match anim["last_key"]:
            case Direzione.UP:
                anim["y"] -= anim["speed"] * dt
            case Direzione.DOWN:
                anim["y"] += anim["speed"] * dt
            case Direzione.LEFT:
                anim["x"] -= anim["speed"] * dt
            case Direzione.RIGHT:
                anim["x"] += anim["speed"] * dt

        # 2. Gestione collisione con i bordi (rimbalzo)
        if anim["x"] <= 1:
            anim["x"] = 0
            anim["last_key"] = None
        elif anim["x"] + anim["size"] >= screen_width:
            anim["x"] = screen_width - anim["size"] - 1
            anim["last_key"] = None

        if anim["y"] <= 1:
            anim["y"] = 0
            anim["last_key"] = None
        elif anim["y"] + anim["size"] >= screen_height:
            anim["y"] = screen_height - anim["size"] - 1
            anim["last_key"] = None
          
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

        # Hook the window close button ('X'):
    # - Event 17: DestroyNotify
    # - Event 33: ClientMessage / WM_DELETE_WINDOW (sent by WSLg window manager)
    m.mlx_hook(win_ptr, EVENT_DESTROY, 0, close_game, None)
    m.mlx_hook(win_ptr, EVENT_DESTROY, STRUCTURE_NOTIFY_MASK, close_game, None)
    m.mlx_hook(win_ptr, EVENT_CLIENT_MESSAGE, 0, close_game, None)
    m.mlx_hook(win_ptr, EVENT_CLIENT_MESSAGE, STRUCTURE_NOTIFY_MASK, close_game, None)

    # Hook keyboard events
    m.mlx_hook(win_ptr, EVENT_KEY_PRESS, KEY_PRESS_MASK, on_key_press, None)
    m.mlx_loop_hook(mlx_ptr, update_game, None)

    print("Window running. Press ESC, 'q', or click 'X' to exit.")
    m.mlx_loop(mlx_ptr)


if __name__ == "__main__":
    graphic_mlx()