# Version 0.1

import copy
import numpy as np
import time

class Game:
    def __init__(self):
        self.taille = 15
        self.state = [[0 for _ in range(self.taille)] for _ in range(self.taille)]
        self.condition_victoire = 5
        self.char = {0: '-', 1: 'X', 2: 'O'}
        self.joueur_actuel = None
        self.temps = None
        self.limite_sup_temps = 5
        self.limite_sup_pions = 60
        self.profondeur = 2 
        #On définit les patterns que l'IA doit reconnaitre pour savoir attaquer : 
        self.attaque = {
            (5, 0, True),
            (5, 0, False),
            (5, 1, True),
            (5, 1, False),
            (5, 2, True),
            (5, 2, False),
            (4, 1, True),
            (4, 2, True),
            (4, 2, False)
        }
        # On définit les menaces pour apprendre à l'IA à reconnaitre les patterns à privilegier : 
        self.menaces = {
            # Les coups qui mènent à une victoire sure
            (5, 0, True): 100000,
            (5, 0, False): 100000,
            (5, 1, True): 100000,
            (5, 1, False): 100000,
            (5, 2, True): 100000,
            (5, 2, False): 100000,
            #------------------------------------------------------
            #Les très bons coups : 
            (4, 2, True): 90000,
            (4, 1, True): 90000,
            
            (4, 2, False): 50000,
            #------------------------------------------------------
            #Les coups moyens :
            (3, 2, True): 10000,
            
            (4, 1, False): 5000,
            (3, 2, False): 5000,
            
            (3, 1, True): 2000,
            #------------------------------------------------------
            #Les coups fréquents :
            (2, 2, True): 100,
            (2, 2, False): 100,
            (1, 1, True): 100,
            (1, 1, False): 100,
            (1, 2, True): 100,
            (1, 2, False): 100,
            (3, 1, False): 100,
            
            (2, 1, True): 50,
            (2, 1, False): 50,
            
        }
        
    def draw_board(self, state):
        print('  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15')
        for i in range(self.taille - 1):
            print(f'{chr(i + 65)} ', end='')
            for j in range(self.taille - 1):
                print(f'{self.char[state[i][j]]}   ', end='')
            print(f'{self.char[state[i][self.taille - 1]]}')
            print('  ', end='')
            for j in range(self.taille - 1):
                print(f'    ', end='')
            print('  ')
        print(f'{chr(self.taille - 1 + 65)} ', end='')
        for j in range(self.taille - 1):
            print(f'{self.char[state[self.taille - 1][j]]}   ', end='')
        print(f'{self.char[state[self.taille - 1][self.taille - 1]]}')   
        
    def tour_joueur(self, state):
        nb_pions = self.nb_pions(state)
        return 1 if nb_pions[1] <= nb_pions[2] else 2
    
    def actions(self, state):
        actions = set()
        nb_pions = self.nb_pions(state)
        if nb_pions[1] == 0 and nb_pions[2] == 0:
            actions.add((self.taille//2, self.taille//2))
        elif nb_pions[1] == 1 and nb_pions[2] == 1:
            for contour in range(self.taille//2 - self.taille // 4):
                first, last = contour, self.taille - 1 - contour
                for i in range(first, last):
                    offset = i - first
                    if not state[first][i]:
                        actions.add((first, i))
                    if not state[i][last]:
                        actions.add((i, last))
                    if not state[last][last - offset]:
                        actions.add((last, last - offset))
                    if not state[last - offset][first]:
                        actions.add((last - offset, first))
        else:
            for i in range(self.taille):
                for j in range(self.taille):
                    if not state[i][j]:
                        actions.add((i, j))
        return actions
    
    
    def result(self, state, action):
        new_state = copy.deepcopy(state)
        new_state[action[0]][action[1]] = self.tour_joueur(state)
        return new_state
    
    
    def gain_joueur(self, state):
        lignes_colonnes_diagonales = self.plateau(state)
        for i in lignes_colonnes_diagonales:
            for j in range(len(i) - self.condition_victoire + 1):
                pion = i[j]
                # if pion and i[j:j+5] == 5*[pion]:
                if pion and all(i[j + x] == pion for x in range(self.condition_victoire)):
                    return True
        return False
    
    def terminal_test(self, state, profondeur):
        return profondeur == 0 or self.is_Fin_du_jeu() or  self.gain_joueur(state)
    
    
    def utility(self, state, joueur_actuel):
        adversaire = 3 - joueur_actuel
        return self.score(state, joueur_actuel) - 1.1 * self.score(state, adversaire)

    def nb_pions(self, state):
        unique, nb_pions = np.unique(np.array(state), return_counts=True)
        nb_pions = dict(zip(unique, nb_pions))
        nb_pions[1] = nb_pions.get(1, 0)
        nb_pions[2] = nb_pions.get(2, 0)
        return nb_pions
    
    def plateau(self, state):
        lignes_colonnes_diagonales = list() 
        lignes_colonnes_diagonales.extend(state) # horizontal
        lignes_colonnes_diagonales.extend(np.array(state).T) # vertical
        lignes_colonnes_diagonales.extend(np.array(state).diagonal(i) for i in range(-self.taille + self.condition_victoire, self.taille - self.condition_victoire + 1)) 
        lignes_colonnes_diagonales.extend(np.fliplr(np.array(state)).diagonal(i) for i in range(-self.taille + self.condition_victoire, self.taille - self.condition_victoire + 1)) # diag tr -> bl
        return lignes_colonnes_diagonales
    
    def meilleures_actions(self, state):
        limite_haut, limite_gauche = self.taille, self.taille
        limite_bas, limite_droite = 0, 0
        for i in range(0, self.taille):
            for j in range(0, self.taille):
                if state[i][j] != 0:
                    if i < limite_haut:
                        limite_haut = i
                    if i > limite_bas:
                        limite_bas = i
                    if j < limite_gauche:
                        limite_gauche = j
                    if j > limite_droite:
                        limite_droite = j
        espace_reduit = set()
        for i in range(max(0, limite_haut - 1), min(self.taille, limite_bas + 2)):
            for j in range(max(0, limite_gauche - 1), min(self.taille, limite_droite + 2)):
                if self.voisins(state, (i, j)):
                    espace_reduit.add((i, j))
        actions = self.actions(state)
        meilleures_actions = actions.intersection(espace_reduit)
        if len(meilleures_actions) != 0:
            return meilleures_actions
        else:
            return actions
        
        
    def voisins(self, state, action):
        neighbors = np.array([[state[i][j] if (i, j) != action else 0 for j in range(max(0, action[1] - 1), min(self.taille, action[1] + 2))] for i in range(max(0, action[0] - 1), min(self.taille, action[0] + 2))], dtype=np.int8)
        return neighbors.any()
    
    
    def is_Fin_du_jeu(self):
        return time.time() - self.temps >= self.limite_sup_temps-0.2
    
    
    def score(self, state, joueur_actuel):
        s = 0
        suite, ouvertures = 0, 0
        current_turn = self.tour_joueur(state) == joueur_actuel
        plateau = self.plateau(state)
        for lignes_colonnes_diagonales in plateau:
            for i in range(len(lignes_colonnes_diagonales)):
                if lignes_colonnes_diagonales[i] == joueur_actuel:
                    suite += 1
                elif lignes_colonnes_diagonales[i] == 0 and suite > 0:
                    ouvertures += 1
                    GAMA = 1.1 if joueur_actuel == self.joueur_actuel and (suite, ouvertures, current_turn) in self.attaque else 1.00
                    s += self.menaces.get((suite, ouvertures, current_turn), 0) * GAMA
                    suite, ouvertures = 0, 1
                elif lignes_colonnes_diagonales[i] == 0:
                    ouvertures = 1
                elif suite > 0:
                    GAMA = 1.1 if joueur_actuel == self.joueur_actuel and (suite, ouvertures, current_turn) in self.attaque else 1.00
                    s += self.menaces.get((suite, ouvertures, current_turn), 0) * GAMA
                    suite, ouvertures = 0, 0
                else:
                    ouvertures = 0
            if suite > 0:
                GAMA = 1.1 if joueur_actuel == self.joueur_actuel and (suite, ouvertures, current_turn) in self.attaque else 1.00
                s += self.menaces.get((suite, ouvertures, current_turn), 0) * GAMA
            suite, ouvertures = 0, 0
        return s
    
    def ChoixPosition(self,state):
        Test_Sortie = False
        while Test_Sortie == False :
            move = input('Entrez votre move: ')
            try :
                row = ord(move[:1].upper()) - 65
                col = int(move[1:]) - 1
                Test_Sortie = True if (row,col) in self.actions(state) else False
            except Exception:
                pass
        return row, col
    

def alpha_beta(game, state, profondeur, alpha, beta, joueur):
    game.joueur_actuel = game.tour_joueur(state)

    if game.terminal_test(state, profondeur):
        return game.utility(state, game.joueur_actuel), None

    elif joueur == game.joueur_actuel:
        max_eval = float('-inf')
        best_move = None
        for i in game.meilleures_actions(state):
            # eval = alpha_beta(game, game.result(game.state, i), profondeur, alpha, beta, 3 - joueur)
            eval, move = alpha_beta(game, game.result(game.state, i), profondeur - 1, alpha, beta, 3 - joueur)
            # test
            if eval > max_eval:
                max_eval = eval
                best_move = i
            # fin test
            # max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                return max_eval, best_move
        return max_eval, best_move

    else:
        min_eval = float('inf')
        best_move = None
        for i in game.meilleures_actions(state):
            # eval = alpha_beta(game, game.result(game.state, i), profondeur, alpha, beta, 3 - joueur)
            eval, move = alpha_beta(game, game.result(game.state, i), profondeur - 1, alpha, beta, 3 - joueur)
            # test
            if eval < min_eval:
                best_move = i
                min_eval = eval
            # fin test
            # min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                return min_eval, best_move
        return min_eval, best_move

def AlphaBetaOpti(game, state):
    game.joueur_actuel = game.tour_joueur(state)
    game.temps = time.time()
    value, move = max_value(game, state, 1, np.NINF, np.inf)
    print(f'temps: {time.time() - game.temps}s')
    return move

def max_value(game, state, profondeur, alpha, beta):
    if game.terminal_test(state, profondeur):
        return game.utility(state, game.joueur_actuel), None
    max_eval, best_move = np.NINF, None
    actions = game.meilleures_actions(state)
    for a in actions:
        if len(actions) == 1:
            return max_eval, a
        eval, move = min_value(game, game.result(state, a), profondeur - 1, alpha, beta)
        if eval > max_eval:
            max_eval, best_move = eval, a
            alpha = max(alpha, max_eval)
        if max_eval >= beta:
            return max_eval, best_move
    return max_eval, best_move

def min_value(game, state, profondeur, alpha, beta):
    if game.terminal_test(state, profondeur):
        return game.utility(state, game.joueur_actuel), None
    min_eval, best_move = np.inf, None
    actions = game.meilleures_actions(state)
    for a in actions:
        if len(actions) == 1:
            return min_eval, a
        eval, move = max_value(game, game.result(state, a), profondeur - 1, alpha, beta)
        if eval < min_eval:
            min_eval, best_move = eval, a
            beta = min(beta, min_eval)
        if min_eval <= alpha:
            return min_eval, best_move
    return min_eval, best_move
      
def main():
    g = Game()
    Tour = 0
    while not g.gain_joueur(g.state):
        if Tour == 60:
            print("Egalité !")
            return True
        
        #IA Joue : 
        if not g.gain_joueur(g.state):
            g.temps = time.time()
            g.joueur_actuel = g.tour_joueur(g.state)
            # _, move = alpha_beta(g, g.state, g.profondeur, float('-inf'), float('inf'), g.joueur_actuel)
            move = AlphaBetaOpti(g, g.state)
            g.state = g.result(g.state, move)
            print(f'Last move: {chr(move[0] + 65)}{move[1] + 1}')
            
        if g.gain_joueur(g.state):
            print(f'Victoire Joueur {g.joueur_actuel} (IA)')

        #Humain Joue : 
        if not g.gain_joueur(g.state):
            g.draw_board(g.state)
            row, col = g.ChoixPosition(g.state)
            g.state = g.result(g.state, (row, col))
            
        if g.gain_joueur(g.state) :
            print(f'Victoire Joueur {3 - g.joueur_actuel} (Joueur)')

    g.draw_board(g.state)


if __name__ == '__main__':
    main()
