# pac_man

# Project

- Cell
    every cell have his params
    - hexa
    - coordinates (x, y)
    - is_entry
    - have_pacgum
    - have_super_pacgum

The Spriters Resource

surface game maker

3/4, muri bassi, ombra = hitbox, sprites pacman a ombra hitbox - py, ridimenzionare la cella in un potenza di 2, oggetti con lo spessore per primo


# TODO
## 1) insert enum with GameState but not insert in flow of program
        aggiunto enum in game_model
        flow program con menu -> scelta -> gioco e torni al menu se lives < 0 
## 2) find the sprites for name of button  (restart, settings exit)
## 3) enum for check if click botton
        questo ho usato una variabile di selezione
        che in base al valore assunto genera un risultato
        ho usato match in on_key_press
## 4) insert lives and score bottom the minimap
## 5) cheat mode (1 no wall collision for player(just the wall inside), 2 super gum infinito, 3) infinity lives 4) to be able to shoot)
## 6) a map page for insert a name and score
## 7) find sprites and cut the background (wall player and ghost)
## 8) insert config json in flow of program