import os
import mlx
import time
from enum import Enum, auto

# ==========================================
# COSTANTI E MAPPATURA TASTI
# ==========================================
KEY_ESC = 65307

EVENT_KEY_PRESS = 2
EVENT_DESTROY = 17
EVENT_CLIENT_MESSAGE = 33
KEY_PRESS_MASK = 1 << 0
STRUCTURE_NOTIFY_MASK = 1 << 17

class Direzione(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

MAPPA_TASTI = {
    65362: Direzione.UP,    # Freccia Su
    119:   Direzione.UP,    # w
    65364: Direzione.DOWN,  # Freccia Giù
    115:   Direzione.DOWN,  # s
    65361: Direzione.LEFT,  # Freccia Sinistra
    97:    Direzione.LEFT,  # a
    65363: Direzione.RIGHT, # Freccia Destra
    100:   Direzione.RIGHT  # d
}

def rgb_to_mlx(r: int, g: int, b: int) -> int:
    """Convert RGB (0-255) values to a 24-bit MLX integer color."""
    return (r << 16) | (g << 8) | b

# ==========================================
# FUNZIONE PRINCIPALE (MOTORE + GIOCO)
# ==========================================
def graphic_mlx() -> None:
    # 1. Inizializza MLX e Finestra
    m = mlx.Mlx()
    mlx_ptr = m.mlx_init()
    screen_width, screen_height = 1024, 764
    win_ptr = m.mlx_new_window(mlx_ptr, screen_width, screen_height, "Pac-Man 42")

    # 2. Inizializza l'Immagine e il Buffer per il rendering super-veloce
    img = m.mlx_new_image(mlx_ptr, screen_width, screen_height)
    data, bpp, size_line, _ = m.mlx_get_data_addr(img)
    bytes_per_pixel = bpp // 8
    buffer_size = screen_height * size_line

    # 3. Prepara il colore di sfondo (Blu notte: 0x050522) in byte per cancellazione rapida
    # In memoria i canali sono B, G, R, A (quindi 0x22, 0x05, 0x05, 0xFF)
    bg_bytes = bytes([0x22, 0x05, 0x05, 0xFF])
    _bg_buffer = bg_bytes * (buffer_size // bytes_per_pixel)

    # --- FUNZIONI GRAFICHE OTTIMIZZATE ---
    def clear_buffer() -> None:
        """Svuota lo schermo applicando il colore di sfondo in un solo colpo (velocissimo)."""
        data[0:buffer_size] = _bg_buffer

    def draw_rect_fast(x: int, y: int, w: int, h: int, color: int) -> None:
        """Disegna il quadrato manipolando direttamente i byte (niente loop lenti in Python)."""
        b_ch = color & 0xFF
        g_ch = (color >> 8) & 0xFF
        r_ch = (color >> 16) & 0xFF

        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(x + w, screen_width), min(y + h, screen_height)
        actual_w = x1 - x0
        
        if actual_w <= 0 or y1 <= y0:
            return

        row_bytes = bytes([b_ch, g_ch, r_ch, 0xFF] * actual_w)
        row_len = actual_w * bytes_per_pixel

        for row in range(y0, y1):
            start = row * size_line + x0 * bytes_per_pixel
            data[start: start + row_len] = row_bytes

    # --- FUNZIONI DI GIOCO ---
    def close_game(*args: object) -> None:
        print("Closing game...")
        m.mlx_destroy_window(mlx_ptr, win_ptr)
        os._exit(0)

    def on_key_press(keycode: int, *args: object) -> int:
        if keycode in (KEY_ESC, 27, ord('q'), ord('Q')):
            close_game()
            
        action = MAPPA_TASTI.get(keycode)
        if action:
            anim["last_key"] = action
            if not anim["started"]:
                anim["started"] = True
                anim["last_time"] = time.perf_counter() # Usa il timer ad alta precisione
        return 0

    # STATO DELL'ANIMAZIONE
    anim = {
        "x": 50.0,
        "y": 150.0,
        "size": 40,
        "speed": 180.0,
        "last_key": None,
        "started": False,
        "last_time": time.perf_counter(),
        "color": rgb_to_mlx(255, 255, 0),
        "target_fps": 60,
    }
    
    def update_game(data_param: object) -> int:
        current_time = time.perf_counter()
        dt = current_time - anim["last_time"]
        frame_duration = 1.0 / anim["target_fps"]

        # Se il frame non è pronto, esce SUBITO senza bloccare X11 (niente sleep!)
        if dt < frame_duration:
            return 0

        anim["last_time"] = current_time

        # 1. Aggiorna Posizione
        if anim["started"]:
            match anim["last_key"]:
                case Direzione.UP:
                    anim["y"] -= anim["speed"] * dt
                case Direzione.DOWN:
                    anim["y"] += anim["speed"] * dt
                case Direzione.LEFT:
                    anim["x"] -= anim["speed"] * dt
                case Direzione.RIGHT:
                    anim["x"] += anim["speed"] * dt

        # 2. Collisioni (si ferma al bordo)
        if anim["x"] <= 0:
            anim["x"] = 0.0
            anim["last_key"] = None
        elif anim["x"] + anim["size"] >= screen_width:
            anim["x"] = float(screen_width - anim["size"])
            anim["last_key"] = None

        if anim["y"] <= 0:
            anim["y"] = 0.0
            anim["last_key"] = None
        elif anim["y"] + anim["size"] >= screen_height:
            anim["y"] = float(screen_height - anim["size"])
            anim["last_key"] = None

        # 3. Sincronizza per evitare sfarfallii e strappi a schermo
        m.mlx_sync(mlx_ptr, mlx.Mlx.SYNC_IMAGE_WRITABLE, img)
        
        # 4. Disegna
        clear_buffer()
        draw_rect_fast(int(anim["x"]), int(anim["y"]), anim["size"], anim["size"], anim["color"])
        
        # 5. Invia alla finestra
        m.mlx_put_image_to_window(mlx_ptr, win_ptr, img, 0, 0)
        return 0

    # --- REGISTRAZIONE HOOK ---
    m.mlx_hook(win_ptr, EVENT_DESTROY, 0, close_game, None)
    m.mlx_hook(win_ptr, EVENT_DESTROY, STRUCTURE_NOTIFY_MASK, close_game, None)
    m.mlx_hook(win_ptr, EVENT_CLIENT_MESSAGE, 0, close_game, None)
    m.mlx_hook(win_ptr, EVENT_CLIENT_MESSAGE, STRUCTURE_NOTIFY_MASK, close_game, None)
    
    m.mlx_hook(win_ptr, EVENT_KEY_PRESS, KEY_PRESS_MASK, on_key_press, None)
    m.mlx_loop_hook(mlx_ptr, update_game, None)

    print("Pac-Man Engine Running. Premi frecce o WASD per muoverti. ESC per uscire.")
    m.mlx_loop(mlx_ptr)

if __name__ == "__main__":
    graphic_mlx()