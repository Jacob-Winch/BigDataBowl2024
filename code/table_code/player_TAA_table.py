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


load_dotenv()
current_directory = os.environ["current_directory"]

players_TAA = pd.read_csv("data\players.csv")

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
players_with_team = pd.DataFrame(defensive_players, columns = cols)

players_TAA = pd.merge(players_TAA, players_with_team[['id', 'Team']], on='id', how='left')

players_TAA['logo'] = players_TAA['Team'].apply(
        lambda x: 
    f"{current_directory}/team_logos/{x}_logo.png"
    )

players_TAA.rename(columns = {'tackles_above_expected': 'tackles_above_average'}, inplace = True)

players_TAA = players_TAA.sort_values(by = 'tackles_above_average', ascending = False)

players_TAA = players_TAA.drop('id', axis = 1)
players_TAA = players_TAA.reset_index(drop = True)
players_TAA.index += 1
players_TAA['Rank'] = players_TAA.index

top_10_players_TAA = players_TAA.head(10)

bottom_10_players_TAA = players_TAA.tail(10)

bobby_wagner = players_TAA[players_TAA['name'] == 'Bobby Wagner']

top_10_players_TAA_plus_bobby_wagner = pd.concat([top_10_players_TAA, bobby_wagner])

def get_profile_picture_file_path(player):
    divided_name = player.split()
    return f"{current_directory}/profile_photos/{divided_name[0]}_{divided_name[1]}.png"

top_10_players_TAA_plus_bobby_wagner['profile_picture'] = top_10_players_TAA_plus_bobby_wagner['name'].apply(get_profile_picture_file_path)

bottom_10_players_TAA['profile_picture'] = bottom_10_players_TAA['name'].apply(get_profile_picture_file_path)

top_10_players_TAA_plus_bobby_wagner['5_star_opportunities'] = top_10_players_TAA_plus_bobby_wagner['star_5_made'] + top_10_players_TAA_plus_bobby_wagner['star_5_missed']
top_10_players_TAA_plus_bobby_wagner['4_star_opportunities'] = top_10_players_TAA_plus_bobby_wagner['star_4_made'] + top_10_players_TAA_plus_bobby_wagner['star_4_missed']
top_10_players_TAA_plus_bobby_wagner['3_star_opportunities'] = top_10_players_TAA_plus_bobby_wagner['star_3_made'] + top_10_players_TAA_plus_bobby_wagner['star_3_missed'] 
top_10_players_TAA_plus_bobby_wagner['2_star_opportunities'] = top_10_players_TAA_plus_bobby_wagner['star_2_made'] + top_10_players_TAA_plus_bobby_wagner['star_2_missed'] 
top_10_players_TAA_plus_bobby_wagner['1_star_opportunities'] = top_10_players_TAA_plus_bobby_wagner['star_1_made'] + top_10_players_TAA_plus_bobby_wagner['star_1_missed'] 

top_10_players_TAA_plus_bobby_wagner['total_tackles'] = top_10_players_TAA_plus_bobby_wagner['star_1_made'] + top_10_players_TAA_plus_bobby_wagner['star_2_made'] + top_10_players_TAA_plus_bobby_wagner['star_3_made'] + top_10_players_TAA_plus_bobby_wagner['star_4_made'] + top_10_players_TAA_plus_bobby_wagner['star_5_made']
top_10_players_TAA_plus_bobby_wagner['total_opps'] = top_10_players_TAA_plus_bobby_wagner['5_star_opportunities'] + top_10_players_TAA_plus_bobby_wagner['4_star_opportunities'] + top_10_players_TAA_plus_bobby_wagner['3_star_opportunities'] + top_10_players_TAA_plus_bobby_wagner['2_star_opportunities'] + top_10_players_TAA_plus_bobby_wagner['1_star_opportunities']
top_10_players_TAA_plus_bobby_wagner['total_pct'] = top_10_players_TAA_plus_bobby_wagner['total_tackles'] / top_10_players_TAA_plus_bobby_wagner['total_opps']

top_10_players_TAA_plus_bobby_wagner = top_10_players_TAA_plus_bobby_wagner[[
    'Rank', 'profile_picture', 'name', 'logo', 'position', 'tackles_above_average',
    'star_5_made', '5_star_opportunities', 'star_5_pct',
    'star_4_made', '4_star_opportunities', 'star_4_pct',
    'star_3_made', '3_star_opportunities', 'star_3_pct',
    'star_2_made', '2_star_opportunities', 'star_2_pct',
    'star_1_made', '1_star_opportunities', 'star_1_pct',
    'total_tackles', 'total_opps', 'total_pct'
]]

top_10_players_TAA_plus_bobby_wagner['tackles_above_average'] = top_10_players_TAA_plus_bobby_wagner['tackles_above_average'].round(2)


