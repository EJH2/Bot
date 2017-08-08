# ViralBot

ViralBot is yet another Multipurpose Python bot (TM) for Discord. It has many commands that are sure to keep the chat 
alive. New features are added often, so be on the lookout for the latest commands!

Any questions should be directed to `EJH2#0330` on [**this cool Discord server**](https://discord.gg/4fKgwPn 
"Gears of Bots").

If you want to run your own ViralBot, please follow the installation steps below:

## Setting up the bot

Before you continue, you will need 2 things:

 - Python 3.6+ 
 - PostgreSQL 9.6 or higher

### Installation Instructions

1. **Download the bot.**

    On the main GitHub Page, click the green "Clone or Download" button, and click Download ZIP. Once it's finished 
    installing, unzip the bot in any place you like.
    
2. **Install the requirements.**

    Open up a terminal, navigate to the folder you put your bot in, and run 
    `python3.6 -m pip install -r requirements.txt`
    
    *Note: Make sure to keep this terminal open, we'll need it later.*
    
3. **Create a PostgreSQL database.**

    This is so we can use features like Dynamic Rules and Logging. If you don't want to use these features, you can
    always disable them in the config.
    
    It's recommended you pick something secure, but for the sake of this tutorial, I'll go with something basic.
    
    ```sql
    CREATE ROLE admin WITH LOGIN PASSWORD 'admin';
    CREATE DATABASE viralbot OWNER admin;
    ```

4. **Run the migrations**

    The migration scripts upgrade the database to the latest version. Run this in the terminal.

     `PYTHONPATH=. asql-migrate migrate`
     
5. **Create a config.**

    On startup for the first time, if the bot doesn't detect a `config.yaml`, it'll auto create one. So just run the
    bot and it'll create a config for you. See step 7 on how to start the bot.
    
6. **Edit the config.**

    For the bot to work, you at least have to have 5 values:
    
    - token
    - command_prefix
    - pg_name
    - pg_user
    - pg_pass
    
7. **Run the bot.**

    You can start the bot by doing `python3.6 bot.py`. If you want to start it in debug mode, you can do
    `python3.6 bot.py debug`
    
### Updating Instructions


Sometimes I will make bug fixes that were left over from previous commits, in which case you'll need to re-pull the repo
to your computer and just copy over the config. In a rare case I might need to re-configure the database, in which case
you will need to issue two commands in a terminal:

1. `PYTHONPATH=. asql-migrate migrate -- -1`

2. `PYTHONPATH=. asql-migrate migrate -- 1`

Done!
    
## Contributing to ViralBot

Contibutions alre always welcome! A copy of guidelines to follow when contributing to the project can be found 
[**here**](https://github.com/EJH2/ViralBot/blob/8806486c46af1a6221c8e3f5366d94ef1acffae8/CONTRIBUTING.md 
"CONTRIBUTING.md").