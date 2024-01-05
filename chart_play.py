from joblib import load
import numpy as np
import matplotlib.patches as patches
from matplotlib.markers import MarkerStyle
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import math
import psycopg2
from sys import argv
import os
from dotenv import load_dotenv
from matplotlib.patches import Patch
load_dotenv()
connection_string = os.environ["connection_string"]


def create_football_field(fig, ax, line_color='white', field_color='green'):
    """Function that plots the football field for viewing players."""

    # set field dimensions
    plt.xlim(0, 120)
    plt.ylim(0, 53.3)

    # adding rectangles to the field
    for i in range(12):
        rect = patches.Rectangle((10 * i, 0), 10, 53.3, linewidth=1, edgecolor=line_color, facecolor=field_color)
        ax.add_patch(rect)

    # configure axes
    ax.tick_params(
        axis='both',
        which='both',
        direction='in',
        pad=-40,
        length=5,
        bottom=True,
        top=True,
        labeltop=True,
        labelbottom=True,
        left=False,
        right=False,
        labelleft=False,
        labelright=False,
        color=line_color)

    # set ticks on the side of the field
    ax.set_xticks([i for i in range(10, 111)])

    # setting yard marking
    label_set = []
    for i in range(1, 10):
        if i <= 5:
            label_set += [" " for j in range(9)] + [str(i * 10)]
        else:
            label_set += [" " for j in range(9)] + [str((10 - i) * 10)]
    label_set = [" "] + label_set + [" " for j in range(10)]
    ax.set_xticklabels(label_set, fontsize=20, color=line_color, zorder = 1)

    return fig, ax


def visualize_frame(game_id: int, play_id: int, home_color: str = 'cornflowerblue', away_color: str = 'coral'):
    """Visualize the crucial frame for a play"""
    model = load("distance.joblib")
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    fig, ax = plt.subplots(figsize=(12, 5.33))
    ax.clear()
    create_football_field(fig, ax)

    cur.execute("SELECT defensive_team FROM plays WHERE game_id=%s AND play_id=%s", (game_id, play_id))
    defensive_team = cur.fetchone()[0]

    cur.execute("SELECT player_id, team, orientation, x, y, speed, acceleration FROM tracking "
                "WHERE game_id=%s AND play_id=%s AND event='pass_arrived'", (game_id, play_id))
    step_info = cur.fetchall()
    cur.execute("SELECT x, y, lr FROM tracking t, plays p "
                "WHERE t.game_id=%s AND p.game_id=%s AND t.play_id=%s AND p.play_id=%s AND t.player_id=p.ball_carrier "
                "AND event='pass_arrived'",
                (game_id, game_id, play_id, play_id))
    ball_carrier = cur.fetchone()
    data = []
    for row in step_info:
        data.append([math.sqrt(abs(ball_carrier[1] - row[4])),  # Sqrt of lateral distance
                     math.sqrt(math.sqrt((ball_carrier[0] - row[3]) ** 2 + (ball_carrier[1] - row[4]) ** 2)),  # Sqrt of euclidean distance
                     row[5], row[6]])  # Speed and acceleration
    probabilities = model.predict_proba(data)

    # iterate step info to populate field
    home_team = None
    for i, row in enumerate(step_info):
        if row[0] == 1:
            color = "saddlebrown"
            ax.scatter(row[3], row[4], marker="d", s=100, color=color)
            continue
        if home_team is None:
            home_team = row[1]
        if row[1] == home_team:
            color = home_color
        else:
            color = away_color
        marker1 = MarkerStyle(r'$\spadesuit$')
        marker1._transform.rotate_deg(360 - row[2])
        if row[1] == defensive_team:
            ax.scatter(row[3], row[4], marker=marker1, s=150, color=color,
                       label="{0} - {1}".format(row[0] % 100, probabilities[i][1]), zorder=3)
            ax.text(row[3], row[4], str(row[0] % 100))
        else:
            ax.scatter(row[3], row[4], marker=marker1, s=150, color=color, zorder=2)

    # set axis title
    ax.set_title(f'Tracking data for {game_id} {play_id}')
    ax.legend()
    plt.savefig("play.png")
    conn.close()