bg_color = "#FFFFFF"
text_color = "#000000"
    
row_colors = {"#91C465", "D0F0C0", "F0FFF0", "F5FFFA"}
    
plt.rcParams['text.color'] = text_color
plt.rcParams['font.family'] = "monospace"

top_10_players_TAA = top_10_players_TAA_plus_bobby_wagner[top_10_players_TAA_plus_bobby_wagner['name'] != 'Bobby Wagner']

bobby_wagner_TAA = top_10_players_TAA_plus_bobby_wagner[top_10_players_TAA_plus_bobby_wagner['name'] == 'Bobby Wagner']

col_defs = [
    ColumnDefinition(
        name = "Rank",
        textprops = {"ha": "center", "weight":"bold"},
        width = 0.4
    ),
    ColumnDefinition(
        name = "profile_picture",
        title = "",
        textprops = {"ha": "center", "va":"center", "color": bg_color},
        width = 0.4,
        plot_fn = circled_image
    ),
    ColumnDefinition(
        name = "name",
        title = "Player",
        textprops = {"ha": "left", "weight":"bold"},
        width = 1.5,
    ),
      ColumnDefinition(
        name = "logo",
        title = "Team",
        textprops = {"ha": "center", "va":"center", "color": text_color},
        width = 0.65,
        plot_fn = image
    ),
    ColumnDefinition(
        name = "position",
        title = "Pos.",
        textprops = {"ha": "center"},
        width = 0.4,
    ),
    ColumnDefinition(
        name = "tackles_above_average",
        title = "TAA",
        textprops = {"ha": "center", 
                     "color": text_color, 
                     "weight":"bold", 
                     "bbox": {"boxstyle": "circle", "pad": .2}
                    },
        cmap = normed_cmap(bottom_10_players_TAA["tackles_above_average"], cmap = plt.cm.Reds.reversed(), num_stds=2),
        width = 0.5,
        formatter =  lambda x: "{:.2f}".format(x)
    ),
    ColumnDefinition(
        name = "star_5_made",
        title = "Tk",
        group = "5 Star",
        textprops = {"ha": "center"},
        width = 0.32,
        border="left"
    ),
     ColumnDefinition(
        name = "5_star_opportunities",
        title = "Opp",
        group = "5 Star",
        textprops = {"ha": "center"},
        width = 0.32
    ),
     ColumnDefinition(
        name = "star_5_pct",
        title = "%",
        group = "5 Star",
        formatter=decimal_to_percent, 
        textprops = {"ha": "center"},
        width = 0.42 
    ),
        ColumnDefinition(
        name = "star_4_made",
        title = "Tk",
        group = "4 Star",
        textprops = {"ha": "center"},
        width = 0.32,
        border="left"
    ),
     ColumnDefinition(
        name = "4_star_opportunities",
        group = "4 Star",
        title = "Opp",
        textprops = {"ha": "center"},
        width = 0.32,
    ),
     ColumnDefinition(
        name = "star_4_pct",
        group = "4 Star",
        title = "%",
        formatter=decimal_to_percent, 
        textprops = {"ha": "center"},
        width = 0.42
    ),
        ColumnDefinition(
        name = "star_3_made",
        group = "3 Star",
        title = "Tk",
        textprops = {"ha": "center"},
        width = 0.32,
        border="left"
    ),
     ColumnDefinition(
        name = "3_star_opportunities",
        group = "3 Star",
        title = "Opp",
        textprops = {"ha": "center"},
        width = 0.32 
    ),
     ColumnDefinition(
        name = "star_3_pct",
        group = "3 Star",
        title = "%",
        formatter=decimal_to_percent, 
        textprops = {"ha": "center"},
        width = 0.42
    ),
        ColumnDefinition(
        name = "star_2_made",
        group = "2 Star",
        title = "Tk",
        textprops = {"ha": "center"},
        width = 0.32,
        border="left"
    ),
     ColumnDefinition(
        name = "2_star_opportunities",
        group = "2 Star",
        title = "Opp",
        textprops = {"ha": "center"},
        width = 0.32
    ),
     ColumnDefinition(
        name = "star_2_pct",
        group = "2 Star",
        title = "%",
        formatter=decimal_to_percent, 
        textprops = {"ha": "center"},
        width = 0.42
    ),
        ColumnDefinition(
        name = "star_1_made",
        group = "1 Star",
        title = "Tk",
        textprops = {"ha": "center"},
        width = 0.32,
        border="left"    
    ),
     ColumnDefinition(
        name = "1_star_opportunities",
        group = "1 Star",
        title = "Opp",
        textprops = {"ha": "center"},
        width = 0.32 
    ),
     ColumnDefinition(
        name = "star_1_pct",
        group = "1 Star",
        title = "%",
        formatter=decimal_to_percent,
        textprops = {"ha": "center"},
        width = 0.42
    ),
        ColumnDefinition(
        name = "total_tackles",
        group = "Total",
        title = "Tk",
        textprops = {"ha": "center"},
        width = 0.32,
        border="left"
    ),
     ColumnDefinition(
        name = "total_opps",
        group = "Total",
        title = "Op",
        textprops = {"ha": "center"},
        width = 0.32
    ),
     ColumnDefinition(
        name = "total_pct",
        group = "Total",
        title = "%",
        formatter=decimal_to_percent,
        textprops = {"ha": "center"},
        width = 0.32
    )
    
]

