import time
import pyxel
import dovetail


SCREEN_WIDTH = 255
SCREEN_HEIGHT = 128
CARD_WIDTH = 32
CARD_HEIGHT = 44

BLACK = 0
DARK_RED = 2
GREEN = 3
GREY = 6
WHITE = 7
RED = 8
GOLD = 9
LIGHT_GREEN = 11
LIGHT_BLUE = 12
ALPHA_COLOR = 13
FLASH_SEQUENCE = [14, 8, 2, 1, 13, 12, 11, 3, 15]

SUIT_COLORS = [BLACK, BLACK, RED, RED]
SUIT_FOUR_COLORS = [BLACK, LIGHT_GREEN, RED, LIGHT_BLUE]
VALUE_STRINGS = ['-', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
DEALER_DELAY = 0.5

PLAYER_X = 4
PLAYER_Y = SCREEN_HEIGHT - CARD_HEIGHT - 12
DEALER_X = 4
DEALER_Y = 4
SPLIT_X = SCREEN_WIDTH // 2 + 4
SPLIT_Y = SCREEN_HEIGHT - CARD_HEIGHT - 12
CHIPS_X = SCREEN_WIDTH // 2 - 24
CHIPS_Y = SCREEN_HEIGHT - 8

INTRO = 0
BET = 1
INSURE = 2
PLAY = 3
SPLIT = 4
DEALER = 5
PAYOUT = 6
SPLASH = 7

UP = pyxel.KEY_UP
DOWN = pyxel.KEY_DOWN
LEFT = pyxel.KEY_LEFT
RIGHT = pyxel.KEY_RIGHT
ENTER = pyxel.KEY_ENTER
KP_ENTER = pyxel.KEY_KP_ENTER
SPACE = pyxel.KEY_SPACE
ESCAPE = pyxel.KEY_ESCAPE
Q = pyxel.KEY_Q
Y = pyxel.KEY_Y
N = pyxel.KEY_N
HIT_BUTTON = pyxel.KEY_H
STAND_BUTTON = pyxel.KEY_S
DOUBLE_BUTTON = pyxel.KEY_D
SPLIT_BUTTON = pyxel.KEY_P
NEXT_BUTTONS = [ENTER, SPACE, KP_ENTER]


class Debug:
    def __init__(self):
        pass

    def update(self):
        pass

    def draw(self, state):
        pyxel.text(SCREEN_WIDTH - 10, 4, str(state.state), GOLD)


class Card:
    def __init__(self, value, suit):
        self.value = value
        self.suit = suit

    def draw(self, x, y):
        card_color = SUIT_COLORS[self.suit]                             # get card color
        # TODO -- SUIT_FOUR_COLORS option (App settings passed in?)
        pyxel.rect(x, y, x + CARD_WIDTH, y + CARD_HEIGHT, WHITE)        # draw card background
        pyxel.rectb(x, y, x + CARD_WIDTH, y + CARD_HEIGHT, card_color)  # draw card border
        value_x = (self.value % 7) * 8
        value_y = self.value // 7 * 8
        if self.suit > 1:
            pyxel.pal(BLACK, card_color)
        pyxel.blt(x + 2, y + 1, 1, value_x, value_y, 8, 8, colkey=ALPHA_COLOR)                              # draw value
        pyxel.blt(x + CARD_WIDTH - 9, y + CARD_HEIGHT - 9, 1, value_x, value_y, -8, -8, colkey=ALPHA_COLOR) # draw rotated value
        for i in range(4):
            pyxel.rectb(x + 10 + (i * 2), y + 14 + (i * 2), x + CARD_WIDTH - 10 - (i * 2), y + CARD_HEIGHT - 14 - (i * 2), card_color)  # draw center flair
        pyxel.pal()
        suit_x = self.suit * 8
        pyxel.blt(x + 1, y + 8, 0, suit_x, 0, 8, 8, colkey=ALPHA_COLOR)                                 # draw suit
        pyxel.blt(x + CARD_WIDTH - 8, y + CARD_HEIGHT - 16, 0, suit_x, 0, -8, -8, colkey=ALPHA_COLOR)   # draw rotated suit


class Hand:
    def __init__(self, x, y):
        self.cards = list()
        self.x = x
        self.y = y
        self.bet = 0
        self.double = False
        self.insured = False

    def __len__(self):
        return len(self.cards)

    def add(self, card):
        assert isinstance(card, Card)
        self.cards.append(card)

    def clear(self):
        self.cards = list()
        self.double = False
        self.insured = False

    def value(self):
        total = 0
        ace = False
        for card in self.cards:
            total += min(card.value, 10)
            if card.value == 1:
                ace = True
        if total <= 11 and ace:
            total += 10
        return total

    def value_text(self, hide_first=False):
        total = 0
        ace = False
        for i, card in enumerate(self.cards):
            if not hide_first or i > 0:
                total += min(card.value, 10)
                if card.value == 1:
                    ace = True
        if ace and total == 11:
            return '21!'
        elif ace and total < 11:
            return '{}/{}'.format(total, total + 10)
        elif total == 0:
            return ''
        else:
            return str(total)

    def draw(self, hide_first=False):
        for i, card in enumerate(self.cards):
            if hide_first and i == 0:
                pyxel.blt(self.x, self.y, 2, 0, 0, CARD_WIDTH, CARD_HEIGHT)
            else:
                card.draw(self.x + i * CARD_WIDTH // 2, self.y)
        pyxel.text(self.x + 3 * CARD_WIDTH // 4, self.y + CARD_HEIGHT + 4, self.value_text(hide_first=hide_first), WHITE)
        if self.bet > 0:
            pyxel.text(self.x + CARD_WIDTH * 2, self.y + CARD_HEIGHT + 4, 'BET: ${}'.format(self.bet), GOLD)


class GameState:

    def __init__(self):
        self.state = INTRO
        self.shoe = self.generate_new_shoe()
        self.dealer = Hand(DEALER_X, DEALER_Y)
        self.player = Hand(PLAYER_X, PLAYER_Y)
        self.split = Hand(SPLIT_X, SPLIT_Y)
        self.chips = 100    # TODO -- load chips from file

    def generate_new_shoe(self, num_decks=8):
        shoe = list()
        for _ in range(num_decks):
            for v in range(1, 14):
                for s in range(4):
                    shoe.append(Card(v, s))
        return dovetail.shuffle(shoe)

    def draw_chips(self):
        pyxel.text(CHIPS_X, CHIPS_Y, 'CHIPS: ${}'.format(self.chips), WHITE)

    def update(self):
        if self.state == INTRO:
            for button in NEXT_BUTTONS:
                if pyxel.btnp(button):
                    self.player.bet = 5
                    self.state = BET
        elif self.state == BET:
            if pyxel.btnp(UP):
                self.player.bet += 5
                self.player.bet = min(self.player.bet, self.chips)
            elif pyxel.btnp(DOWN):
                self.player.bet -= 5
                self.player.bet = max(self.player.bet, 0)
            if pyxel.btnp(RIGHT):
                self.player.bet += 1
                self.player.bet = min(self.player.bet, self.chips)
            elif pyxel.btnp(LEFT):
                self.player.bet -= 1
                self.player.bet = max(self.player.bet, 0)
            else:
                for button in NEXT_BUTTONS:
                    if self.player.bet > 0 and pyxel.btnp(button):
                        self.chips -= self.player.bet
                        if len(self.shoe) < 20:
                            self.shoe = self.generate_new_shoe()
                        for _ in range(2):
                            self.player.add(self.shoe.pop())
                            self.dealer.add(self.shoe.pop())
                        if self.dealer.cards[1].value == 1:
                            self.state = INSURE
                        else:
                            if self.player.value() == 21 or self.dealer.value() == 21:
                                self.state = PAYOUT
                            else:
                                self.state = PLAY
        elif self.state == INSURE:
            if self.chips >= self.player.bet // 2:
                if pyxel.btnp(Y):
                    self.chips -= self.player.bet // 2
                    self.player.insured = True
                    if self.player.value() == 21 or self.dealer.value():
                        self.state = PAYOUT
                    else:
                        self.state = PLAY
                if pyxel.btnp(N):
                    if self.player.value() == 21 or self.dealer.value():
                        self.state = PAYOUT
                    else:
                        self.state = PLAY
            else:
                if self.player.value() == 21 or self.dealer.value():
                    self.state = PAYOUT
                else:
                    self.state = PLAY
        elif self.state == PLAY:
            if pyxel.btnp(HIT_BUTTON):
                self.player.add(self.shoe.pop())
                if self.player.value() > 21:
                    if len(self.split) > 0:
                        self.state = SPLIT
                    else:
                        self.state = SPLASH
            if pyxel.btnp(STAND_BUTTON):
                if len(self.split) > 0:
                    self.state = SPLIT
                else:
                    self.state = DEALER
            if pyxel.btnp(SPLIT_BUTTON) and len(self.player) == 2 and len(self.split) == 0 and self.player.cards[0].value == self.player.cards[1].value and self.chips >= self.player.bet:
                self.chips -= self.player.bet
                self.split.bet = self.player.bet
                self.split.add(self.player.cards.pop())
                self.player.add(self.shoe.pop())
                self.split.add(self.shoe.pop())
                if self.player.value() == 21:
                    self.state = SPLIT
            if pyxel.btnp(DOUBLE_BUTTON) and len(self.player) == 2 and len(self.split) == 0 and self.chips >= self.player.bet:
                self.chips -= self.player.bet
                self.player.double = True
                self.player.add(self.shoe.pop())
                self.state = DEALER
        elif self.state == SPLIT:
            if len(self.split) == 2 and self.split.value() == 21:
                if len(self.player) == 2 and self.player.value() == 21:
                    self.state = PAYOUT
                else:
                    self.state = DEALER
            if pyxel.btnp(HIT_BUTTON):
                self.split.add(self.shoe.pop())
                if self.split.value() > 21:
                    if self.player.value() > 21:
                        self.state = PAYOUT
                    else:
                        self.state = DEALER
            if pyxel.btnp(STAND_BUTTON):
                self.state = DEALER
        elif self.state == DEALER:
            time.sleep(DEALER_DELAY)
            if self.dealer.value() < 17:
                self.dealer.add(self.shoe.pop())
            else:
                self.state = PAYOUT
        elif self.state == PAYOUT:
            if len(self.split) > 0 and self.split.value() <= 21:
                if len(self.split) == 2 and self.split.value() == 21:
                    self.chips += 2 * self.split.bet + self.split.bet // 2
                elif self.split.value() > self.dealer.value() or self.dealer.value() > 21:
                    self.chips += self.split.bet * 2
                elif self.split.value() == self.dealer.value():
                    self.chips += self.split.bet
            if self.player.value() <= 21:
                if self.player.value() == 21 or self.dealer.value() == 21:
                    if self.dealer.value() == 21:
                        if not self.player.insured:
                            if self.player.value() == 21:
                                self.chips += self.player.bet
                        else:
                            if self.player.value() == 21:
                                self.chips += self.player.bet * 2
                            else:
                                self.chips += self.player.bet + self.player.bet // 2
                    else:
                        self.chips += self.player.bet * 2 + self.player.bet // 2
                elif self.player.value() > self.dealer.value() or self.dealer.value() > 21:
                    self.chips += self.player.bet * 2
                    if self.player.double:
                        self.chips += self.player.bet * 2
                elif self.player.value() == self.dealer.value():
                    self.chips += self.player.bet
                    if self.player.double:
                        self.chips += self.player.bet
            self.state = SPLASH
        elif self.state == SPLASH:
            for button in NEXT_BUTTONS:
                if pyxel.btnp(button):
                    self.player.clear()
                    self.dealer.clear()
                    self.split.clear()
                    self.split.bet = 0
                    self.state = BET
        else:
            raise ValueError('GameState.state is in an invalid state: {}'.format(self.state))


class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, caption='Blackjack')
        pyxel.image(0).load(0, 0, 'suits.png')
        pyxel.image(1).load(0, 0, 'values.png')
        pyxel.image(2).load(0, 0, 'card_back.png')
        self.game = GameState()
        self.debug = Debug()
        '''self.player = Hand(PLAYER_X, PLAYER_Y)
        self.dealer = Hand(DEALER_X, DEALER_Y)
        self.split = Hand(SPLIT_X, SPLIT_Y)'''
        pyxel.run(self.update, self.draw)

    def update(self):
        self.game.update()

    def draw(self):
        pyxel.cls(GREEN)
        self.debug.draw(self.game)
        if self.game.state == INTRO:
            pass    # TODO -- draw intro
        else:
            self.game.draw_chips()
            self.game.player.draw()
            self.game.split.draw()
        if self.game.state in [BET, INSURE, PLAY, SPLIT]:
            self.game.dealer.draw(hide_first=True)
        else:
            self.game.dealer.draw()
        if self.game.state == INSURE:
            pass    # TODO -- draw insurance y/n box
        if self.game.state == SPLASH:
            if len(self.game.split) > 0:
                if self.game.split.value() > 21:
                    self.draw_bust(self.game.split.x, self.game.split.y)
                elif self.game.split.value() > self.game.dealer.value() or self.game.dealer.value() > 21:
                    self.draw_win(self.game.split.x, self.game.split.y)
                elif self.game.split.value() == self.game.dealer.value():
                    self.draw_push(self.game.split.x, self.game.split.y)
                else:
                    self.draw_lose(self.game.split.x, self.game.split.y)
            if self.game.player.value() > 21:
                self.draw_bust(self.game.player.x, self.game.player.y)
            elif self.game.player.value() > self.game.dealer.value() or self.game.dealer.value() > 21:
                self.draw_win(self.game.player.x, self.game.player.y)
            elif self.game.player.value() == self.game.dealer.value():
                self.draw_push(self.game.player.x, self.game.player.y)
            else:
                self.draw_lose(self.game.player.x, self.game.player.y)

    def draw_bust(self, x, y):
        pyxel.rect(x + 8, y + 16, x + 33, y + 26, RED)
        pyxel.text(x + 12, y + 19, 'BUST', WHITE)

    def draw_win(self, x, y):
        pyxel.rect(x + 8, y + 16, x + 33, y + 26, GREEN)
        pyxel.text(x + 12, y + 19, 'WIN!', WHITE)

    def draw_push(self, x, y):
        pyxel.rect(x + 8, y + 16, x + 33, y + 26, GREY)
        pyxel.text(x + 12, y + 19, 'PUSH', BLACK)

    def draw_lose(self, x, y):
        pyxel.rect(x + 8, y + 16, x + 33, y + 26, RED)
        pyxel.text(x + 12, y + 19, 'LOSE', WHITE)


App()
