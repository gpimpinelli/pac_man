import os
import mlx

# X11 Keycodes
KEY_ESC = 65307  # Escape key on Linux/X11

# X11 Event IDs and Masks
EVENT_DESTROY = 17         # DestroyNotify event
EVENT_CLIENT_MESSAGE = 33  # ClientMessage event (WM_DELETE_WINDOW from window manager)
STRUCTURE_NOTIFY_MASK = 1 << 17


def graphic_mlx() -> None:
    # 1. Initialize MLX wrapper
    m = mlx.Mlx()

    # 2. Initialize display connection
    mlx_ptr = m.mlx_init()
    screen_width, screen_height = 400, 400

    # 3. Create window
    win_ptr = m.mlx_new_window(mlx_ptr, screen_width, screen_height, "Pac-Man 42")

    # 4. Clean exit callback
    def close_game(*args: object) -> None:
        print("Closing game...")
        m.mlx_destroy_window(mlx_ptr, win_ptr)
        os._exit(0)

    # 5. Keyboard callback
    def on_key(keycode: int, *args: object) -> None:
        print(f"Key pressed: {keycode}")
        if keycode in (KEY_ESC, 27, ord('q'), ord('Q')):
            close_game()

    # Hook the window close button ('X'):
    # - Event 17: DestroyNotify (with mask 0 and StructureNotifyMask)
    # - Event 33: ClientMessage / WM_DELETE_WINDOW (sent by WSLg / X11 window manager)
    m.mlx_hook(win_ptr, EVENT_DESTROY, 0, close_game, None)
    m.mlx_hook(win_ptr, EVENT_DESTROY, STRUCTURE_NOTIFY_MASK, close_game, None)
    m.mlx_hook(win_ptr, EVENT_CLIENT_MESSAGE, 0, close_game, None)
    m.mlx_hook(win_ptr, EVENT_CLIENT_MESSAGE, STRUCTURE_NOTIFY_MASK, close_game, None)

    # Hook keyboard events
    m.mlx_key_hook(win_ptr, on_key, None)

    print("Window running. Press ESC, 'q', or click 'X' to exit.")
    m.mlx_loop(mlx_ptr)


if __name__ == "__main__":
    graphic_mlx()