def visualize_play(game_id: int, play_id: int, title_str: str):
    """Visualize a play from the dataset"""
    model = load("distance.joblib")
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    # Get max frame_id to find total length of the play
    cur.execute("SELECT MAX(frame_id) FROM tracking WHERE game_id=%s AND play_id=%s", (game_id, play_id))
    max_step = cur.fetchone()[0]
    frame_mod = 2
    og_frames = max_step // frame_mod
    interval_ms = 100 * frame_mod
    fig, ax = plt.subplots(figsize=(12, 5.33))

    # Find the frame_id of when the pass arrived
    cur.execute("SELECT frame_id FROM tracking WHERE game_id=%s AND play_id=%s AND event LIKE 'pass_arrived'",
                (game_id, play_id))
    pass_arrived_frame = cur.fetchone()[0] if cur.rowcount != 0 else None

    pause_duration_frames = 10

    # Increase the total number of frames to include the pause
    frames = og_frames + pause_duration_frames
    step_list = np.linspace(1, max_step, frames)

    cur.execute("SELECT player_id, team, orientation, x, y, speed, acceleration, p.name FROM tracking, players p "
                "WHERE player_id=%s AND game_id=%s AND play_id=%s AND event='pass_arrived' AND player_id=p.id",
                (argv[4], game_id, play_id))
    tackler = cur.fetchone()
    cur.execute("SELECT x, y, lr FROM tracking t, plays p "
                "WHERE t.game_id=%s AND p.game_id=%s AND t.play_id=%s AND p.play_id=%s AND t.player_id=p.ball_carrier "
                "AND event='pass_arrived'",
                (game_id, game_id, play_id, play_id))
    ball_carrier = cur.fetchone()
    # Repeat the data used to train the model
    data = [[math.sqrt(abs(ball_carrier[1] - tackler[4])),
             math.sqrt(math.sqrt((ball_carrier[0] - tackler[3]) ** 2 + (ball_carrier[1] - tackler[4]) ** 2)),
             tackler[5], tackler[6]]]
    probability = model.predict_proba(data)[0]

    def animate(i: int, game_id: int, play_id: int, frames: int, home_color: str = 'cornflowerblue',
                away_color: str = 'coral', home_text_color: str = 'white', away_text_color: str = 'white'):
        """Function to animate player tracking data"""
        ax.clear()
        create_football_field(fig, ax)

        home_patch = Patch(color=home_color, label=f'Home Team: New Orleans Saints')
        away_patch = Patch(color=away_color, label=f'Away Team: Cincinnati Bengals')

        legend = ax.legend(handles=[home_patch, away_patch],
                       loc='upper left', frameon=True, handlelength=0, handletextpad=0)
        legend.get_frame().set_facecolor('lightgray')  # Set the legend background color
        legend.get_frame().set_edgecolor('black')  # Optionally, set the legend border color
        legend.get_frame().set_alpha(0.8)  # Optionally, set the transparency of the background
        if pass_arrived_frame and pass_arrived_frame <= i <= pass_arrived_frame + pause_duration_frames:

            cur.execute("SELECT player_id, team, orientation, x, y, speed_x, speed_y, acc_x, acc_y, jerseynumber FROM tracking "
                        "WHERE game_id=%s AND play_id=%s AND frame_id=%s", (game_id, play_id, pass_arrived_frame))
            paused_step_info = cur.fetchall()
            home_team = None
            for row in paused_step_info:
                if row[0] == 1:
                    color = "saddlebrown"
                    ax.scatter(row[3], row[4], marker="d", s=100, color=color)
                    continue
                if home_team is None:
                    home_team = row[1]
                if row[1] == home_team:
                    color = home_color
                    text_color = home_text_color
                    player_zorder = 3
                else:
                    color = away_color
                    text_color = away_text_color
                    player_zorder = 2
                marker1 = MarkerStyle(r'o')
                marker1._transform.rotate_deg(360 - row[2])
                ax.scatter(row[3], row[4], marker=marker1, s=150, color=color, zorder = player_zorder)
                player_number = str(int(row[9]))
                ax.text(row[3], row[4], player_number, color = text_color, fontsize = 8, ha = 'center', va = 'center')

                if row[0] == int(argv[4]):  # If the current player is the "focused" player
                    circle = plt.Circle((row[3], row[4]), 1.5, color='yellow', fill=False, lw=2)
                    ax.add_patch(circle)
                    textstr = f"{tackler[-1]}: Tackle Probability: {round(probability[1] * 100, 2)}"
                    ax.annotate(textstr,
                            xy=(row[3], row[4]), xycoords='data',
                            xytext=(0.75, 0.83), textcoords='axes fraction',
                            arrowprops=dict(arrowstyle="->", connectionstyle="arc3"),
                            bbox=dict(boxstyle="round,pad=0.5", facecolor='wheat', edgecolor='black', alpha=0.5),
                            fontsize=12)
            ax.set_title(f"{title_str}", fontsize=14, fontweight='bold')
            return

        if i > (pass_arrived_frame + pause_duration_frames):
            i -= pause_duration_frames

        # create fresh field
        step = int(step_list[i])

        # subset data to step info
        cur.execute("SELECT player_id, team, orientation, x, y, speed_x, speed_y, acc_x, acc_y, jerseynumber FROM tracking "
                    "WHERE game_id=%s AND play_id=%s AND frame_id=%s", (game_id, play_id, step))
        step_info = cur.fetchall()

        # iterate step info to populate field
        home_team = None
        for row in step_info:
            if row[0] == 1:
                color = "saddlebrown"
                ax.scatter(row[3], row[4], marker="d", s=100, color=color)
                continue
            if home_team is None:
                home_team = row[1]
            if row[1] == home_team:
                color = home_color
                text_color = home_text_color
                player_zorder = 3
            else:
                color = away_color
                text_color = away_text_color
                player_zorder = 2
            marker1 = MarkerStyle(r'o')
            marker1._transform.rotate_deg(360 - row[2])
            ax.scatter(row[3], row[4], marker=marker1, s=150, color=color, zorder = player_zorder)
            player_number = str(int(row[9]))
            ax.text(row[3], row[4], player_number, color = text_color, fontsize = 8, ha = 'center', va = 'center')

        # set axis title
        ax.set_title(f"{title_str}", fontsize=14, fontweight='bold')

    anim = animation.FuncAnimation(fig, animate, fargs=(game_id, play_id, frames), frames=frames, repeat=False,
                                   interval=interval_ms)
    anim.save("{0}.gif".format(argv[5]), writer="imagemagick", fps=10)
    conn.close()


