# Tackles Above Average: Determining Tackle Probability at the Moment of a Catch
Are the current measurements of total tackles and number of missed tackles a great representation and indication of individual tackling skill? Although these statistics are informative, they do not provide the context around the tackle as they equally weigh each tackle. For example, a tackle could be hard to make as the player could be far away from the play, but the tackler swoops in to secure the ball carrier against high odds. Rather than measuring individuals by total tackles, we aim to quantify each tackle's difficulty to understand better a defender's true skill level and contribution to the game, ensuring that each play is evaluated in the context of its unique circumstances and challenges. 

We aim to predict a defender’s probability of tackling a ball carrier based on their position and distance away from the ball while factoring in speed and acceleration. The inspiration for this project comes from Baseball Savant’s outs above-average (OAA) metric. This metric focuses on an outfielder's ability to convert fly balls into outs relative to his peers. Similarly, we want to focus on a defensive player's ability to make tackles that an average NFL defender would not be expected to make. We accomplish this given a set of criteria describing a play, such as distance and speed. Expected tackle models can be useful tools for professionals and coaches to help identify individual players who thrive on tackling more than expected or vice versa, pinpoint players who miss tackles they should make. Ultimately, we want to contextualize and quantify the tackling statistics to be more informative and useful than current counting measurements. 

### Submission for the 2024 NFL Big Data Bowl - Undergraduate Track
### Team North | University of Alberta

Jacob Winch, Statistics Undergraduate Student | [Linkedin](https://www.linkedin.com/in/jacob-winch/)

Colton Schneider, Computer Science Undergraduate Student | [Linkedin](https://www.linkedin.com/in/colton-schneider-272940201/)

Siddhartha Chitrakar, Mathematics and Computer Undergraduate Student | [Linkedin](https://www.linkedin.com/in/siddhartha-chitrakar/)

## Repository Directory
### Figures
- The figures folder contains all of the tables and gifs used in our report.
  
### code
- The code directory contains all of the Python scripts used to build our report. The files are described below:
  - `build_model.py`: Our Logistic Regression model to determine tackling probability. Also determines the stars of a given tackle.
  - `chart_play.py`: Creates the gifs to visualize the tackling probability of a specific player on a given play.
  - `create_db.py`: Creates a PostgreSQL database from the NFL Big Data Bowl 2024 CSV files.
  - `table_code`: Creates the tables used in the report.

### data
- Additional CSV files that contain the TAA data for both players and teams. 
### profile_photos
- All of the profile photos of players used in the tables in our report. All of the profile photos were taken from ESPN's player roster pages.

### team_logos
- All of the team logo photos used in the tables in our report. All of the team logos were taken from Wikipedia's NFL team pages.

## Bibliography
@misc{nfl-big-data-bowl-2024,
    author = {Michael Lopez, Thompson Bliss, Ally Blake, Andrew Patton, Jonathan McWilliams, Addison Howard, Will Cukierski},
    title = {NFL Big Data Bowl 2024},
    publisher = {Kaggle},
    year = {2023},
    url = {https://kaggle.com/competitions/nfl-big-data-bowl-2024}
}
