from joblib import dump, load
import math
import numpy as np
from sklearn.linear_model import LogisticRegression

import psycopg2


def star_tackles_missed():
    """Calculate total tackles missed"""
    model = load("distance.joblib")
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
        if ball_carrier is None:
            continue
        cur.execute("SELECT player_id, x, y, speed, acceleration FROM tracking WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id "
            "NOT IN (SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
            "AND event='pass_arrived'", list(play[:2]) + [ball_carrier[3]] + list(play[:2]))
        non_tacklers = cur.fetchall()
        non_tacklers_x = [[math.sqrt(abs(ball_carrier[1] - tackler[2])),
                       math.sqrt(math.sqrt((ball_carrier[0] - tackler[1]) ** 2 + (ball_carrier[1] - tackler[2]) ** 2)),
                       tackler[3], tackler[4]]
                      for tackler in non_tacklers]
        tackler_probability = model.predict_proba(non_tacklers_x) if non_tacklers_x else []
        for i, tackler in enumerate(tackler_probability):
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
    model = load("distance.joblib")
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
        if ball_carrier is None:
            continue
        cur.execute("SELECT player_id, x, y, speed, acceleration FROM tracking WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id "
            "IN (SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
            "AND event='pass_arrived'", list(play[:2]) + [ball_carrier[3]] + list(play[:2]))
        tacklers = cur.fetchall()
        tacklers_x = [[math.sqrt(abs(ball_carrier[1] - tackler[2])),
                       math.sqrt(math.sqrt((ball_carrier[0] - tackler[1]) ** 2 + (ball_carrier[1] - tackler[2]) ** 2)),
                       tackler[3], tackler[4]]
                      for tackler in tacklers]
        tackler_probability = model.predict_proba(tacklers_x) if tacklers_x else []
        for i, tackler in enumerate(tackler_probability):
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
    model = load("distance.joblib")
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
        if ball_carrier is None:
            continue
        cur.execute("SELECT player_id, x, y, speed, acceleration, team FROM tracking WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id "
                    "IN (SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='pass_arrived'", list(play[:2]) + [ball_carrier[3]] + list(play[:2]))
        tacklers = cur.fetchall()
        cur.execute("SELECT player_id, x, y, speed, acceleration, team FROM tracking WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id "
                    "NOT IN (SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='pass_arrived'", list(play[:2]) + [ball_carrier[3]] + list(play[:2]))
        non_tacklers = cur.fetchall()
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
                cur.execute("UPDATE teams SET tackles_above_expected=tackles_above_expected-%s WHERE name=%s",
                            (ntp.get(nt), non_tacklers[0][5]))
                break
        else:
            for t in tp:
                if t == 35466:
                    print("{0}: {1}".format(play, tp.get(t)))
                cur.execute("UPDATE players SET tackles_above_expected=tackles_above_expected+%s WHERE id=%s",
                            (1 - tp.get(t), t))
                cur.execute("UPDATE teams SET tackles_above_expected=tackles_above_expected+%s WHERE name=%s",
                            (1 - tp.get(t), non_tacklers[0][5]))
            for nt in ntp:
                if ntp.get(nt) < max(tp.values()) + 0.25:
                    break
                cur.execute("UPDATE players SET tackles_above_expected=tackles_above_expected-%s WHERE id=%s",
                            (ntp.get(nt), nt))
                cur.execute("UPDATE teams SET tackles_above_expected=tackles_above_expected-%s WHERE name=%s",
                            (ntp.get(nt), non_tacklers[0][5]))
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
    vec = [[], []]
    speed = [[], []]
    acceleration = [[], []]
    for play in plays:
        cur.execute("SELECT x, y, team, speed_x, speed_y FROM tracking WHERE game_id=%s AND play_id=%s AND player_id=%s "
                    "AND event='pass_arrived'", play)
        ball_carrier = cur.fetchone()
        if ball_carrier is None:
            continue
        cur.execute("SELECT x, y, speed, acceleration FROM tracking WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id IN "
                    "(SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='pass_arrived'", list(play[:2]) + [ball_carrier[2]] + list(play[:2]))
        players[0] = cur.fetchall()
        cur.execute("SELECT x, y, speed, acceleration FROM tracking WHERE game_id=%s AND play_id=%s AND team!=%s AND team!='FB' AND player_id NOT IN "
                    "(SELECT player_id FROM tackles WHERE game_id=%s AND play_id=%s AND (tackle='t' OR assist='t')) "
                    "AND event='pass_arrived'", list(play[:2]) + [ball_carrier[2]] + list(play[:2]))
        players[1] = cur.fetchall()
        np.seterr(all="raise")
        for i in range(2):
            for player in players[i]:
                vertical[i].append(math.sqrt(abs(ball_carrier[0] - player[0])))
                lateral[i].append(math.sqrt(abs(ball_carrier[1] - player[1])))
                distance[i].append(math.sqrt(math.sqrt((ball_carrier[0] - player[0]) ** 2
                                                       + (ball_carrier[1] - player[1]) ** 2)))
                #print(ball_carrier)
                #print(player)
                """try:
                    bc_unit_vec = [ball_carrier[4] / np.sqrt(ball_carrier[3] ** 2 + ball_carrier[4] ** 2),
                                   ball_carrier[3] / np.sqrt(ball_carrier[3] ** 2 + ball_carrier[4] ** 2)]
                    player_unit_vec = [player[3], player[2]]
                    vec[i].append(abs((player[0] - ball_carrier[0] - bc_unit_vec[1] * (player[1] - ball_carrier[1])
                                   / bc_unit_vec[0]) / (bc_unit_vec[1] * player_unit_vec[0] / bc_unit_vec[0]
                                                        - player_unit_vec[1])))
                    #print(vec[i][-1])
                except FloatingPointError:
                    vec[i].append(100)"""
                speed[i].append(player[2])
                acceleration[i].append(player[3])
    """weights = [[1 / len(distance[0])] * len(distance[0])] + [[1 / len(distance[1])] * len(distance[1])]
    plt.hist(vertical, weights=weights)
    plt.show()
    plt.hist(lateral, weights=weights)
    plt.show()
    plt.hist(distance, weights=weights)
    plt.show()"""
    x = [i for i in zip(lateral[0] + lateral[1], distance[0] + distance[1], speed[0] + speed[1], acceleration[0] + acceleration[1])]
    y = [1] * len(distance[0]) + [0] * len(distance[1])
    print(np.corrcoef(vertical[0] + vertical[1], y))
    print(np.corrcoef(distance[0] + distance[1], y))
    print(np.corrcoef(acceleration[0] + acceleration[1], y))
    print(np.corrcoef(distance[0] + distance[1], vertical[0] + vertical[1]))
    model = LogisticRegression(class_weight="balanced").fit(x, y)
    print(sum(model.predict(x)))
    print(model.score(x, y))  # This is an F1-score
    print(model.coef_, model.intercept_)
    dump(model, "distance.joblib")


if __name__ == "__main__":
    star_tackles_missed()
    star_tackles_made()
