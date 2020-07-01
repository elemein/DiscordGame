import os # idk what this does
import asyncio
import random
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

async def invalid_command(message): # Say Hi Command.
    await message.channel.send('Invalid command.')
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
                f"""INSERT INTO BattleInfo (p1UID, p2UID, p1HP, p2HP, p1MP, p2MP, p1ATK, p2ATK, p1SPD, p2SPD, p1Action, p2Action, rndCounter, battleGround)
                                       VALUES ('{p1Stats[0]}', '{p2Stats[0]}', {p1Stats[1]}, {p2Stats[1]}, 1, 1,{p1Stats[2]}, {p2Stats[2]}, {p1Stats[3]}, {p2Stats[3]},'None','None',1,'{battleGround}');""")
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

    cursor.execute(f"""SELECT p1UID, p1Action, p2UID, p2Action, battleGround, p1MP, p2MP FROM BattleInfo WHERE p1UID='{message.author.id}' OR p2UID='{message.author.id}'; """)
    actionState = cursor.fetchone()

    if ((message.author.id == int(actionState[0])) and (actionState[1] != 'None')) or ((message.author.id == int(actionState[2])) and (actionState[3] != 'None')) :
        await message.channel.send('You have already locked in an ability.')
        return

    # Determine which player is choosing.
    if (message.author.id == int(actionState[0])):
        player = 1
    elif (message.author.id == int(actionState[2])):
        player = 2

    cursor.execute(f"""SELECT Action{abilityChoice} FROM UserInfo WHERE UID='{message.author.id}'; """)
    chosenAbility = cursor.fetchone()[0]

    cursor.execute(f"""SELECT * from AbilityInfo WHERE abilityName = '{chosenAbility}';""")
    abiltiyInfo = cursor.fetchone()

    abiltiyInfo[2]

    if (player == 1) and (abiltiyInfo[2]>actionState[5]):
        await message.channel.send('Insufficient mana for this action!')
        return
    elif (player == 2) and (abiltiyInfo[2] > actionState[6]):
        await message.channel.send('Insufficient mana for this action!')
        return

    if player == 1:
        cursor.execute(f"""UPDATE BattleInfo SET p1Action = '{chosenAbility}', p1MP = {actionState[5]-abiltiyInfo[2]} WHERE p1UID='{message.author.id}'; """)
        connection.commit()
    else:
        cursor.execute(f"""UPDATE BattleInfo SET p2Action = '{chosenAbility}', p2MP = {actionState[6]-abiltiyInfo[2]} WHERE p2UID='{message.author.id}'; """)
        connection.commit()

    channel = client.get_channel(int(actionState[4]))
    await channel.send(f'Player {player} is ready.')

    cursor.execute(f"""SELECT p1Action, p2Action FROM BattleInfo WHERE p{player}UID = '{message.author.id}'; """)
    abilityCheck = cursor.fetchone()

    if ((abilityCheck[0] != 'None') and (abilityCheck[1] != 'None')):
        await resolveRound(message)

    return

