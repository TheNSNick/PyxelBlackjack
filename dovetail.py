"""Implement mathematically defined shuffling.

This module is based on the 1992 Bayer-Diaconis paper 'Trailing the Dovetail Shuffle to its Lair',
which describes the earlier Gilbert-Shannon-Reeds shuffle, or GSR Shuffle, and how many are adequate.

To my layman's eyes, it appears they come to the conclusion that after shuffling a deck of N cards
3/2 * log(base 2)N, shuffling becomes 'effective'. The default is 3, but the keyword 'eff_shuffles'
can be passed to alter this.

The full paper can be found at:     http://statweb.stanford.edu/~cgates/PERSI/papers/bayer92.pdf
and also at:                        http://projecteuclid.org/download/pdf_1/euclid.aoap/1177005705

"""
import math
import random


def choose(n, k):
    """Calculate n choose k.

    n choose k, or the k-combination of a set of n items can be calculated as:
    n! / k!(n-k)!

    """
    if n < 0 or k < 0 or n < k:
        raise ValueError('Invalid number given to choose({}, {})'.format(n, k))
    else:
        return math.factorial(n) / (math.factorial(k) * math.factorial(n-k))


def binomial_split(deck):
    """Split a deck according to a binomial distribution.

    Given a deck with N cards, divide such that the chances of k cards being taken off the top is:
    (N choose k) / 2^N      for 0 <= k <= N.
    """
    n = len(deck)
    total_odds = pow(2, n)
    odds_table = {}
    for k in range(1, n+1):
        if k-1 in odds_table.keys():
            odds_table[k] = choose(n, k) + odds_table[k-1]
        else:
            odds_table[k] = choose(n, k)
    random.seed()
    random_int = random.randint(1, total_odds)
    cut = n
    for k in range(1, n+1):
        if odds_table[k] > random_int:
            if k == 0:
                cut = 0
            elif abs(odds_table[k] - random_int) < abs(odds_table[k-1] - random_int):
                cut = k
            else:
                cut = k - 1
            break
    return deck[:cut], deck[cut:]


def riffle(part_a, part_b):
    """Shuffles two parts together as described in a GSR shuffle.

    The two parts, containing A and B cards, respectively, are shuffled
    such that the odds of a card coming from part_a are: A / (A + B)
    and thus the odds of a card coming from part_b are: B / (A + B)

    """
    deck = []
    a = len(part_a)
    b = len(part_b)
    random.seed()
    while a > 0 and b > 0:
        random_int = random.randint(1, a+b)
        if random_int <= a:
            deck.insert(0, part_a.pop())
            a = len(part_a)
        else:
            deck.insert(0, part_b.pop())
            b = len(part_b)
    final_deck = []
    if a == 0:
        final_deck.extend(part_b)
    else:
        final_deck.extend(part_a)
    final_deck.extend(deck)
    return final_deck


def shuffle(deck, eff_shuffles=3):
    """Shuffles a number of times as determined by Bayer Diaconis 1992.

    This amount is 3/2 * log(base 2)n + theta ;
    where theta is the number of effective shuffles,
    and n is the number of cards in the deck.

    """
    shuffle_deck = deck[:]
    base_num_shuffles = int(round(1.5 * math.log(len(deck), 2)))
    num_shuffles = base_num_shuffles + eff_shuffles
    for _ in range(num_shuffles):
        left, right = binomial_split(shuffle_deck)
        shuffle_deck = riffle(left, right)
    return shuffle_deck
