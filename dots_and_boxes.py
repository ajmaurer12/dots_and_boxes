import numpy as np
import random
import tensorflow as tf
import pickle

#For ease of testing, you can start a game many different ways
#Rules of Dots and Boxes: Two players take turns connecting pairs of dots on the board, vertically or horizontally.
#If the player completes a box, they score a point, and get to move again. Most points wins
#The strategy to the game is a bit involved, but reasonable for a computer to be able to pick up. In the "checkers" region of difficulty.

#Machine learning is still being tested, but the two player game is working.
def game_opening():
    print('Welcome to Dots and Boxes!')
    rows = int(raw_input('How many rows of boxes will the game have? '))
    cols = int(raw_input('How many columns of boxes will the game have? '))
    print('')
    return [rows,cols]

class Board(object):
    
    def __init__(self, size=None):
        if size is not None:
            self.size = size 
        else:
            self.game_opening()
        self.initialize_board()

    def game_opening(self):
        print('Welcome to Dots and Boxes!')
        rows = int(raw_input('How many rows of boxes will the game have? '))
        cols = int(raw_input('How many columns of boxes will the game have? '))
        print('')
        return [rows,cols]

    def initialize_board(self):
        self._board_state_centers = np.zeros(self.size) #Indicators for complete boxes
        self._board_state_verts = np.zeros((self.size[0],self.size[1] + 1)) #Indicators for drawn vertical lines
        self._board_state_horis = np.zeros((self.size[0] + 1,self.size[1])) #Indicators for drawn vertical lines
        self._board_state_print = []
        self._score = [0,0]
        self._box_count = 0
        self._turn = 1
        self._game_type = 0
        self._box_made = 0
        #The computer needs information in a vector for learning, these mark the ends of the horizontals, verticals, and score
        self._lims=[0, self.size[0]*self.size[1] + self.size[1], 2*self.size[0]*self.size[1] + self.size[0] + self.size[1], 2*self.size[0]*self.size[1] + self.size[0] + self.size[1] + 2]
        self._computer_viewpoint = np.zeros( (self._lims[3]) )
        #These arrays map back the computers move to the indicator for the line it wants to draw.
        self._comp_hori_map = np.reshape( range(self._lims[0], self._lims[1]) , (self.size[0] + 1,self.size[1]))
        self._comp_vert_map = np.reshape( range(self._lims[1], self._lims[2]) , (self.size[0],self.size[1] + 1))
        self._comp_score_map = np.array(range(self._lims[2], self._lims[3]))
        #This is the initial version of what we will print in the command line to form the board
        self._board_state_print.append(list('  1' + ( '  ' * self.size[1] )))
        self._board_state_print.append(list('1 ' + '. ' * self.size[1] + '.'))
        for i in range(self.size[0]):
            self._board_state_print.append(list('  ' * self.size[1] + '   '))
            self._board_state_print.append(list('  ' + '. ' * self.size[1] + '.'))

    def print_board(self):
        for x in self._board_state_print:
            print(''.join(x))
        print('')

    #When a box is made, update the indicator, print array, and score
    def update_center(self, row, col):
        self._board_state_centers[row][col] = 1
        self._board_state_print[2 * row + 2][2 * col + 3] = str(self.turn)
        self.score_point()

    #Update point totals and computer vector
    def score_point(self):
        self._score[self.turn - 1] += 1
        self._box_count += 1
        comp_index = self._comp_score_map[self.turn - 1]
        self._computer_viewpoint[comp_index] += 1
        self._box_made = 1

    #When a player draws a horizonatal line, update the indicator, print array, computer vector, and account for produced boxes
    def update_hori(self, row, col):
        self._board_state_horis[row][col] = 1
        self._board_state_print[2 * row + 1][2 * col + 3] = '-'
        comp_index = self._comp_hori_map[row][col]
        self._computer_viewpoint[comp_index] = 1
        points = 0
        if 0 <= row < self.size[0] and self.check_hori(row + 1, col) and self.check_vert(row, col) and self.check_vert(row, col + 1):
            self.update_center(row, col)
            points += 1
        if 0 < row <= self.size[0] and self.check_hori(row - 1, col) and self.check_vert(row - 1, col) and self.check_vert(row -1, col + 1):
            self.update_center(row - 1, col)
            points += 1
        return points

    #Do the same for a player drawing a vertical line
    def update_vert(self, row, col):
        self._board_state_verts[row][col] = 1
        self._board_state_print[2 * row + 2][2 * col + 2] = '|'
        comp_index = self._comp_vert_map[row][col]
        self._computer_viewpoint[comp_index] = 1
        points = 0
        if 0 <= col < self.size[1] and self.check_vert(row, col + 1) and self.check_hori(row, col) and self.check_hori(row + 1, col):
            self.update_center(row, col)
            points += 1
        if 0 < col <= self.size[1] and self.check_vert(row, col - 1) and self.check_hori(row, col - 1) and self.check_hori(row + 1, col - 1):
            self.update_center(row, col - 1)
            points += 1
        return points

    #Query whether a line has already been drawn
    def check_hori(self, row, col):
        return self._board_state_horis[row][col]

    def check_vert(self, row, col):
        return self._board_state_verts[row][col]

    #Allows the human player to enter a move. For easy testing, the move is entered one coordinate at a time and the move can be restarted on an error by giving it a nonsense number.
    #Verifies that the move involves valid dots, the rest is accounted for in the move making function
    def read_move(self):
        read_flag = True
        print('If you make an error entering your move, enter 0 to restart the move entry.\n')
        while read_flag:
            row1 = int(raw_input('What is the row of the first dot in your move? (1 is the topmost dot, ' + str(self.size[0] + 1) + ' is the bottommost dot) ' ))
            if row1 not in range(1, self.size[0] + 2):
                print('Error. Must enter an integer between 1 and ' + str(self.size[0] + 1) + '.')
                print('Restarting entry...\n')
                continue
            col1 = int(raw_input('What is the column of the first dot in your move? (1 is the leftmost dot, ' + str(self.size[1] + 1) + ' is the rightmost dot) ' ))
            if col1 not in range(1, self.size[1] + 2):
                print('Error. Must enter an integer between 1 and ' + str(self.size[1] + 1) + '.')
                print('Restarting entry...\n')
                continue
            row2 = int(raw_input('What is the row of the second dot in your move? (1 is the topmost dot, ' + str(self.size[0] + 1) + ' is the bottommost dot ) ' ))
            if row2 not in range(1, self.size[0] + 2):
                print('Error. Must enter an integer between 1 and ' + str(self.size[0] + 1) + '.')
                print('Restarting entry...\n')
                continue
            col2 = int(raw_input('What is the column of the second dot in your move? (1 is the leftmost dot, ' + str(self.size[1] + 1) + ' is the rightmost dot) ' ))
            if col2 not in range(1, self.size[1] + 2):
                print('Error. Must enter an integer between 1 and ' + str(self.size[1] + 1) + '.')
                print('Restarting entry...\n')
                continue

            read_flag = False
            dot_coords=[row1,col1,row2,col2]
            return dot_coords

    #Makes the human player's move. Verifies that the dots form a line that has not been drawn yet.
    def make_move(self,dot_coords):
            row1 = dot_coords[0]
            col1 = dot_coords[1]
            row2 = dot_coords[2]
            col2 = dot_coords[3]
            row_d = row2 - row1
            col_d = col2 - col1

            if row_d == 1 and col_d == 0:
                if self.check_vert(row1 - 1, col1 - 1):
                    print('Error. This line has already been drawn. Restarting move selection.\n')
                    return 0
                else:
                    self.update_vert(row1 - 1, col1 - 1)
                    return 1
            elif row_d == -1 and col_d == 0:
                if self.check_vert(row2 - 1, col2 - 1):
                    print('Error. This line has already been drawn. Restarting move selection.\n')
                    return 0
                else:
                    self.update_vert(row2 - 1, col2 - 1)
                    return 1
            elif row_d == 0 and col_d == 1:
                if self.check_hori(row1 - 1, col1 - 1):
                    print('Error. This line has already been drawn. Restarting move selection.\n')
                    return 0
                else:
                    self.update_hori(row1 - 1, col1 - 1)
                    return 1
            elif row_d == 0 and col_d == -1:
                if self.check_hori(row2 - 1, col2 - 1):
                    print('Error. This line has already been drawn. Restarting move selection.\n')
                    return 0
                else:
                    self.update_hori(row2 - 1, col2 - 1)
                    return 1
            else:
                print('Error. These points do not form a valid line. Restarting move selection.\n')
                return 0

    def get_box_count(self):
        return self._box_count

    def set_box_count(self, value):
        self._box_count = value

    #Tracks how many boxes are complete to end the game when it is time
    box_count = property(get_box_count,set_box_count)

    def get_box_made(self):
        return self._box_made

    def set_box_made(self, value):
        self._box_made = value

    #Track whether a box has been made on that turn to keep track of when a player gets to play again
    box_made = property(get_box_made,set_box_made)

    def get_game_type(self):
        return self._game_type

    def set_game_type(self, value):
        self._game_type = value

    #Has one of three values: 0, human vs. human; 1, computer moves first; 2, computer moves second.
    game_type = property(get_game_type,set_game_type)

    def get_turn(self):
        return self._turn

    def set_turn(self, value):
        self._turn = value

    #1, first player turn; 2, second player turn.
    turn = property(get_turn,set_turn)

    def turn_switch(self):
        if self.turn == 1:
            self.turn = 2
        else:
            self.turn = 1

    #Play a human vs. human game
    def two_player_game(self):
        self.game_type = 0
        self.turn = 1
        final_count = self.size[0] * self.size[1]
        while self.box_count < final_count:
            print('Begin Player %d turn' % self.turn)
            self.print_board()
            self.box_made = 0
            valid_move = 0
            while not valid_move:
                move = self.read_move()
                valid_move = self.make_move(move)
            if not self.box_made:
                self.turn_switch()
        self.who_wins_2p()

    #Play a human vs. computer game
    def one_player_game(self):
        order = int(raw_input('Will you move first or second? (1/2) '))
        print('')
        if order == 1:
            self.game_type = 2
        else:
            self.game_type = 1

        self.turn = 1
        final_count = self.size[0] * self.size[1]
        while self.box_count < final_count:
            if self.game_type != self.turn:
                print('Begin your turn\n')
                self.print_board()
                self.box_made = 0
                valid_move = 0
                while not valid_move:
                    move = self.read_move()
                    valid_move = self.make_move(move)
            else:
                print('The computer is making a move...\n')
                self.print_board()
                comp_index = self.computer_choose_move()
                self.box_made = 0
                self.computer_make_move(comp_index)
                
            if not self.box_made:
                self.turn_switch()
        self.who_wins_1p()

    #Used in machine learning. Full line = 1, no line = -1
    def computer_look(self):
        return np.reshape(self._computer_viewpoint[0:self._lims[2]],(1,self._lims[2])) * 2 - 1

    #What is this player's score?
    def get_score(self, player):
        return self._score[player - 1]

    #Somewhat advanced computer strtegy, to train against.
    def computer_level2_choose_move(self):
        level2_choose = self._computer_viewpoint[0:self._lims[2]] * -1000
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                if self.check_vert(i,j) and self.check_vert(i,j+1): #look for adjacent parallel lines, finish box or avoid making a triple
                    if self.check_hori(i,j):
                        level2_choose[self._comp_hori_map[i+1][j]] += 10 #get the box
                    elif self.check_hori(i+1,j): #if both, already -1000
                        level2_choose[self._comp_hori_map[i][j]] += 10  #get the box
                    else:
                        level2_choose[self._comp_hori_map[i][j]] -= 1   #these moves give the opponent a box
                        level2_choose[self._comp_hori_map[i+1][j]] -= 1 
                if self.check_hori(i,j) and self.check_hori(i+1,j):
                    if self.check_vert(i,j):
                        level2_choose[self._comp_vert_map[i][j+1]] += 10 #get the box
                    elif self.check_vert(i,j+1): #if both, already -1000
                        level2_choose[self._comp_vert_map[i][j]] += 10  #get the box
                    else:
                        level2_choose[self._comp_vert_map[i][j]] -= 1   #these moves give the opponent a box
                        level2_choose[self._comp_vert_map[i][j+1]] -= 1 
                if self.check_hori(i,j): # Find corners, if they aren't a triple, don't make one
                    if self.check_vert(i,j):
                        level2_choose[self._comp_hori_map[i+1][j]] -= 1 
                        level2_choose[self._comp_vert_map[i][j+1]] -= 1
                    if self.check_vert(i,j+1):
                        level2_choose[self._comp_hori_map[i+1][j]] -= 1
                        level2_choose[self._comp_vert_map[i][j]] -= 1
                if self.check_hori(i+1,j): # Find corners, if they aren't a triple, don't make one
                    if self.check_vert(i,j):
                        level2_choose[self._comp_hori_map[i][j]] -= 1 
                        level2_choose[self._comp_vert_map[i][j+1]] -= 1
                    if self.check_vert(i,j+1):
                        level2_choose[self._comp_hori_map[i][j]] -= 1
                        level2_choose[self._comp_vert_map[i][j]] -= 1
        x = np.amax(level2_choose)
        poss_moves = np.flatnonzero(level2_choose == x)
        move_index = np.random.choice(poss_moves)
        return move_index

    #Ok computer strategy, to train agaainst
    def computer_level1_choose_move(self):
        level1_choose = self._computer_viewpoint[0:self._lims[2]] * -1000
        for i in range(self.size[0]):
            for j in range(self.size[1]):
                if self.check_vert(i,j) and self.check_vert(i,j+1): #look for adjacent parallel lines, finish box
                    if self.check_hori(i,j):
                        level1_choose[self._comp_hori_map[i+1][j]] += 10 #get the box
                    elif self.check_hori(i+1,j): #if both, already -1000
                        level1_choose[self._comp_hori_map[i][j]] += 10  #get the box
                if self.check_hori(i,j) and self.check_hori(i+1,j):
                    if self.check_vert(i,j):
                        level1_choose[self._comp_vert_map[i][j+1]] += 10 #get the box
                    elif self.check_vert(i,j+1): #if both, already -1000
                        level1_choose[self._comp_vert_map[i][j]] += 10  #get the box

        x = np.amax(level1_choose)
        poss_moves = np.flatnonzero(level1_choose == x)
        move_index = np.random.choice(poss_moves)
        return move_index

