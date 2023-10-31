import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.markers import MarkerStyle
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import psycopg2
from sys import argv


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
    ax.set_xticklabels(label_set, fontsize=20, color=line_color)

    return fig, ax


def visualize_play(game_id: int, play_id: int):
    """Visualize a play from the dataset"""
    conn = psycopg2.connect("dbname=BigDataBowl user=cschneider")
    cur = conn.cursor()
    cur.execute("SELECT MAX(frame_id) FROM tracking WHERE game_id=%s AND play_id=%s", (game_id, play_id))
    frames = cur.fetchone()[0]
    frame_mod = 2
    frames = frames // frame_mod
    interval_ms = 100 * frame_mod
    fig, ax = plt.subplots(figsize=(12, 5.33))

    def animate(i: int, game_id: int, play_id: int, frames: int, home_color: str = 'cornflowerblue',
                away_color: str = 'coral'):
        """Function to animate player tracking data"""
        # create fresh field
        ax.clear()
        create_football_field(fig, ax)

        # find appropriate
        cur.execute("SELECT MAX(frame_id) FROM tracking WHERE game_id=%s AND play_id=%s", (game_id, play_id))
        max_step = cur.fetchone()[0]
        step_list = np.linspace(1, max_step, frames)
        step = int(step_list[i])

        # subset data to step info
        cur.execute("SELECT player_id, team, orientation, x, y, speed_x, speed_y, acc_x, acc_y FROM tracking "
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
            else:
                color = away_color
            marker1 = MarkerStyle(r'$\spadesuit$')
            marker1._transform.rotate_deg(360 - row[2])
            ax.scatter(row[3], row[4], marker=marker1, s=150, color=color)

        # set axis title
        ax.set_title(f'Tracking data for {game_id} {play_id} at step {step}')

    anim = animation.FuncAnimation(fig, animate, fargs=(game_id, play_id, frames), frames=frames, repeat=False,
                                   interval=interval_ms)
    anim.save("play.gif", writer="imagemagick", fps=10)
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
        visualize_play(int(argv[2]), int(argv[3]))
    elif argv[1] == "-v":
        visualize_speed(int(argv[2]), int(argv[3]))
