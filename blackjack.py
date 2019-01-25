import time
import pyxel
import dovetail


SCREEN_WIDTH = 255
SCREEN_HEIGHT = 127
CARD_WIDTH = 32
CARD_HEIGHT = 44

BLACK = 0
DARK_RED = 2
GREEN = 3
WHITE = 7
RED = 8
GOLD = 9
LIGHT_GREEN = 11
LIGHT_BLUE = 12
ALPHA_COLOR = 13
FLASH_SEQUENCE = [14, 8, 2, 1, 13, 12, 11, 3, 15]

SPADES = 0
CLUBS = 1
HEARTS = 2
DIAMONDS = 3

SUIT_COLORS = [BLACK, BLACK, RED, RED]
SUIT_FOUR_COLORS = [BLACK, LIGHT_GREEN, RED, LIGHT_BLUE]
VALUE_STRINGS = ['-', 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
DEALER_DELAY = 0.5

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
HIT_BUTTON = pyxel.KEY_H
STAND_BUTTON = pyxel.KEY_S
DOUBLE_BUTTON = pyxel.KEY_D
SPLIT_BUTTON = pyxel.KEY_P


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
        self.x = x
        self.y = y
        self.cards = list()
        self.bet = 0
        self.double = False
        self.insured = False
        self.blackjack = False

    def add(self, card):
        self.cards.append(card)

    def clear(self, clear_bet=False):
        self.cards.clear()
        self.double = False
        self.insured = False
        if clear_bet:
            self.bet = 0

    def value(self):
        total = 0
        ace = False
        for card in self.cards:
            total += min(card.value, 10)
            if card.value == 1:
                ace = True
        if ace and total <= 11:
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
        if total == 0:
            return ''
        if ace and total < 11:
            return '{}/{}'.format(total, total + 10)
        if ace and total == 11:
            return '21!'
        return str(total)

    def draw(self, hide_first=False):
        for i, card in enumerate(self.cards):
            if hide_first and i == 0:
                pyxel.blt(self.x, self.y, 2, 0, 0, CARD_WIDTH, CARD_HEIGHT)
            else:
                card_x = self.x + i * CARD_WIDTH // 2
                card.draw(card_x, self.y)
        pyxel.text(self.x + 8, self.y + CARD_HEIGHT + 4, self.value_text(hide_first=hide_first), WHITE)
        if self.bet > 0:
            bet_amount = self.bet
            if self.double:
                bet_amount += self.bet
            pyxel.text(self.x + CARD_WIDTH, self.y + CARD_HEIGHT + 4, 'BET: ${}'.format(bet_amount), GOLD)


class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT)
        # initialization
        pyxel.image(0).load(0, 0, 'suits.png')
        pyxel.image(1).load(0, 0, 'values.png')
        pyxel.image(2).load(0, 0, 'card_back.png')
        self.state = INTRO
        self.shoe = list()
        self.dealer = Hand(4, 4)
        self.player = Hand(4, SCREEN_HEIGHT - CARD_HEIGHT - 12)
        self.player.bet = 5
        self.split = Hand(SCREEN_WIDTH // 2 + 4, SCREEN_HEIGHT - CARD_HEIGHT - 12)  # TODO -- move over?
        self.chips = 100
        pyxel.run(self.update, self.draw)

    def deal_new_shoe(self, num_decks=8):
        new_shoe = list()
        for _ in range(num_decks):
            for v in range(1, 14):
                for s in range(4):
                    new_shoe.append(Card(v, s))
        self.shoe = dovetail.shuffle(new_shoe)

    def deal_new_hand(self):
        if len(self.shoe) < 20:
            self.deal_new_shoe()
        self.dealer.clear()
        self.player.clear()
        self.split.clear(clear_bet=True)
        for _ in range(2):
            self.player.add(self.shoe.pop())
            self.dealer.add(self.shoe.pop())

    def update(self):
        if pyxel.btnp(ESCAPE) or pyxel.btnp(Q):
            pyxel.quit()
        if self.state == INTRO:
            if pyxel.btnp(ENTER) or pyxel.btnp(SPACE) or pyxel.btnp(KP_ENTER):
                # TODO -- load chips from file
                self.state = BET
        else:
            pyxel.mouse(True)
            if self.state == BET:
                if pyxel.btnp(UP):
                    self.player.bet += 5
                    if self.player.bet > self.chips:
                        self.player.bet = self.chips
                if pyxel.btnp(DOWN):
                    self.player.bet -= 5
                    if self.player.bet < 0:
                        self.player.bet = 0
                if pyxel.btnp(LEFT):
                    self.player.bet -= 1
                    if self.player.bet < 0:
                        self.player.bet = 0
                if pyxel.btnp(RIGHT):
                    self.player.bet += 1
                    if self.player.bet > self.chips:
                        self.player.bet = self.chips
                if (pyxel.btnp(ENTER) or pyxel.btnp(SPACE) or pyxel.btnp(KP_ENTER)) and 0 < self.player.bet <= self.chips:
                    self.chips -= self.player.bet
                    # TODO -- save chip amount to file
                    self.deal_new_hand()
                    if self.dealer.cards[1].value == 1:
                        self.state == INSURE
                    if self.player.value() == 21:
                        self.player.blackjack = True
                    if self.dealer.value() == 21:
                        self.dealer.blackjack = True
                    if self.player.blackjack or self.dealer.blackjack:
                        self.state = PAYOUT
                    self.state = PLAY
            elif self.state == INSURE:
                if pyxel.btnp(pyxel.KEY_Y) or pyxel.btnp(pyxel.KEY_N):
                    if pyxel.btn(pyxel.KEY_Y) and (self.player.value() == 21 or self.chips >= self.bet // 2):
                        self.player.insured = True
                        if self.player.value() == 21:
                            self.player.blackjack = True
                        else:
                            self.chips -= self.bet // 2
                    if self.player.value() == 21:
                        self.player.blackjack = True
                    if self.dealer.value() == 21:
                        self.dealer.blackjack = True
                    if self.player.blackjack or self.dealer.blackjack:
                        self.state = PAYOUT
                self.state = PLAY
            elif self.state == PLAY:
                if pyxel.btnp(HIT_BUTTON):
                    # TODO -- animation
                    self.player.cards.append(self.shoe.pop())
                    if self.player.value() > 21:
                        if len(self.split.cards) > 0:
                            self.state = SPLIT
                        else:
                            self.state = SPLASH
                if pyxel.btnp(STAND_BUTTON):
                    if len(self.split.cards) > 0:
                        self.state = SPLIT
                    else:
                        self.state = DEALER
                if pyxel.btnp(DOUBLE_BUTTON) and len(self.split.cards) == 0 and self.chips >= self.player.bet and len(self.player.cards) == 2:
                    self.player.double = True
                    self.chips -= self.player.bet
                    # TODO -- animation
                    self.player.cards.append(self.shoe.pop())
                    if self.player.value() > 21:
                        self.state = SPLASH
                    else:
                        self.state = DEALER
                if pyxel.btnp(SPLIT_BUTTON) and len(self.split.cards) == 0 and self.chips >= self.player.bet and len(self.player.cards) == 2 and self.player.cards[0].value == self.player.cards[1].value:
                    self.chips -= self.player.bet
                    self.split.bet = self.player.bet
                    # TODO -- animation
                    self.split.cards.append(self.player.cards.pop())
                    # TODO -- animation
                    self.player.cards.append(self.shoe.pop())
                    # TODO -- animation
                    self.split.cards.append(self.shoe.pop())
            elif self.state == SPLIT:
                if pyxel.btnp(HIT_BUTTON):
                    # TODO -- animation
                    self.split.cards.append(self.shoe.pop())
                    if self.split.value() > 21:
                        if self.player.value() > 21:
                            self.state = SPLASH
                        else:
                            self.state = DEALER
                if pyxel.btnp(STAND_BUTTON):
                    self.state = DEALER
                if pyxel.btnp(DOUBLE_BUTTON) and len(self.split.cards) == 2 and self.chips >= self.split.bet:
                    self.chips -= self.split.bet
                    self.split.double = True
                    # TODO -- animation
                    self.split.cards.append(self.shoe.pop())
                    if self.split.value() > 21 and self.player.value() > 21:
                        self.state = SPLASH
                    else:
                        self.state = DEALER
            elif self.state == DEALER:
                time.sleep(DEALER_DELAY)
                if self.dealer.value() < 17:
                    self.dealer.cards.append(self.shoe.pop())
                    if self.dealer.value() > 21:
                        self.state = PAYOUT
            elif self.state == PAYOUT:
                # TODO -- saving chips to file
                self.state = SPLASH
                if self.player.blackjack:
                    if self.dealer.blackjack:
                        if self.player.insured:
                            self.chips += 2 * self.player.bet   # insured - even money on blackjack
                        else:
                            self.chips += self.player.bet   # push
                    else:
                        self.chips += (5 * self.player.bet) // 2    # 3:2 payout + bet back
                else:
                    if self.player.value() > 21 and (len(self.split.cards) == 0 or self.split.value() > 21):
                        pass    # bust
                    else:
                        for hand in [self.player, self.split]:
                            if len(hand.cards) > 0 and hand.value() <= 21:
                                if self.dealer.value() > 21 or hand.value() > self.dealer.value():
                                    winnings = 2 * hand.bet  # WIN
                                    if hand.double:
                                        winnings *= 2
                                    self.chips += winnings
                                elif hand.value() == self.dealer.value():
                                    push = hand.bet     # PUSH (money back)
                                    if hand.double:
                                        push *= 2
                                    self.chips += push
            elif self.state == SPLASH:
                if pyxel.btnp(ENTER) or pyxel.btnp(SPACE) or pyxel.btnp(KP_ENTER):
                    self.dealer.clear(clear_bet=True)
                    self.player.clear()
                    self.split.clear(clear_bet=True)
                    self.state = BET

    def draw(self):
        pyxel.cls(GREEN)
        if self.state == INTRO:
            self.draw_intro()
        else:
            # TODO -- draw shoe
            if self.state == BET:
                self.player.draw()  # for drawing bet amount
                self.draw_chips()
            else:
                if self.state in [INSURE, PLAY, SPLIT]:
                    self.dealer.draw(hide_first=True)
                else:
                    self.dealer.draw()
                self.player.draw()
                self.draw_chips()
                self.split.draw()
                if self.state == BET:
                    pass    # TODO : "BET!" flash text and GOLD instructions (up/down/left/right)
                if self.state == INSURE:
                    self.draw_insurance()
                if self.state == SPLASH:
                    pyxel.text(10, 10, 'Placeholder W/L text', WHITE)    # TODO -- WIN/LOSE gfx
                    # TODO -- split W/L gfx if necessary

    def draw_intro(self):
        pyxel.text(SCREEN_WIDTH // 2 - 40, SCREEN_HEIGHT // 3, 'Welcome to BLACKJACK!', GOLD)
        flash_color = FLASH_SEQUENCE[(pyxel.frame_count // 4) % len(FLASH_SEQUENCE)]
        pyxel.text(SCREEN_WIDTH // 2 - 54, 3 * SCREEN_HEIGHT // 5, 'Press SPACE or ENTER to begin', flash_color)
        # TODO -- draw the intro screen

    def draw_chips(self):
        pyxel.text(SCREEN_WIDTH // 4 + 12, SCREEN_HEIGHT - 8, 'CHIPS: ${}'.format(self.chips), GOLD)

    def draw_insurace(self):
        pyxel.rect(SCREEN_WIDTH // 2 - 32, SCREEN_HEIGHT // 2, SCREEN_WIDTH // 2 + 32, SCREEN_HEIGHT // 2 + 16, GREEN)
        pyxel.rectb(SCREEN_WIDTH // 2 - 31, SCREEN_HEIGHT // 2 + 1, SCREEN_WIDTH // 2 + 31, SCREEN_HEIGHT // 2 + 14, GOLD)
        pyxel.text(SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2 + 3, 'INSURANCE?', GOLD)
        pyxel.text(SCREEN_WIDTH // 2 - 8, SCREEN_HEIGHT // 2 + 10, 'Y / N', GOLD)


App()
