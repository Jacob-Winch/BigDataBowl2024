import pandas as pd 
import matplotlib.pyplot as plt 
import numpy as np
from plottable import ColumnDefinition, Table
from plottable.cmap import normed_cmap
from plottable.plots import image, circled_image, bar
from plottable.formatters import decimal_to_percent
import os
from dotenv import load_dotenv
load_dotenv()
current_directory = os.environ["current_directory"]

teams = pd.read_csv("data/teams.csv")

teams_TAA = teams[teams['name'] != 'FB']

teams_TAA['logo'] = teams_TAA['name'].apply(
        lambda x: 
    f"{current_directory}/team_logos/{x}_logo.png"
    )

team_abbr_mapping = {
    'ARI': 'Arizona Cardinals',
    'ATL': 'Atlanta Falcons',
    'BAL': 'Baltimore Ravens',
    'BUF': 'Buffalo Bills',
    'CAR': 'Carolina Panthers',
    'CHI': 'Chicago Bears',
    'CIN': 'Cincinnati Bengals',
    'CLE': 'Cleveland Browns',
    'DAL': 'Dallas Cowboys',
    'DEN': 'Denver Broncos',
    'DET': 'Detroit Lions',
    'GB': 'Green Bay Packers',
    'HOU': 'Houston Texans',
    'IND': 'Indianapolis Colts',
    'JAX': 'Jacksonville Jaguars',
    'KC': 'Kansas City Chiefs',
    'LV': 'Las Vegas Raiders',
    'LAC': 'Los Angeles Chargers',
    'LA': 'Los Angeles Rams',
    'MIA': 'Miami Dolphins',
    'MIN': 'Minnesota Vikings',
    'NE': 'New England Patriots',
    'NO': 'New Orleans Saints',
    'NYG': 'New York Giants',
    'NYJ': 'New York Jets',
    'PHI': 'Philadelphia Eagles',
    'PIT': 'Pittsburgh Steelers',
    'SEA': 'Seattle Seahawks',
    'SF': 'San Francisco 49ers',
    'TB': 'Tampa Bay Buccaneers',
    'TEN': 'Tennessee Titans',
    'WAS': 'Washington Commanders'
}

teams_TAA['full_team_name'] = teams_TAA['name'].map(team_abbr_mapping)

teams_TAA.rename(columns = {'tackles_above_expected': 'tackles_above_average'}, inplace = True)

teams_TAA = teams_TAA.sort_values(by = 'tackles_above_average', ascending = False)

teams_TAA = teams_TAA.drop('id', axis = 1)

teams_TAA = teams_TAA.reset_index(drop = True)

teams_TAA.index += 1

teams_TAA['Rank'] = teams_TAA.index

teams_TAA = teams_TAA[['Rank', 'logo', 'full_team_name', 'tackles_above_average']]

bg_color = "#FFFFFF"
text_color = "#000000"
    
row_colors = {"#91C465", "D0F0C0", "F0FFF0", "F5FFFA"}
    
plt.rcParams['text.color'] = text_color
plt.rcParams['font.family'] = "monospace"
cmap = normed_cmap(teams_TAA["tackles_above_average"], cmap = plt.cm.PiYG, num_stds = 2.5)

def plot_total_TAA_bar(ax, val, height, cmap, width = 0.4):
    """Plots TAA bar on the plottable table

    Args:
        ax : matplotlib axis
        val (float): value to be plotted
        height : height of bar
        cmap : matplotlib color map
        width (float, optional): width of bar Defaults to 0.5.
    """
    color = cmap(val)
    ax.barh(y=[0], width=[val], color=color, height=height)
    ax.set_xlim(-15.5, 15)  
    ax.axis('off')  
    ax.text(val if val >= 0 else val - 0.5, 0, f'{val:.2f}', 
            va='center', ha='right' if val < 0 else 'left', fontweight='bold')
    
col_defs = [
    ColumnDefinition(
        name = "Rank",
        textprops = {"ha": "center", "weight":"bold"},
        width = 0.1
    ),
    ColumnDefinition(
        name = "logo",
        title = "Team",
        textprops = {"ha": "center", "va":"center", "weight":"bold", "color": text_color},
        width = 0.1,
        plot_fn = image
    ),
    ColumnDefinition(
        name = "full_team_name",
        title = "",
        textprops = {"ha": "left", "va":"center", "weight":"bold", "color": text_color},
        width = 0.5,
    ),
    ColumnDefinition(
        name = "tackles_above_average",
        title = "Cumulative Tackles Above Average (cTAA)",
        textprops = {"ha": "center", "va":"center", "weight":"bold", "color": text_color},
        width = 1.25,
        plot_fn = plot_total_TAA_bar,
        plot_kw = {
            "height": 0.4,
            "cmap": cmap
        }
    )
]

fig, ax = plt.subplots(figsize=(17,15))
fig.set_facecolor(bg_color)
ax.set_facecolor(bg_color)
table = Table(
    teams_TAA,
    column_definitions = col_defs,
    index_col = "Rank",
    row_dividers = True,
    row_divider_kw = {"linewidth":1, "linestyle": (0, (1,5))},
    footer_divider = True, 
    textprops = {"fontsize":10},
    ax = ax
).autoset_fontcolors(colnames=["tackles_above_average"])
    
fig.savefig('team_TAA.png', facecolor = ax.get_facecolor(), dpi = 400)
    
plt.show()

