import os # idk what this does
import asyncio
import sqlite3 # IMPORT SQL
import discord #import discord tools
from dotenv import load_dotenv # load .env loader for environment variables

load_dotenv() # spawn tool
connection = sqlite3.connect("myTable.db")
cursor = connection.cursor()
client = discord.Client() # connect the bot to discord

async def sayhi(message): # Say Hi Command.
    await message.channel.send('Hi')
    return

async def registerMe(message):
    print(message.author.id)
    cursor.execute(f"""SELECT UID FROM UserInfo WHERE UID={message.author.id}  ;""")

    if (cursor.fetchone() != None):
        await message.channel.send('You\'re already registered. Fuck off.')
        return
    else:
        cursor.execute(f"""INSERT INTO UserInfo (UID, DisplayName, Rating, Challenging, inBattle, HP, ATK, SPD, Action1, Action2, Action3, Action4)
                           VALUES ('{message.author.id}', '{message.author.name}', 100, 'None', 0, 10,3,5,'None','None','None','None');""")
        connection.commit()
        await message.channel.send(f'You\'ve been registered with ID: {message.author.id} and DisplayName: {message.author.name} ')

    return

async def showInfo(message):
    cursor.execute(f"""SELECT displayName, Rating, HP, ATK, SPD, Action1, Action2, Action3, Action4 FROM UserInfo WHERE UID={message.author.id}  ;""")
    info = cursor.fetchone()

    await message.channel.send(f'Here\'s your info:\nName: {info[0]} | Rating: {info[1]}\n---Stats---\n**HP:** {info[2]} | **ATK:** {info[3]} | **SPD:** {info[4]}'
                               f'\nAbilities:\n1. {info[5]}\n2. {info[6]}\n3. {info[7]}\n4. {info[8]}')

    return

async def challenge(message):
    # Check if challenge request has more than one person listed.
    if (len(message.mentions) > 1):
        await message.channel.send('Cannot challenge more than one person. Fuck off.')
    # ---

    # If challenge request has only one person listed.
    elif (len(message.mentions)==1):
        # Take player IDs and move them to variable.
        challenger = str(message.author.id)
        challenged = str(message.mentions[0].id)
        # ---
        # Check if challenged player is already in combat. Return if so.
        cursor.execute(f"""SELECT inBattle FROM UserInfo WHERE UID={challenged}  ;""")
        battleStatus = int(cursor.fetchone()[0])
        if (battleStatus == 1):
            await message.channel.send('That person is already in the heat of combat! Try again later.')
            return
        # ---

        # Set challenger's "Challenging" value to the ID of the challenged.
        cursor.execute(f"""UPDATE UserInfo SET Challenging = {challenged} WHERE UID={challenger}  ;""")
        connection.commit()
        # ---

        # Check if challengee is already challenging the challenger. If so, start the fight.
        cursor.execute(f"""SELECT Challenging FROM UserInfo WHERE UID={challenged};""")
        whoIsChallengedChallenging = str(cursor.fetchone()[0])

        if (whoIsChallengedChallenging == challenger):
            await message.channel.send(f'Combat between **{message.author.name}** and **{message.mentions[0].name}** has started.')

            # Set the player's inBattle status to 1.
            cursor.execute(f"""UPDATE UserInfo SET inBattle = 1 WHERE (UID={challenger});""")
            connection.commit()
            cursor.execute(f"""UPDATE UserInfo SET inBattle = 1 WHERE (UID={challenged});""")
            connection.commit()

            # Load all the stats from the players and put them into the battle instance.
            cursor.execute(f"""SELECT UID, HP, ATK, SPD FROM UserInfo WHERE UID={challenged};""")
            p1Stats = cursor.fetchone()
            cursor.execute(f"""SELECT UID, HP, ATK, SPD FROM UserInfo WHERE UID={challenger};""")
            p2Stats = cursor.fetchone()

            # Create Combat Instance!

            battleGround = message.channel.id

            cursor.execute(
                f"""INSERT INTO BattleInfo (p1UID, p2UID, p1HP, p2HP, p1MP, p2MP, p1ATK, p2ATK, p1SPD, p2SPD, p1Action, p2Action, rndCounter, goingNext, battleGround)
                                       VALUES ('{p1Stats[0]}', '{p2Stats[0]}', {p1Stats[1]}, {p2Stats[1]}, 0, 0,{p1Stats[2]}, {p2Stats[2]}, {p1Stats[3]}, {p2Stats[3]},'None','None',1,'None', '{battleGround}');""")
            connection.commit()

            await roundStart(message)
        # ---
    return

async def leaveFight(message):
    # Find out if you're even in a fight. If not, state that you're not.
    cursor.execute(f"""SELECT inBattle FROM UserInfo WHERE UID={message.author.id};""")
    status = cursor.fetchone()
    if (status[0] == 0):
        await message.channel.send('You\'re not currently in battle.')
        return

    else:
        # Gather the fighter IDs.
        cursor.execute(f"""SELECT p1UID, p2UID FROM BattleInfo WHERE (p1UID={message.author.id}) OR (p2UID={message.author.id}) ;""")
        IDs = cursor.fetchone()

        # Clear inBattle & Challenging Status
        cursor.execute(f"""UPDATE UserInfo SET inBattle = 0 WHERE (UID={IDs[0]});""")
        connection.commit()
        cursor.execute(f"""UPDATE UserInfo SET inBattle = 0 WHERE (UID={IDs[1]});""")
        connection.commit()
        cursor.execute(f"""UPDATE UserInfo SET Challenging = '0' WHERE (UID={IDs[0]});""")
        connection.commit()
        cursor.execute(f"""UPDATE UserInfo SET Challenging = '0' WHERE (UID={IDs[1]});""")
        connection.commit()

        cursor.execute(f"""DELETE FROM BattleInfo WHERE (p1UID = {IDs[0]}) OR (p2UID = {IDs[0]}) ;""")
        connection.commit()

        await message.channel.send('Fight left.')

    return