async def resolveRound(message):

    cursor.execute(f'''SELECT * FROM BattleInfo WHERE (p1UID = {message.author.id}) OR (p2UID = {message.author.id}); ''')
    initialState = cursor.fetchone()

    cursor.execute(f'''SELECT abilityName, priority, latent FROM AbilityInfo WHERE abilityName = '{initialState[10]}';''')
    p1ActionInfo = cursor.fetchone()

    cursor.execute(f'''SELECT abilityName, priority, latent FROM AbilityInfo WHERE abilityName = '{initialState[11]}';''')
    p2ActionInfo = cursor.fetchone()

    # initialState[x] =
    # 0 = p1UID, 1 = p2UID, 2 = p1HP, 3 = p2HP, 4 = p1MP, 5 = p2MP, 6 = p1ATK, 7 = p2ATK, 8 = p1SPD, 9 = p2SPD, 10 = p1Action, 11 = p2Action
    # 12 = rndCounter, 13 = battleGround

    # Determine turn preference by speed.

    if (initialState[8] > initialState[9]):
        goingFirst = (initialState[0],) + p1ActionInfo
        goingLast = (initialState[1],) + p2ActionInfo
    elif (initialState[8] < initialState[9]):
        goingFirst = (initialState[1],) + p2ActionInfo
        goingLast = (initialState[0],) + p1ActionInfo
    else:
        preference = random.randint(1,2)
        if preference == 1:
            goingFirst = (initialState[0],) + p1ActionInfo
            goingLast = (initialState[1],) + p2ActionInfo
        else:
            goingFirst = (initialState[1],) + p2ActionInfo
            goingLast = (initialState[0],) + p1ActionInfo

    # Determine turn order taking into account priority and latent.

    if (p1ActionInfo[1] == 1 and p2ActionInfo[1] != 1):
        goingFirst = (initialState[0],) + p1ActionInfo
        goingLast = (initialState[1],) + p2ActionInfo
    elif (p1ActionInfo[1] != 1 and p2ActionInfo[1] == 1):
        goingFirst = (initialState[1],) + p2ActionInfo
        goingLast = (initialState[0],) + p1ActionInfo
    elif (p1ActionInfo[2] != 1 and p2ActionInfo[2] == 1):
        goingFirst = (initialState[0],) + p1ActionInfo
        goingLast = (initialState[1],) + p2ActionInfo
    elif (p1ActionInfo[2] == 1 and p2ActionInfo[2] != 1):
        goingFirst = (initialState[1],) + p2ActionInfo
        goingLast = (initialState[0],) + p1ActionInfo

    # Lets resolve this round!

    # Create some stuff needed to help resolve the round.

    ability_list = {
        "Attack": attack,
        "Heavy Attack": heavy_attack,
        "Defend": defend,
        "Dodge": dodge
    }

    defensive_abilities = {
        "Defend": defend,
        "Dodge": dodge
    }

    currentGameState = 'first round'
    resolvedGameState = 0
    gameOver = 0
    channel = client.get_channel(int(initialState[13]))

    currentGameState = await ability_list.get(goingFirst[1])(initialState, currentGameState, goingFirst, goingLast, goingFirst[0])

    # check HPs
    if (currentGameState[2] <= 0) and (goingLast[1] not in defensive_abilities):
        await channel.send(f'Fight over! P2 is the winner!')
        gameOver = 1
        await endGame(initialState[0], initialState[1])
    elif (currentGameState[3] <=0) and (goingLast[1] not in defensive_abilities):
        await channel.send(f'Fight over! P1 is the winner!')
        gameOver = 1
        await endGame(initialState[0], initialState[1])

    if (gameOver == 0) or (goingLast[1] in defensive_abilities):
        resolvedGameState = await ability_list.get(goingLast[1])(initialState, currentGameState, goingFirst, goingLast, goingLast[0])

        if resolvedGameState[2] <= 0:
            await channel.send(f'Fight over! P2 is the winner!')
            gameOver = 1
            await endGame(initialState[0], initialState[1])
        elif resolvedGameState[3] <=0:
            await channel.send(f'Fight over! P1 is the winner!')
            gameOver = 1
            await endGame(initialState[0], initialState[1])

    cursor.execute(f'''SELECT HP FROM UserInfo WHERE UID={initialState[0]}''')
    p1maxHP = cursor.fetchone()

    cursor.execute(f'''SELECT HP FROM UserInfo WHERE UID={initialState[1]}''')
    p2maxHP = cursor.fetchone()

    await channel.send(f'Round resolved.\nP1 HP: {(resolvedGameState[2]/p1maxHP[0])*100} %\nP2 HP: {(resolvedGameState[3]/p2maxHP[0])*100} %\nNew round.')

    # commit round to database

    cursor.execute(f'''UPDATE BattleInfo SET p1HP = {resolvedGameState[2]}, p2HP = {resolvedGameState[3]}, 
                       p1MP = {resolvedGameState[4]+1}, p2MP = {resolvedGameState[5]+1}, 
                       p1ATK = {resolvedGameState[6]}, p2ATK = {resolvedGameState[7]}, 
                       p1SPD = {resolvedGameState[8]}, p2SPD = {resolvedGameState[9]}, 
                       p1Action = 'None', p2Action = 'None', rndCounter = {resolvedGameState[12]+1} 
                       WHERE (p1UID = {message.author.id}) OR (p2UID = {message.author.id});''')
    connection.commit()

    if gameOver == 0:
        await roundStart(message)

    return

