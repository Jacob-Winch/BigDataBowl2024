from joblib import dump, load
import math
import numpy as np
from sklearn.linear_model import LogisticRegression
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
connection_string = os.environ["connection_string"]


def star_tackles_missed():
    """Calculate total tackles missed"""
    model = load("model.joblib")
    conn = psycopg2.connect("dbname=BigDataBowl user=cschneider")
    cur = conn.cursor()
    for i in range(1, 6):
        cur.execute("UPDATE players SET star_{0}_missed=0".format(i))
    cur.execute("SELECT game_id, play_id, ball_carrier FROM plays")
    plays = cur.fetchall()
    for play in plays:
        cur.execute("SELECT x, y, lr, team FROM tracking WHERE game_id=%s AND play_id=%s AND player_id=%s "
                    "AND event='pass_arrived'", play)
        ball_carrier = cur.fetchone()
        if ball_carrier is None:  # This means that the play was not a passing play
            continue
        # Get player data for the non-tacklers
        cur.execute("SELECT player_id, x, y, speed, acceleration FROM tracking "
                    "WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id "
                    "NOT IN (SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s "
                    "AND (tackle='t' OR assist='t')) AND event='pass_arrived'",
                    list(play[:2]) + [ball_carrier[3]] + list(play[:2]))
        non_tacklers = cur.fetchall()
        non_tacklers_x = [[math.sqrt(abs(ball_carrier[1] - tackler[2])),  # Sqrt of lateral distance
                           math.sqrt(math.sqrt((ball_carrier[0] - tackler[1]) ** 2
                                               + (ball_carrier[1] - tackler[2]) ** 2)),  # Sqrt of Euclidean distance
                           tackler[3], tackler[4]] for tackler in non_tacklers]  # Speed and acceleration
        tackler_probability = model.predict_proba(non_tacklers_x) if non_tacklers_x else []  # Predict probabilities
        for i, tackler in enumerate(tackler_probability):
            # Assign a star value passed on the probability
            if tackler[1] > 0.90:
                stars = "1"
            elif tackler[1] > 0.75:
                stars = "2"
            elif tackler[1] > 0.5:
                stars = "3"
            elif tackler[1] > 0.25:
                stars = "4"
            else:
                stars = "5"
            cur.execute("UPDATE players SET star_{0}_missed=star_{0}_missed+1 WHERE id=%s".format(stars),
                        (non_tacklers[i][0],))
    conn.commit()
    conn.close()


def star_tackles_made():
    """Calculate total star tackles made by each player"""
    model = load("model.joblib")
    conn = psycopg2.connect("dbname=BigDataBowl user=cschneider")
    cur = conn.cursor()
    for i in range(1, 6):
        cur.execute("UPDATE players SET star_{0}_made=0".format(i))
    cur.execute("SELECT game_id, play_id, ball_carrier FROM plays")
    plays = cur.fetchall()
    for play in plays:
        cur.execute("SELECT x, y, lr, team FROM tracking WHERE game_id=%s AND play_id=%s AND player_id=%s "
                    "AND event='pass_arrived'", play)
        ball_carrier = cur.fetchone()
        if ball_carrier is None:  # This means the play was not a passing play
            continue
        # Get player data
        cur.execute("SELECT player_id, x, y, speed, acceleration FROM tracking "
                    "WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id "
                    "IN (SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='pass_arrived'", list(play[:2]) + [ball_carrier[3]] + list(play[:2]))
        tacklers = cur.fetchall()
        tacklers_x = [[math.sqrt(abs(ball_carrier[1] - tackler[2])),  # Sqrt of lateral distance
                       math.sqrt(math.sqrt((ball_carrier[0] - tackler[1]) ** 2
                                           + (ball_carrier[1] - tackler[2]) ** 2)),  # Sqrt of Euclidean distance
                       tackler[3], tackler[4]]  # Speed and acceleration
                      for tackler in tacklers]
        tackler_probability = model.predict_proba(tacklers_x) if tacklers_x else []
        for i, tackler in enumerate(tackler_probability):
            # Assign a star value to the tackle
            if tackler[1] > 0.90:
                stars = "1"
            elif tackler[1] > 0.75:
                stars = "2"
            elif tackler[1] > 0.5:
                stars = "3"
            elif tackler[1] > 0.25:
                stars = "4"
            else:
                stars = "5"
            cur.execute("UPDATE players SET star_{0}_made=star_{0}_made+1 WHERE id=%s".format(stars),
                        (tacklers[i][0], ))
    conn.commit()
    conn.close()


def calculate_vector(magnitude: float, degrees: float):
    """Calculate the vector of a defender or ball_carrier's speed or acceleration"""
    actual_degrees = (450 - degrees) % 360
    rads = actual_degrees * math.pi / 180
    return [magnitude * math.cos(rads), magnitude * math.sin(rads)]