async def roundStart(message):

    # Load fighters.
    cursor.execute(f"""SELECT p1UID, p2UID FROM BattleInfo WHERE (p1UID={message.author.id}) OR (p2UID={message.author.id}) ;""")
    IDs = cursor.fetchone()

    # Increment MP.
    cursor.execute(f"""SELECT p1MP, p2MP FROM BattleInfo WHERE (p1UID={IDs[0]}) OR (p2UID={IDs[0]}) ;""")
    playerMPs = cursor.fetchone()
    cursor.execute(f"""UPDATE BattleInfo SET p1MP = {playerMPs[0]+1} WHERE (p1UID={IDs[0]}) OR (p2UID={IDs[0]}) ;""")
    connection.commit()
    cursor.execute(f"""UPDATE BattleInfo SET p2MP = {playerMPs[1]+1} WHERE (p1UID={IDs[0]}) OR (p2UID={IDs[0]}) ;""")
    connection.commit()

    # Send fighters their stats and options.

    cursor.execute(f"""SELECT p1HP, p1MP, p1ATK, p1SPD, p2HP, p2MP, p2ATK, p2SPD FROM BattleInfo WHERE (p1UID={IDs[0]}) OR (p2UID={IDs[0]}) ;""")
    battleInfo = cursor.fetchone()

    cursor.execute(f"""SELECT Action1, Action2, Action3, Action4 FROM UserInfo WHERE UID={IDs[0]}""")
    p1Moves = cursor.fetchone()

    cursor.execute(f"""SELECT Action1, Action2, Action3, Action4 FROM UserInfo WHERE UID={IDs[1]}""")
    p2Moves = cursor.fetchone()

    user = client.get_user(int(IDs[0]))
    await user.send(f'What will you do this round? \n Your stats are: \n **HP:** {battleInfo[0]} |  **MP:** {battleInfo[1]} \n **ATK:** {battleInfo[2]} | **SPD:** {battleInfo[3]}'
                    f'\nYour moves are: \n1. {p1Moves[0]}\n2. {p1Moves[1]}\n3. {p1Moves[2]}\n4. {p1Moves[3]}')
    user = client.get_user(int(IDs[1]))
    await user.send(f'What will you do this round? \n Your stats are: \n **HP:** {battleInfo[4]} |  **MP:** {battleInfo[5]} \n **ATK:** {battleInfo[6]} | **SPD:** {battleInfo[7]}'
                    f'\nYour moves are: \n1. {p2Moves[0]}\n2. {p2Moves[1]}\n3. {p2Moves[2]}\n4. {p2Moves[3]}')
    #


    return

async def replace(message):

    replaceNumber = int(message.content[11:13])

    replaceRequest = message.content[13:]

    cursor.execute("""SELECT abilityName FROM AbilityInfo""")
    abilityNames = cursor.fetchall()
    print(abilityNames)
    print(replaceRequest)

    if replaceNumber not in range(1,5):
        await message.channel.send('Please specify an ability between 1-4.')
        return

    if replaceRequest not in [ability[0] for ability in abilityNames]:
        await message.channel.send('Please specify a valid ability.')
        return

    cursor.execute(f"""UPDATE UserInfo SET Action{replaceNumber} = '{replaceRequest}' WHERE (UID={message.author.id});""")
    connection.commit()

    return

async def chooseAttack(message):

    abilityChoice = int(message.content[10:12])

    if abilityChoice not in range(1, 5):
        await message.channel.send('Please choose an ability between 1-4.')
        return

    cursor.execute(f"""SELECT p1UID, p2UID FROM BattleInfo WHERE p1UID='{message.author.id}' OR p2UID='{message.author.id}'; """)
    letsSee = cursor.fetchone()
    print(letsSee)

    return

# This function awaits a message, and if the message starts with !d, it proceeds to act on the command.
@client.event
async def on_message(message: object):

    if message.content.startswith('!d'):
        command = (message.content[3:])

        if (command == 'sayhi'):
            await sayhi(message)
        elif (command == 'registerMe'):
            await registerMe(message)
        elif (command == 'showInfo'):
            await showInfo(message)
        elif (command[0:9] == 'challenge'):
            await challenge(message)
        elif (command == 'leaveFight'):
            await leaveFight(message)
        elif (command[0:7] == 'replace'):
            await replace(message)
        elif (command[0:6] == 'choose'):
            await chooseAttack(message)

@client.event
async def on_ready():
    async def on_ready():
        print('Logged in as\n' + client.user.name + '\n' + client.user.id )

client.run(os.getenv('DISCORD_TOKEN')) # go online