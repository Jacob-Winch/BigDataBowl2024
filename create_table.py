import pandas as pd 
import matplotlib.pyplot as plt 
import numpy as np
from plottable import ColumnDefinition, Table
from plottable.cmap import normed_cmap
from plottable.plots import image, circled_image
from plottable.formatters import decimal_to_percent
import psycopg2 as pg
import os
from dotenv import load_dotenv
import random
random.seed(73)

load_dotenv()
current_directory = os.environ["current_directory"]

def get_profile_picture_file_path(player):
    divided_name = player.split()
    return f"{current_directory}/profile_photos/{divided_name[0]}_{divided_name[1]}.png"

def get_players_table():
    """Get's the team and position of every defensive player in the NFL"""
    
    connection_string = os.environ["connection_string"]
    conn = pg.connect(connection_string)
    cur = conn.cursor()
    cur.execute("""SELECT DISTINCT p.id, p.name, t.team, p.position
                FROM players AS p
                JOIN tracking AS t ON p.id = t.player_id
                WHERE p.position IN (
                    'OLB', 'CB', 'SS', 'ILB', 'DT', 'FS',
                    'MLB', 'NT', 'DB', 'DE'
                    )
                """)
    defensive_players = cur.fetchall()
    cols = [
        "id",
        "Player",
        "Team",
        "Position"
    ]
    
    df = pd.DataFrame(defensive_players, columns = cols)

    df['logo'] = df['Team'].apply(
            lambda x: 
            f"{current_directory}/team_logos/{x}_logo.png"
        )
    df["profile_picture"] = np.nan
    df = df[['profile_picture', 'Player', 'logo', 'Team', 'Position']]
    bg_color = "#FFFFFF"
    text_color = "#000000"
    
    row_colors = {"#91C465", "D0F0C0", "F0FFF0", "F5FFFA"}
    
    plt.rcParams['text.color'] = text_color
    plt.rcParams['font.family'] = "monospace"
    df["tackles_above_expected"] = [round(random.uniform(-20, 20), 2) for _ in range(len(df))]
    # Add and populate dummy tackle type place holders 
    tackle_types = ["five_star", "four_star", "three_star", "two_star", "one_star", "total"]

    for tackle in tackle_types:
        tackles = [random.choices([0, 1, 2, 3], weights=[0.60, 0.20, 0.15, 0.05])[0] for _ in range(len(df))]
        df[f"{tackle}_tackles"] = tackles
        df[f"{tackle}_opportunities"] = [random.randrange(4, 100) for _ in range(len(df))]
        df[f"{tackle}_percentage"] = round(df[f"{tackle}_tackles"] / df[f"{tackle}_opportunities"], 2)


    mock_table = df.sort_values(by = "tackles_above_expected", ascending = False).head(10)
    mock_table['profile_picture'] = mock_table['Player'].apply(get_profile_picture_file_path)
    mock_table = mock_table.reset_index(drop = True)
    mock_table['Rank'] = mock_table["tackles_above_expected"].rank(ascending=False).astype(int)
    mock_table = mock_table[['Rank','profile_picture', 'Player', 'logo', 'Position',
       'tackles_above_expected', 'five_star_tackles', 'five_star_opportunities',
       'five_star_percentage', 'four_star_tackles', 'four_star_opportunities',
       'four_star_percentage', 'three_star_tackles', 'three_star_opportunities',
       'three_star_percentage', 'two_star_tackles', 'two_star_opportunities',
       'two_star_percentage', 'one_star_tackles', 'one_star_opportunities',
       'one_star_percentage', 'total_tackles', 'total_opportunities',
       'total_percentage']]

    col_defs = [
        ColumnDefinition(
            name = "Rank",
            textprops = {"ha": "center", "weight":"bold"},
            width = 0.4
        ),
        ColumnDefinition(
            name = "profile_picture",
            textprops = {"ha": "center", "va":"center", "color": bg_color},
            width = 0.5,
            plot_fn = circled_image
        ),
        ColumnDefinition(
            name = "Player",
            title = "Player",
            textprops = {"ha": "left", "weight":"bold"},
            width = 1.5,
        ),
        ColumnDefinition(
            name = "logo",
            title = "Team",
            textprops = {"ha": "center", "va":"center", "color": text_color},
            width = 0.5,
            plot_fn = image
        ),
        ColumnDefinition(
            name = "Position",
            textprops = {"ha": "center"},
            width = 0.5,
        ),
        ColumnDefinition(
            name = "tackles_above_expected",
            title = "TAE",
            textprops = {"ha": "center", "color": text_color, "weight":"bold", "bbox": {"boxstyle": "circle", "pad": .35}},
            cmap = normed_cmap(mock_table["tackles_above_expected"], cmap = plt.cm.PiYG, num_stds=2),
            width = 0.75,
        ),
        ColumnDefinition(
            name = "five_star_tackles",
            title = "Tk",
            group = "5 Star (0-25%)",
            textprops = {"ha": "center"},
            width = 0.5,
            border="left"
        ),
        ColumnDefinition(
            name = "five_star_opportunities",
            title = "Opp",
            group = "5 Star (0-25%)",
            textprops = {"ha": "center"},
            width = 0.5 
        ),
        ColumnDefinition(
            name = "five_star_percentage",
            title = "%",
            group = "5 Star (0-25%)",
            formatter=decimal_to_percent, 
            textprops = {"ha": "center"},
            width = 0.5 
        ),
            ColumnDefinition(
            name = "four_star_tackles",
            title = "Tk",
            group = "4 Star (26-50%)",
            textprops = {"ha": "center"},
            width = 0.5,
            border="left"
        ),
        ColumnDefinition(
            name = "four_star_opportunities",
            group = "4 Star (26-50%)",
            title = "Opp",
            textprops = {"ha": "center"},
            width = 0.5,
        ),
        ColumnDefinition(
            name = "four_star_percentage",
            group = "4 Star (26-50%)",
            title = "%",
            formatter=decimal_to_percent, 
            textprops = {"ha": "center"},
            width = 0.5 
        ),
            ColumnDefinition(
            name = "three_star_tackles",
            group = "3 Star (51-75%)",
            title = "Tk",
            textprops = {"ha": "center"},
            width = 0.5,
            border="left"
        ),
        ColumnDefinition(
            name = "three_star_opportunities",
            group = "3 Star (51-75%)",
            title = "Opp",
            textprops = {"ha": "center"},
            width = 0.5 
        ),
        ColumnDefinition(
            name = "three_star_percentage",
            group = "3 Star (51-75%)",
            title = "%",
            formatter=decimal_to_percent, 
            textprops = {"ha": "center"},
            width = 0.5 
        ),
            ColumnDefinition(
            name = "two_star_tackles",
            group = "2 Star (76-90%)",
            title = "Tk",
            textprops = {"ha": "center"},
            width = 0.5,
            border="left"
        ),
        ColumnDefinition(
            name = "two_star_opportunities",
            group = "2 Star (76-90%)",
            title = "Opp",
            textprops = {"ha": "center"},
            width = 0.5 
        ),
        ColumnDefinition(
            name = "two_star_percentage",
            group = "2 Star (76-90%)",
            title = "%",
            formatter=decimal_to_percent, 
            textprops = {"ha": "center"},
            width = 0.5 
        ),
            ColumnDefinition(
            name = "one_star_tackles",
            group = "1 Star (91-95%)",
            title = "Tk",
            textprops = {"ha": "center"},
            width = 0.5,
            border="left"    
        ),
        ColumnDefinition(
            name = "one_star_opportunities",
            group = "1 Star (91-95%)",
            title = "Opp",
            textprops = {"ha": "center"},
            width = 0.5 
        ),
        ColumnDefinition(
            name = "one_star_percentage",
            group = "1 Star (91-95%)",
            title = "%",
            formatter=decimal_to_percent,
            textprops = {"ha": "center"},
            width = 0.5 
        ),
            ColumnDefinition(
            name = "total_tackles",
            group = "Total",
            title = "Tk",
            textprops = {"ha": "center"},
            width = 0.5,
            border="left"
        ),
        ColumnDefinition(
            name = "total_opportunities",
            group = "Total",
            title = "Op",
            textprops = {"ha": "center"},
            width = 0.5 
        ),
        ColumnDefinition(
            name = "total_percentage",
            group = "Total",
            title = "%",
            formatter=decimal_to_percent,
            textprops = {"ha": "center"},
            width = 0.5 
        )
        
    ]

    fig, ax = plt.subplots(figsize=(20,20))
    fig.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    table = Table(
        mock_table,
        column_definitions = col_defs,
        index_col = "Rank",
        row_dividers = True,
        row_divider_kw = {"linewidth":1, "linestyle": (0, (1,5))},
        footer_divider = True, 
        textprops = {"fontsize":14},
        ax = ax
    ).autoset_fontcolors(colnames=["tackles_above_expected"])
    plt.show()

if __name__ == "__main__":
    get_players_table()
    