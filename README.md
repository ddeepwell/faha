# Fantasy Hockey Analysis (FAHA)

A simple analysis tool to explore fantasy player statistics.

Much appreciation to the following repo:
https://github.com/bbenbenek/nfl-fantasy-football



# Getting started

1. Register for Yahoo Developer Network and get your credentials:
    1) Register for a  Yahoo account at https://yahoo.com/
    2) Go to https://developer.yahoo.com/ --> 'My Apps' --> 'YDN Apps'
    3) On the lefthand panel, click 'Create an App'
    4) Name your app whatever you please ("Fantasy Football Stats") in the 'Application Name' block.
    5) Select the 'Installed Application' option since we're only going to be accessing the data from our local machines.
    6) Under the 'API Permissions' sections select 'Fantasy Sports' and then make sure that 'Read' is selected. 'Read/Write' would only be used if you wanted to be able to control your league via Python scripting vice just reading the data from your league. You can come back and change these options in the future.
    7) You have now successfully created a Yahoo Developer App and you will see `App ID`, `Client ID(Consumer Key)`, and `Client Secret(Consumer Secret)` with a long string of random letters and numbers. Yahoo will use these keys to allow you to access it's API via OAuth 2.0.
2. Add client keys.
    1) Using the Consumer Key and Consumer Secret, execute `initialize_tokens` to add these to the project. This will open a web browser with a short key. Copy and paste the key into the terminal when requested.
3. Get league information and ID
    1) Get the league ID. This can be found in your league's unique Yahoo Fantasy URL: "https://hockey.fantasysports.yahoo.com/hockey/XXXXX". Execute `input_league_id` and follow the prompts with this ID number and the season's starting year.
    2) Get the league info. Execute `get_league_info`
