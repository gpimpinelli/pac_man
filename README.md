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
## 1) insert GameState.CHEAT
## 5) cheat mode (1 no wall collision for player(just the wall inside), 2 super gum infinito, 3) infinity lives 4) to be able to shoot 5) for ecer super 6) caricare direttamente un livello
## inserire nelle view stat a che livello siamo
## scegliere la palette di colori e inserirli in un enum
## 7) find sprites and cut the background (wall player and ghost)
## capire come facilitare i livelli piu avanti
1. Aumentare il tempo dei Super Pac Gum

È la soluzione più semplice a livello di codice, ma cambia il ritmo di gioco.

    Pro: Modifichi solo una variabile (es. duration = 5 + level). Zero sforzo tecnico.

    Contro: Se l'invincibilità dura troppo, il gioco diventa noioso. Passerai la maggior parte del tempo a inseguire fantasmi lenti e blu anziché scappare.

    Il trucco del design: Nel Pac-Man originale facevano il contrario. Per rendere il gioco difficilissimo, ai livelli alti il tempo di invincibilità scendeva a zero.

2. Aumentare il numero di Super Pac Gum

Aggiungere più palloni speciali in punti casuali o strategici.

    Pro: Dà al giocatore più "ancore di salvezza" sparse per la mappa, permettendogli di sopravvivere anche contro fantasmi velocissimi.

    Contro: Richiede di mettere mano al codice che genera la mappa (la tua matrice o il file di testo). Devi trovare un modo per sostituire alcuni pallini normali con quelli speciali senza rompere la simmetria del labirinto.

3. Aumentare il numero di fantasmi (La scelta più divertente)

Invece di avere solo i classici 4, potresti aggiungerne un quinto al livello 3, un sesto al livello 5, e così via.

    L'impatto sul gioco: Più fantasmi ci sono, più percorsi vengono bloccati. Il labirinto diventa affollato. Anche se i fantasmi non sono velocissimi, sarai costretto a fare continui cambi di direzione per non farti accerchiare.

    Come si fa: Nel punto in cui fai lo spawn dei fantasmi all'inizio del livello (probabilmente hai un ciclo for), ti basta legare il numero al livello attuale:
    Python

    # Partiamo da 4 fantasmi e ne aggiungiamo 1 ogni 2 livelli
    numero_fantasmi = 4 + (self.current_level_index // 2) 

    for _ in range(numero_fantasmi):
        # codice che crea e posiziona il fantasma

Il mix ideale?
Potresti unire le cose: mantieni la formula in cui i fantasmi diventano un po' più veloci (speed = 90 * 1.05 ** level con il tetto massimo a 120), e aggiungi un fantasma extra ogni 3 livelli. Così la difficoltà sale in due modi diversi: prima diventano più rapidi, poi diventano un vero e proprio sciame.