async def endGame(p1UID, p2UID):

    cursor.execute(f'''DELETE FROM BattleInfo WHERE (p1UID = {p1UID}) OR (p2UID = {p1UID});''')
    connection.commit()

    cursor.execute(f'''UPDATE UserInfo SET Challenging = 'None', inBattle = 0 
                       WHERE UID = {p1UID};''')
    connection.commit()

    cursor.execute(f'''UPDATE UserInfo SET Challenging = 'None', inBattle = 0 
                       WHERE UID = {p2UID};''')
    connection.commit()

    return

async def attack(initialState, currentGameState, goingFirst, goingLast, attackCaller):

# if this is the first action in the round

    channel = client.get_channel(int(initialState[13]))

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]:
            modifiedGameState = initialState[:3] + ((initialState[3] - initialState[6]),) + initialState[4:]
            await channel.send(f'P1 attacked P2, dealing {initialState[6]} damage.')
        # if attack caller is p2
        else:
            modifiedGameState = initialState[:2] + ((initialState[2] - initialState[7]),) + initialState[3:]
            await channel.send(f'P2 attacked P1, dealing {initialState[7]} damage.')
# if this is the second action in the round
    else:
        # if attack caller is p1
        if attackCaller == initialState[0]:
            modifiedGameState = currentGameState[:3] + ((currentGameState[3] - currentGameState[6]),) + currentGameState[4:]
            await channel.send(f'P1 attacked P2, dealing {initialState[6]} damage.')
        # if attack caller is p2
        else:
            modifiedGameState = currentGameState[:2] + ((currentGameState[2] - currentGameState[7]),) + currentGameState[3:]
            await channel.send(f'P2 attacked P1, dealing {initialState[7]} damage.')

    # perform attack on p2 HP if attack caller is p1

    return modifiedGameState

async def heavy_attack(initialState, currentGameState, goingFirst, goingLast, attackCaller):
    # if this is the first action in the round

    channel = client.get_channel(int(initialState[13]))

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]:
            modifiedGameState = initialState[:3] + ((initialState[3] - (initialState[6] * 2)),) + initialState[4:]
            await channel.send(f'P1 heavy attacked P2, dealing {(initialState[6] * 2)} damage.')
        # if attack caller is p2
        else:
            modifiedGameState = initialState[:2] + ((initialState[2] - (initialState[7] * 2)),) + initialState[3:]
            await channel.send(f'P2 heavy attacked P1, dealing {(initialState[7] * 2)} damage.')
    # if this is the second action in the round
    else:
        # if attack caller is p1
        if attackCaller == initialState[0]:
            modifiedGameState = currentGameState[:3] + (
            (currentGameState[3] - (currentGameState[6] * 2)),) + currentGameState[4:]
            await channel.send(f'P1 heavy attacked P2, dealing {(initialState[6] * 2)} damage.')
        # if attack caller is p2
        else:
            modifiedGameState = currentGameState[:2] + (
            (currentGameState[2] - (currentGameState[7] * 2)),) + currentGameState[3:]
            await channel.send(f'P2 heavy attacked P1, dealing {(initialState[7] * 2)} damage.')

    # perform attack on p2 HP if attack caller is p1

    return modifiedGameState

async def defend(initialState, currentGameState, goingFirst, goingLast, attackCaller):

# if this is the first action in the round

    channel = client.get_channel(int(initialState[13]))
    modifiedGameState = initialState

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]:
            await channel.send(f'P1 attempted to defend, but there was no attack to defend against!')
        # if attack caller is p2
        else:
            await channel.send(f'P2 attempted to defend, but there was no attack to defend against!')