#This is used when there are learned layers to apply.

#    def computer_choose_move(self):
#        if self.size == [2,3]:
#            l1_out = np.tanh( np.dot(self._computer_viewpoint[0:self._lims[2]] * 2 - 1,l1) + b1 )
#            l2_out = np.tanh( np.dot(l1_out,l2) + b1 )
#            move_mat = np.dot(l2_out, l3)
#            move_mat += 100
#            move_mat = np.multiply(move_mat, (1 - self._computer_viewpoint[0:self._lims[2]]) )
#            move_index = np.argmax(move_mat)
#        else:
#            move_weights = 1 - self._computer_viewpoint[0:self._lims[2]]
#            move_weights = move_weights / np.sum(move_weights)
#            move_index = np.random.choice(self._lims[2], None, None, move_weights)
#        return move_index

    #Temporary setup without layers to apply
    def computer_choose_move(self):
        move_weights = 1 - self._computer_viewpoint[0:self._lims[2]]
        move_weights = move_weights / np.sum(move_weights)
        move_index = np.random.choice(self._lims[2], None, None, move_weights)
        return move_index

    #Poor computer strategy, to train against
    def computer_random_move(self):
        move_weights = 1 - self._computer_viewpoint[0:self._lims[2]]
        move_weights = move_weights / np.sum(move_weights)
        move_index = np.random.choice(self._lims[2], None, None, move_weights)
        return move_index

    #Computer makes its move, with some error warnings in case something has gone wrong elsewhere
    def computer_make_move(self, comp_index):
        if self._lims[0] <= comp_index < self._lims[1]:
            move_index = np.nonzero(self._comp_hori_map == comp_index)
            if self.check_hori(move_index[0][0],move_index[1][0]):
                print('computer is cheating')
            pts = self.update_hori(move_index[0][0],move_index[1][0])
        elif self._lims[1] <= comp_index < self._lims[2]:
            move_index = np.nonzero(self._comp_vert_map == comp_index)
            if self.check_vert(move_index[0][0],move_index[1][0]):
                print('computer is cheating')
            pts = self.update_vert(move_index[0][0],move_index[1][0])
        else:
            raise ValueError
        return pts

    #This version of the learner's move function gives a -1 reward for trying to move illegally, but gives a reward of the number of points scored otherwise
    def learner_make_move(self, comp_index):
        if self._lims[0] <= comp_index < self._lims[1]:
            move_index = np.nonzero(self._comp_hori_map == comp_index)
            if self.check_hori(move_index[0][0],move_index[1][0]):
                return -1
            pts = self.update_hori(move_index[0][0],move_index[1][0])
        elif self._lims[1] <= comp_index < self._lims[2]:
            move_index = np.nonzero(self._comp_vert_map == comp_index)
            if self.check_vert(move_index[0][0],move_index[1][0]):
                return -1
            pts = self.update_vert(move_index[0][0],move_index[1][0])
        else:
            raise ValueError
        return pts

    #Start a game, does not wipe the board before it starts
    def start_game(self):
        comp = raw_input('Will you play against the computer? (y/n) ').lower()
        print('')
        if comp[0] == 'y':
            self.one_player_game()
        else:
            self.two_player_game()
        
    #Results
    def who_wins_2p(self):
        if self._score[0] > self._score[1]:
            print('Player 1 wins!')
        elif self._score[0] < self._score[1]:
            print('Player 2 wins!')
        else:
            print("It's a draw!")
        self.print_board()

    def who_wins_1p(self):
        if self._score[0] > self._score[1]:
            if self.game_type == 1:
                print('Computer wins!')
            else:
                print('You win!')
        elif self._score[0] < self._score[1]:
            if self.game_type == 2:
                print('Computer wins!')
            else:
                print('You win')
        else:
            print("It's a draw!")
        self.print_board()


size = game_opening()
#loads in machine learning layers, not active right now
#with open('layers_level1.pickle', 'rb') as f:
#    data = pickle.load(f)
#l1 = data['l1_W1']
#l2 = data['l2_W1']
#l3 = data['l3_W1']
#b1 = data['l1_b1']
#b2 = data['l2_b1']
test_board = Board(size)
test_board.start_game()