def visualize_speed(game_id: int, play_id: int, home_color: str = "cornflowerblue", away_color: str = "coral"):
    """Visualize speed vectors for a play"""
    conn = psycopg2.connect("dbname=BigDataBowl user=cschneider")
    cur = conn.cursor()
    fig, ax = plt.subplots(figsize=(12, 5.33))
    # create fresh field
    ax.clear()
    create_football_field(fig, ax)

    cur.execute("SELECT player_id, team, orientation, x, y, speed_x, speed_y FROM tracking "
                "WHERE game_id=%s AND play_id=%s AND event='handoff'", (game_id, play_id))
    info = cur.fetchall()

    # iterate step info to populate field
    home_team = None
    for row in info:
        if row[0] == 1:
            color = "saddlebrown"
            ax.scatter(row[3], row[4], marker="d", s=100, color=color)
            continue
        if home_team is None:
            home_team = row[1]
        if row[1] == home_team:
            color = home_color
        else:
            color = away_color
        marker1 = MarkerStyle(r'$\spadesuit$')
        marker1._transform.rotate_deg(360 - row[2])
        ax.scatter(row[3], row[4], marker=marker1, s=150, color=color)
        ax.arrow(row[3], row[4], row[5], row[6], color="firebrick", width=0.25)

    # set axis title
    ax.set_title(f'Tracking data for {game_id} {play_id}')
    plt.show()


if __name__ == "__main__":
    if argv[1] == "-p":
        # Get the play description before calling the function
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        cur.execute("SELECT play FROM plays WHERE game_id=%s AND play_id=%s", (argv[2], argv[3]))
        play_description = cur.fetchone()[0]
        play_description = play_description.split(")")[2][1:]
        play_description = play_description.split("(")[0][:-1]
        # Visualize the play
        visualize_play(int(argv[2]), int(argv[3]), play_description)
    elif argv[1] == "-v":
        visualize_speed(int(argv[2]), int(argv[3]))