fig, ax = plt.subplots(figsize=(17,12))
fig.set_facecolor(bg_color)
ax.set_facecolor(bg_color)

table = Table(
    top_10_players_TAA,
    column_definitions = col_defs,
    index_col = "Rank",
    row_dividers = True,
    row_divider_kw = {"linewidth":1, "linestyle": (0, (1,5))},
    footer_divider = True, 
    textprops = {"fontsize":10},
    ax = ax
).autoset_fontcolors(colnames=["tackles_above_average"])
#fig.savefig('figures/top_10_TAA_2.png', facecolor = ax.get_facecolor(), dpi = 400)
plt.show()

fig, ax = plt.subplots(figsize=(17,2.5))
fig.set_facecolor(bg_color)
ax.set_facecolor(bg_color)

table = Table(
    bobby_wagner_TAA,
    column_definitions = col_defs,
    index_col = "Rank",
    row_dividers = True,
    row_divider_kw = {"linewidth":1, "linestyle": (0, (1,5))},
    footer_divider = True, 
    textprops = {"fontsize":10},
    ax = ax
).autoset_fontcolors(colnames=["tackles_above_average"])
#fig.savefig('figures/bobby_wagner_TAA_2.png', facecolor = ax.get_facecolor(), dpi = 400)
plt.show()

bottom_10_players_TAA['5_star_opportunities'] = bottom_10_players_TAA['star_5_made'] + bottom_10_players_TAA['star_5_missed']
bottom_10_players_TAA['4_star_opportunities'] = bottom_10_players_TAA['star_4_made'] + bottom_10_players_TAA['star_4_missed']
bottom_10_players_TAA['3_star_opportunities'] = bottom_10_players_TAA['star_3_made'] + bottom_10_players_TAA['star_3_missed'] 
bottom_10_players_TAA['2_star_opportunities'] = bottom_10_players_TAA['star_2_made'] + bottom_10_players_TAA['star_2_missed'] 
bottom_10_players_TAA['1_star_opportunities'] = bottom_10_players_TAA['star_1_made'] + bottom_10_players_TAA['star_1_missed'] 

bottom_10_players_TAA['total_tackles'] = bottom_10_players_TAA['star_1_made'] + bottom_10_players_TAA['star_2_made'] + bottom_10_players_TAA['star_3_made'] + bottom_10_players_TAA['star_4_made'] + bottom_10_players_TAA['star_5_made']
bottom_10_players_TAA['total_opps'] = bottom_10_players_TAA['5_star_opportunities'] + bottom_10_players_TAA['4_star_opportunities'] + bottom_10_players_TAA['3_star_opportunities'] + bottom_10_players_TAA['2_star_opportunities'] + bottom_10_players_TAA['1_star_opportunities']
bottom_10_players_TAA['total_pct'] = bottom_10_players_TAA['total_tackles'] / bottom_10_players_TAA['total_opps']

bottom_10_players_TAA = bottom_10_players_TAA[[
    'Rank', 'profile_picture', 'name', 'logo', 'position', 'tackles_above_average',
    'star_5_made', '5_star_opportunities', 'star_5_pct',
    'star_4_made', '4_star_opportunities', 'star_4_pct',
    'star_3_made', '3_star_opportunities', 'star_3_pct',
    'star_2_made', '2_star_opportunities', 'star_2_pct',
    'star_1_made', '1_star_opportunities', 'star_1_pct',
    'total_tackles', 'total_opps', 'total_pct'
]]

bottom_10_players_TAA['tackles_above_average'] = bottom_10_players_TAA['tackles_above_average'].round(2)

fig, ax = plt.subplots(figsize=(17,12))
fig.set_facecolor(bg_color)
ax.set_facecolor(bg_color)

table = Table(
    bottom_10_players_TAA,
    column_definitions = col_defs,
    index_col = "Rank",
    row_dividers = True,
    row_divider_kw = {"linewidth":1, "linestyle": (0, (1,5))},
    footer_divider = True, 
    textprops = {"fontsize":10},
    ax = ax
).autoset_fontcolors(colnames=["tackles_above_average"])
fig.savefig('figures/bottom_10_TAA_2.png', facecolor = ax.get_facecolor(), dpi = 400)
plt.show()



