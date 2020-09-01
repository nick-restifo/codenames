import pandas as pd
import numpy as np
import requests
import random

wordlist = pd.read_csv("wordlist.csv")
expansion_wordlist = pd.read_csv("expansion_wordlist.csv")

word_site = "http://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain"

web_wordlist = pd.DataFrame([str(x, 'utf-8') for x in requests.get(word_site).content.splitlines()], columns=['words'])
opening_wordlist = [x.lower() for x in list(wordlist.append(expansion_wordlist).append(web_wordlist)["words"])]


def create_board():
    board_words = random.sample(list(wordlist["words"]), 25)
    kill_word = [board_words[0]]
    red_words = board_words[1:10]
    blue_words = board_words[10:18]
    neutral_words = board_words[18:25]
    board = {
        'red': red_words,
        'blue': blue_words,
        'neutral': neutral_words,
        'kill': kill_word
    }
    return board


def create_gameinfo():
    game_info = {}
    for team in ["red", "blue"]:
        game_info[team] = {}
        for dict in ["remaining", "score", "turns", "guesses_made", "clues_given", "clues_given_full"]:
            if dict == "remaining":
                if team == "red":
                    game_info[team][dict] = 9
                else:
                    game_info[team][dict] = 8
            elif dict in ["score", "turns"]:
                game_info[team][dict] = 0
            else:
                game_info[team][dict] = []
    game_info["game_end"] = 0
    return game_info


def scoreboard_text(game_info):
    if game_info["red"]["remaining"] < game_info["blue"]["remaining"]:
        scoreboard = "Red leads Blue, " + str(game_info["red"]["remaining"]) + "-" + str(game_info["blue"]["remaining"])
    elif game_info["red"]["remaining"] > game_info["blue"]["remaining"]:
        scoreboard = "Blue leads Red, " + str(game_info["blue"]["remaining"]) + "-" + str(game_info["red"]["remaining"])
    else:
        scoreboard = "Red & Blue are tied, " + str(game_info["blue"]["remaining"]) + "-" + str(game_info["red"]["remaining"])
    return scoreboard


def create_scoreboard(game_info, ending_team=None):
    if game_info["game_end"] == 0:
        scoreboard = scoreboard_text(game_info)
    else:
        if ending_team is None:
            if game_info["red"]["remaining"] == 0:
                scoreboard = "Red beats Blue, Blue had " + game_info["blue"]["remaining"] + " clues remaining."
            else:
                scoreboard = "Blue beats Red, Red had " + game_info["red"]["remaining"] + " clues remaining."
        else:
            first_scoreboard = scoreboard_text(game_info)
            scoreboard = ending_team + " loses on the kill card! " + first_scoreboard.replace("leads", "was leading").replace("are tied", "were tired")
    return scoreboard


def board_to_list(board):
    full_list = []
    for type in board:
        for word in board[type]:
            full_list.append(word.lower())
    return full_list


def clue_vailidity(board, clue):
    valid = True
    if clue.lower() not in opening_wordlist:
        print("Unknown word. Not a valid clue.")
        valid = False
    elif clue.lower() in board_to_list(board):
        print("Cannot use a word on the board. Not a valid clue.")
        valid = False
    return valid


def guess_validity(board, guess):
    if guess.lower() in board_to_list(board):
        return True
    else:
        return False


def provide_clue(board):
    valid = False
    while valid is False:
        clue = input("Enter Clue:")
        if clue_vailidity(board, clue):
            valid = True
            bid = input("Enter Bid:")
            print(clue + " for ", bid)
            bid = int(bid)
            return clue, bid


def make_guess(board):
    valid = False
    while valid is False:
        guess = input("Enter Guess:").lower()
        if guess_validity(board, guess):
            valid = True
            return guess


def alter_board(board, team, guess):
    turn_status = "continue"
    for type in board:
        for word in board[type]:
            if guess == word.lower():
                board[type].remove(word)
                if type == team:
                    turn_status = "continue"
                elif type == "kill":
                    turn_status = type
                else:
                    turn_status = "end"
    return board, turn_status


def run_game():
    board = create_board()
    game_info = create_gameinfo()
    while game_info["game_end"] == 0:
        for team in ["Red", "Blue"]:
            print(team, "'s Turn")
            print(board)
            game_info[team.lower()]["turns"] += 1
            cluetype = provide_clue(board)
            clue = cluetype[0]
            bid = cluetype[1]
            full_clue = clue + " for " + str(bid)
            game_info[team.lower()]["clues_given"].append(clue)
            game_info[team.lower()]["clues_given_full"].append(full_clue)
            turn = "continue"
            guesses = 0
            while turn == "continue" and guesses < bid:
                guess = make_guess(board)
                game_info[team.lower()]["guesses_made"].append(guess)
                game = alter_board(board, team.lower(), guess)
                board = game[0]
                turn = game[1]
                if turn == "continue":
                    print("Correct!")
                    game_info[team.lower()]["remaining"] -= 1
                    game_info[team.lower()]["score"] += 1
                elif turn == "kill" or game_info[team.lower()]["remaining"] == 0:
                    break
                else:
                    print("Incorrect")
                guesses += 1
            if turn == "kill" or game_info[team.lower()]["remaining"] == 0:
                game_info["game_end"] = 1
                print("Game Over!")
                scoreboard = create_scoreboard(game_info, team)
                print(scoreboard)
                break
            scoreboard = create_scoreboard(game_info)
            print(scoreboard)

