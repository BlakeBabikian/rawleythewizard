from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import numpy as np
import json


@app.route('/', methods=['GET', 'POST'])
def home():
    session.clear()
    if request.method == 'POST':
        num_players = int(request.form.get('num_players'))
        if num_players <= 3:
            num_rounds = 20
        elif num_players == 4:
            num_rounds = 15
        elif num_players <= 5:
            num_rounds = 12
        else:
            num_rounds = 10
        session['total_rounds'] = num_rounds
        if 2 <= num_players < 7:
            session['num_players'] = num_players
            return redirect('/players')
        else:
            return render_template('index.html', error="Enter a number from 2 to 6")
    return render_template('index.html')


@app.route('/players', methods=['GET', 'POST'])
def players():
    session['starter_id'] = np.random.randint(1, session['num_players'] + 1)
    if request.method == 'POST':
        player_names = {i: request.form.get(f'player{i}') for i in range(1, session['num_players'] + 1)}
        session['player_points'] = {i: {"player_name": name, "points": 0} for i, name in player_names.items()}
        session['round_tracker'] = 1
        return redirect('/game')
    return render_template('players.html', num_players=session['num_players'])


@app.route('/game', methods=['GET', 'POST'])
def game():
    return render_template('game.html', player_points=session['player_points'], round_number=session['round_tracker'])


@app.route('/results', methods=['GET', 'POST'])
def results():
    return render_template('game.html', data=session['player_points'])


@app.route('/scorecard', methods=['GET', 'POST'])
def scorecard():
    # this if statement will prevent an empty scorecard to be displayed
    if 'total_score' in session:
        return render_template('scorecard.html', data=session['total_score'])
    # this else will ensure the scorecard gets displayed when data is relevant
    else:
        return render_template('game.html', player_points=session['player_points'],
                               round_number=session['round_tracker'])


def count_points(round_score):
    player_points = session['player_points']  # set player points as a local variable
    # for loop going through the indexes of round score i = player id
    for i in round_score:
        player = round_score.get(i)  # get the player from round score
        player_guess = player.get('guessed')  # get the guess from player
        player_outcome = player.get('outcome')  # get the outcome from player
        # this if statement will run when the player guess the right number of tricks
        if player_guess == player_outcome:
            player_points[i]['points'] += 20 + (10 * player_guess)  # calculate points, add to existing points
        # this else will when the player did not get their guess right
        else:
            difference = abs(player_guess - player_outcome)  # calculate difference
            player_points[i]['points'] -= difference * 10  # calculate points, subtract from existing points
        round_score[i]['Points'] = player_points[i]['points']  # add player points to round score for scorecard
        round_score[i]['Name'] = player_points[i]['player_name']  # add player name to round score for scorecard
    session['round_score'] = round_score  # set round_score back to session var
    return player_points  # return updated player points


@app.route('/play_round', methods=['GET', 'POST'])
def play_round():
    # this if statement will only run for the first guess of the first round
    if 'guess_tracker' not in session:
        session['guess_tracker'] = 1  # guess_tracker is to keep track of guesses within a round, reset at end of round
        session['input_type'] = 'Guess'  # input type keeps track of if the numbers being inputted are guess or outcomes
        session['current_id'] = session['starter_id']  # set the current id to the randomly chosen starter id

    # this if else statement will only run at the end of the game, it will return the final results page
    elif session['round_tracker'] > session['total_rounds']:
        return render_template('game.html', player_points=session['player_points'],
                               round_number=session['round_tracker'])  # untested

    # this else will run all other round and guesses
    else:
        # this if statement will run after everyone has guessed,
        if session['guess_tracker'] == session['num_players'] and session['input_type'] == 'Guess':
            session['input_type'] = 'Actual'  # change the input type to 'Actual' in preparation for next input
            return render_template('play_round.html')  # page that signals everyone has guessed

        # this if else statement catches if everyone has entered a guess and their outcomes
        elif session['guess_tracker'] == session['num_players'] * 2:
            session['input_type'] = 'Guess'  # change the input type to 'Guess' in preparation for next round
            session['current_id'] = session['starter_id']  # set current id to starting id
            session['guess_tracker'] = 0  # reset guess tracker
            # this if statement will run to prevent setting an unavailable player id
            if session['starter_id'] == session['num_players']:
                session['starter_id'] = 1  # set the start id rotation back to the start
            # this else will run when increasing the current id by 1 produces a valid player id
            else:
                session['starter_id'] += 1  # increase starter id by 1
            # this if statement will run on all rounds besides the first
            if 'total_score' in session:
                # update the total score to include this rounds results
                session['total_score'].update({str(session['round_tracker']): session['round_score']})
            # this else will run on after the first round only
            else:
                # create session variable containing a dictionary of round results
                session['total_score'] = {session['round_tracker']: session['round_score']}
            session['round_tracker'] = session['round_tracker'] + 1  # increase round tracking by 1
            # this line sends round score to the count_points function, which return the player points, saved to session
            session['player_points'] = count_points(session['round_score'])
            session.pop('round_score')  # clear round score from session, in preparation for next round
            return redirect('/game')  # open the main game page

        # this if statement will run on the first outcome input of each round
        elif session['guess_tracker'] == session['num_players'] and session['input_type'] == 'Actual':
            session['current_id'] = session['starter_id']  # set the current id to the starting id

        # this if statement will run to prevent setting an unavailable player id
        elif session['current_id'] == session['num_players']:
            session['current_id'] = 1  # set the start id rotation back to the start

        # this else will be run on most rounds excluding the special cases from above
        else:
            # this if statement will run to prevent setting an unavailable player id
            if session['guess_tracker'] == session['num_players'] and session['input_type'] == 'Actual':
                session['current_id'] = session['starter_id']  # set the current id to start id
            # this else will run when increasing the current id by 1 produces a valid player id
            else:
                session['current_id'] = session['current_id'] + 1   # increase current id by 1

        session['guess_tracker'] = session['guess_tracker'] + 1  # increase guess tracker by 1
    session['current_name'] = session['player_points'][str(session['current_id'])]['player_name']  # retrieve name
    return render_template('enter_number.html', player_id=session['current_id'],
                           player_name=session['current_name'],
                           input_type=session['input_type'])


@app.route('/enter_number', methods=['POST'])
def enter_number():
    # this if statement ensures correct entry point
    if request.method == 'POST':
        input_type = request.form.get('input_type')
        player_id = request.form.get('player_id')
        number = int(request.form.get('number'))
        if 'round_score' not in session:
            round_score = {}
        else:
            round_score = session['round_score']
        if input_type == "Guess":
            round_score.update({player_id: {"guessed": number, "outcome": 0}})
        else:
            round_score[player_id]['outcome'] = number
        session['round_score'] = round_score
        return redirect(url_for('play_round'))
    return "Invalid method", 405


if __name__ == '__main__':
    app.run(debug=True)


