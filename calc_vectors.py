from joblib import dump, load
import math
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression

import psycopg2


def calculate_vector(magnitude: float, degrees: float):
    """Calculate the vector of a defender or ball_carrier's speed or acceleration"""
    actual_degrees = (450 - degrees) % 360
    rads = actual_degrees * math.pi / 180
    return [magnitude * math.cos(rads), magnitude * math.sin(rads)]


def expected_tackles():
    """Calculate expected tackles"""
    model = load("distance.joblib")
    conn = psycopg2.connect("dbname=BigDataBowl user=cschneider")
    cur = conn.cursor()
    cur.execute("UPDATE players SET tackles_above_expected=0")
    cur.execute("SELECT game_id, play_id, ball_carrier FROM plays")
    plays = cur.fetchall()
    for play in plays:
        cur.execute("SELECT x, y, lr, team FROM tracking WHERE game_id=%s AND play_id=%s AND player_id=%s "
                    "AND event='handoff'", play)
        ball_carrier = cur.fetchone()
        if ball_carrier is None:
            continue
        cur.execute("SELECT player_id, x, y FROM tracking WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id "
                    "IN (SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='handoff'", list(play[:2]) + [ball_carrier[3]] + list(play[:2]))
        tacklers = cur.fetchall()
        cur.execute("SELECT player_id, x, y FROM tracking WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id "
                    "NOT IN (SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='handoff'", list(play[:2]) + [ball_carrier[3]] + list(play[:2]))
        non_tacklers = cur.fetchall()
        tacklers_x = [[math.sqrt(abs(ball_carrier[1] - tackler[2])),
                       math.sqrt(math.sqrt((ball_carrier[0] - tackler[1]) ** 2 + (ball_carrier[1] - tackler[2]) ** 2))]
                      for tackler in tacklers]
        non_tacklers_x = [[math.sqrt(abs(ball_carrier[1] - tackler[2])),
                           math.sqrt(math.sqrt((ball_carrier[0] - tackler[1]) ** 2 + (ball_carrier[1] - tackler[2]) ** 2))]
                          for tackler in non_tacklers]
        tackler_probability = model.predict_proba(tacklers_x) if tacklers_x else []
        non_tackler_probability = model.predict_proba(non_tacklers_x)
        tp, ntp = {}, {}
        for i, tackler in enumerate(tackler_probability):
            tp[tacklers[i][0]] = tackler[1]
        for i, tackler in enumerate(non_tackler_probability):
            ntp[non_tacklers[i][0]] = tackler[1]
        ntp = dict(sorted(ntp.items(), key=lambda item: -item[1]))
        if not tacklers:
            for nt in ntp:
                cur.execute("UPDATE players SET tackles_above_expected=tackles_above_expected-%s WHERE id=%s",
                            (ntp.get(nt), nt))
                break
        else:
            for t in tp:
                cur.execute("UPDATE players SET tackles_above_expected=tackles_above_expected+%s WHERE id=%s",
                            (1 - tp.get(t), t))
            min_distance = min([math.sqrt(val[1] ** 2 + val[2] ** 2) for val in tacklers])
            for nt in ntp:
                if ntp.get(nt) < max(tp.values()):
                    break
                val = 0
                for non_tackler in non_tacklers:
                    if non_tackler[0] == nt:
                        val = non_tackler[1:]
                        break
                if math.sqrt(val[0] ** 2 + val[1] ** 2) <= min_distance:
                    cur.execute("UPDATE players SET tackles_above_expected=tackles_above_expected-%s WHERE id=%s",
                                (ntp.get(nt), nt))
    conn.commit()
    conn.close()


def plot_distance():
    """Plot the distance between a defender and the ball-carrier"""
    conn = psycopg2.connect("dbname=BigDataBowl user=cschneider")
    cur = conn.cursor()
    cur.execute("SELECT game_id, play_id, ball_carrier FROM plays")
    plays = cur.fetchall()
    vertical = [[], []]
    lateral = [[], []]
    distance = [[], []]
    players = [[], []]
    orientation = [[], []]
    for play in plays:
        cur.execute("SELECT x, y, lr, team FROM tracking WHERE game_id=%s AND play_id=%s AND player_id=%s "
                    "AND event='handoff'", play)
        ball_carrier = cur.fetchone()
        if ball_carrier is None:
            continue
        cur.execute("SELECT x, y, direction FROM tracking WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id IN "
                    "(SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='handoff'", list(play[:2]) + [ball_carrier[3]] + list(play[:2]))
        players[0] = cur.fetchall()
        cur.execute("SELECT x, y, direction FROM tracking WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id NOT IN "
                    "(SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='handoff'", list(play[:2]) + [ball_carrier[3]] + list(play[:2]))
        players[1] = cur.fetchall()
        for i in range(2):
            for player in players[i]:
                vertical[i].append(abs(ball_carrier[0] - player[0]))
                lateral[i].append(math.sqrt(abs(ball_carrier[1] - player[1])))
                distance[i].append(math.sqrt(math.sqrt((ball_carrier[0] - player[0]) ** 2
                                                       + (ball_carrier[1] - player[1]) ** 2)))
                degrees = np.degrees(np.arctan2(ball_carrier[0] - player[0], ball_carrier[1] - player[1])) % 360
                degree_difference = abs(player[2] - degrees)
                if degree_difference > 180:
                    degree_difference = 360 - degree_difference  # Degree difference is now between 0-180
                orientation[i].append(np.sqrt((180 - degree_difference) / 180))
    """weights = [[1 / len(distance[0])] * len(distance[0])] + [[1 / len(distance[1])] * len(distance[1])]
    plt.hist(vertical, weights=weights)
    plt.show()
    plt.hist(lateral, weights=weights)
    plt.show()
    plt.hist(distance, weights=weights)
    plt.show()"""
    x = [i for i in zip(lateral[0] + lateral[1], distance[0] + distance[1])]
    y = [1] * len(distance[0]) + [0] * len(distance[1])
    print(np.corrcoef(orientation[0] + orientation[1], y))
    model = LogisticRegression(class_weight="balanced").fit(x, y)
    print(sum(model.predict(x)))
    print(model.score(x, y))  # This is an F1-score
    print(model.coef_, model.intercept_)
    dump(model, "distance.joblib")


if __name__ == "__main__":
    plot_distance()