# if this is the second action in the round
    else:
        # if attack caller is p1
        if attackCaller == initialState[0]:
            if (currentGameState[2]<initialState[2]):
                # defend

                damageDealt = initialState[2] - currentGameState[2] # Find how much damage was dealt.
                defendAmount = initialState[6]/2 # Find how much to defend by.
                damageDealt = damageDealt-defendAmount # Lower damage dealt by defend amount.

                if damageDealt <= 0:
                    await channel.send(f'P1 defended against P2\'s attack, negating all damage.')
                    modifiedGameState = initialState
                elif damageDealt > 0:
                    await channel.send(f'P1 defended against P2\'s attack, negating {defendAmount} damage.')
                    modifiedGameState = initialState[:2] + ((initialState[2] - damageDealt),) + initialState[3:]
            else:
                await channel.send(f'P1 attempted to defend, but there was no attack to defend against!')
        # if attack caller is p2
        else:
            if (currentGameState[3] < initialState[3]):
                # defend
                damageDealt = initialState[3] - currentGameState[3]  # Find how much damage was dealt.
                defendAmount = initialState[7] / 2  # Find how much to defend by.
                damageDealt = damageDealt - defendAmount  # Lower damage dealt by defend amount.

                if damageDealt <= 0:
                    await channel.send(f'P2 defended against P1\'s attack, negating all damage.')
                    modifiedGameState = initialState
                elif damageDealt > 0:
                    await channel.send(f'P2 defended against P1\'s attack, negating {defendAmount} damage.')
                    modifiedGameState = initialState[:3] + ((initialState[3] - damageDealt),) + initialState[4:]
            else:
                await channel.send(f'P2 attempted to defend, but there was no attack to defend against!')

    return modifiedGameState

async def dodge(initialState, currentGameState, goingFirst, goingLast, attackCaller):

# if this is the first action in the round

    channel = client.get_channel(int(initialState[13]))
    modifiedGameState = initialState

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]:
            await channel.send(f'P1 attempted to dodge, but there was no attack to dodge!')
        # if attack caller is p2
        else:
            await channel.send(f'P2 attempted to dodge, but there was no attack to dodge!')
# if this is the second action in the round
    else:
        # if attack caller is p1
        if attackCaller == initialState[0]:
            if (currentGameState[2]<initialState[2]):
                # defend

                dodgeChance = ((currentGameState[8] * 5) + 25)

                dodge = random.randint(0,100)

                if dodge < dodgeChance:
                    await channel.send(f'P1 dodged P2\'s attack!')
                    modifiedGameState = initialState
                else:
                    await channel.send(f'P1 failed to dodge P2\'s attack!')
                    modifiedGameState = currentGameState

            else:
                await channel.send(f'P1 attempted to dodge, but there was no attack to dodge!')
        # if attack caller is p2
        else:
            if (currentGameState[3] < initialState[3]):
                # defend
                dodgeChance = ((currentGameState[9] * 5) + 25)

                dodge = random.randint(0, 100)

                if dodge < dodgeChance:
                    await channel.send(f'P2 dodged P1\'s attack!')
                    modifiedGameState = initialState
                else:
                    await channel.send(f'P2 failed to dodge P1\'s attack!')
                    modifiedGameState = currentGameState
            else:
                await channel.send(f'P2 attempted to dodge, but there was no attack to dodge!')

    return modifiedGameState


# This function awaits a message, and if the message starts with !d, it proceeds to act on the command.
@client.event
async def on_message(message: object):

    if message.content.startswith('!d'):
        command = (message.content.split(' ')[1])

        command_list = {
            "sayhi": sayhi,
            "registerMe": registerMe,
            "showInfo": showInfo,
            "challenge": challenge,
            "leaveFight": leaveFight,
            "replace": replace,
            "choose": chooseAttack
        }

        await command_list.get(command, invalid_command)(message)

@client.event
async def on_ready():
    async def on_ready():
        print('Logged in as\n' + client.user.name + '\n' + client.user.id )

client.run(os.getenv('DISCORD_TOKEN')) # go online