def expected_tackles():
    """Calculate expected tackles"""
    model = load("model.joblib")
    conn = psycopg2.connect("dbname=BigDataBowl user=cschneider")
    cur = conn.cursor()
    cur.execute("UPDATE players SET tackles_above_expected=0")
    cur.execute("UPDATE teams SET tackles_above_expected=0")
    cur.execute("SELECT game_id, play_id, ball_carrier FROM plays")
    plays = cur.fetchall()
    for play in plays:
        cur.execute("SELECT x, y, lr, team FROM tracking WHERE game_id=%s AND play_id=%s AND player_id=%s "
                    "AND event='pass_arrived'", play)
        ball_carrier = cur.fetchone()
        if ball_carrier is None:  # This means that the play is not a passing play
            continue
        # Get tackler data
        cur.execute("SELECT player_id, x, y, speed, acceleration, team FROM tracking "
                    "WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id "
                    "IN (SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='pass_arrived'", list(play[:2]) + [ball_carrier[3]] + list(play[:2]))
        tacklers = cur.fetchall()
        # Get non-tackler data
        cur.execute("SELECT player_id, x, y, speed, acceleration, team FROM tracking "
                    "WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id "
                    "NOT IN (SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='pass_arrived'", list(play[:2]) + [ball_carrier[3]] + list(play[:2]))
        non_tacklers = cur.fetchall()
        # Calculate model features for tacklers and non-tacklers
        tacklers_x = [[math.sqrt(abs(ball_carrier[1] - tackler[2])),
                       math.sqrt(math.sqrt((ball_carrier[0] - tackler[1]) ** 2 + (ball_carrier[1] - tackler[2]) ** 2)),
                       tackler[3], tackler[4]]
                      for tackler in tacklers]
        non_tacklers_x = [[math.sqrt(abs(ball_carrier[1] - tackler[2])),
                           math.sqrt(math.sqrt((ball_carrier[0] - tackler[1]) ** 2 + (ball_carrier[1] - tackler[2]) ** 2)),
                           tackler[3], tackler[4]]
                          for tackler in non_tacklers]
        tackler_probability = model.predict_proba(tacklers_x) if tacklers_x else []
        non_tackler_probability = model.predict_proba(non_tacklers_x)
        # Create dicts to map tackler and non-tackler ids to their tackle probability
        tp, ntp = {}, {}
        for i, tackler in enumerate(tackler_probability):
            tp[tacklers[i][0]] = tackler[1]
        for i, tackler in enumerate(non_tackler_probability):
            ntp[non_tacklers[i][0]] = tackler[1]
        ntp = dict(sorted(ntp.items(), key=lambda item: -item[1]))
        # If there was no tackle made on the play, assign the missed tackle to the player with the highest probability
        if not tacklers:
            for nt in ntp:
                cur.execute("UPDATE players SET tackles_above_expected=tackles_above_expected-%s WHERE id=%s",
                            (ntp.get(nt), nt))
                cur.execute("UPDATE teams SET tackles_above_expected=tackles_above_expected-%s WHERE name=%s",
                            (ntp.get(nt), non_tacklers[0][5]))
                break
        else:
            # Increment the TAA of each tackler
            for t in tp:
                cur.execute("UPDATE players SET tackles_above_expected=tackles_above_expected+%s WHERE id=%s",
                            (1 - tp.get(t), t))
                cur.execute("UPDATE teams SET tackles_above_expected=tackles_above_expected+%s WHERE name=%s",
                            (1 - tp.get(t), non_tacklers[0][5]))
            # Decrement the TAA of each non-tackler with a tackle probability
            # of at least 25% higher than the highest tackler
            for nt in ntp:
                if ntp.get(nt) < max(tp.values()) + 0.25:
                    break
                cur.execute("UPDATE players SET tackles_above_expected=tackles_above_expected-%s WHERE id=%s",
                            (ntp.get(nt), nt))
                cur.execute("UPDATE teams SET tackles_above_expected=tackles_above_expected-%s WHERE name=%s",
                            (ntp.get(nt), non_tacklers[0][5]))
    conn.commit()
    conn.close()


def generate_model():
    """Generate the Logistic Regression model used to determine tackle probability"""
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    cur.execute("SELECT game_id, play_id, ball_carrier FROM plays")
    plays = cur.fetchall()
    lateral = [[], []]
    distance = [[], []]
    speed = [[], []]
    acceleration = [[], []]
    players = [[], []]
    for play in plays:
        cur.execute("SELECT x, y, team, speed_x, speed_y FROM tracking "
                    "WHERE game_id=%s AND play_id=%s AND player_id=%s AND event='pass_arrived'", play)
        ball_carrier = cur.fetchone()
        if ball_carrier is None:  # This implies that it is not a passing play
            continue
        # Get tackler and non-tackler data
        cur.execute("SELECT x, y, speed, acceleration FROM tracking "
                    "WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id IN "
                    "(SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='pass_arrived'", list(play[:2]) + [ball_carrier[2]] + list(play[:2]))
        players[0] = cur.fetchall()
        cur.execute("SELECT x, y, speed, acceleration FROM tracking WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id NOT IN "
                    "(SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='pass_arrived'", list(play[:2]) + [ball_carrier[2]] + list(play[:2]))
        players[1] = cur.fetchall()
        np.seterr(all="raise")  # Raise all warnings as errors
        # Calculate the data for each player
        for i in range(2):
            for player in players[i]:
                lateral[i].append(math.sqrt(abs(ball_carrier[1] - player[1])))
                distance[i].append(math.sqrt(math.sqrt((ball_carrier[0] - player[0]) ** 2
                                                       + (ball_carrier[1] - player[1]) ** 2)))
                speed[i].append(player[2])
                acceleration[i].append(player[3])
    # Convert the calculated variables to the format needed for the LogisticRegression model
    x = [i for i in zip(lateral[0] + lateral[1], distance[0] + distance[1], speed[0] + speed[1],
                        acceleration[0] + acceleration[1])]
    y = [1] * len(distance[0]) + [0] * len(distance[1])
    model = LogisticRegression(class_weight="balanced").fit(x, y)
    print(model.score(x, y))  # This is an F1-score
    print(model.coef_, model.intercept_)
    dump(model, "model.joblib")


if __name__ == "__main__":
    star_tackles_missed()
    star_tackles_made()
