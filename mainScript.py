import os # idk what this does
import random
import sqlite3 # IMPORT SQL
import discord #import discord tools
from dotenv import load_dotenv # load .env loader for environment variables

load_dotenv() # spawn tool
connection = sqlite3.connect("myTable.db")
cursor = connection.cursor()
client = discord.Client() # connect the bot to discord

    # ToDo:
    #   - overall improve code
    #   - move to GCP platform

async def invalid_command(message):
    await message.channel.send('Invalid command. Please use "!d help" for more info on this bot\'s commands.')
    return

async def helpUser(message):
    user = client.get_user(message.author.id)

    await user.send('This is the Drysduel Bot Help Dialog!\n'
                    'Drysduel is a turn-based PvP tactical fighting game based around choosing moves to outsmart your opponent!\n\n'
                    '*----- Gameplay -----*\n'
                    '- Combat is split into rounds. At round start, each player gains 1 MP which can be used to fuel certain spells. Each player selects a move.\n'
                    '- Once moves are chosen, the round is resolved. The player with the higher SPD stat moves first, except when priority'
                    'or latent moves are used (priority moves always go first, latent moves go last) \n'
                    '- At round end, the HP values are resolved and the next round starts.\n'
                    '- This continues until someone\'s HP is lowered to 0 or less, then the other player wins!\n\n'
                    '*----- Commands -----*\n'
                    '**!d registerMe** - Use this to register yourself in the system. Once done, you\'re ready to fight!\n'
                    '**!d showInfo** - Shows your info. Displays your stats and moveset.\n'
                    '**!d challenge @opponent** - Used to initiate fights with others. If two users challenge eachother, a fight begins!\n'
                    '**!d leaveFight** - Leave any fight you\'re currently in.\n'
                    '**!d choose x** - Used to choose a move while in combat. Replace x with your move choice; a number between 1 and 4.\n'
                    '**!d moveList** - Sends you a list of all moves in the game!\n'
                    '**!d replace moveSlot move** - Used to edit your moveset. Replace "moveSlot" with the ability number you\'d like to replace, and "move" with the name of the ability you\'d like to add.\n')
    return

async def registerMe(message):
    print(message.author.id)
    cursor.execute(f"""SELECT UID FROM UserInfo WHERE UID={message.author.id}  ;""")

    if (cursor.fetchone() != None):
        await message.channel.send('You\'re already registered.')
        return
    else:
        cursor.execute(f"""INSERT INTO UserInfo (UID, DisplayName, Rating, Challenging, inBattle, HP, ATK, SPD, Action1, Action2, Action3, Action4)
                           VALUES ('{message.author.id}', '{message.author.name}', 100, 'None', 0, 10,3,5,'Attack','Heavy Attack','Defend','Dodge');""")
        connection.commit()
        await message.channel.send(f'You\'ve been registered with name: {message.author.name} ')

    return

async def showInfo(message):
    cursor.execute(f"""SELECT displayName, Rating, HP, ATK, SPD, Action1, Action2, Action3, Action4 FROM UserInfo WHERE UID={message.author.id}  ;""")
    info = cursor.fetchone()
    userMoveNames = [info[5], info[6], info[7], info[8]]

# --------------------------

    moveList = ''
    toJoin = ''
    toFormat = []

    for x in userMoveNames:
        cursor.execute(f'''SELECT * from AbilityInfo WHERE abilityName = '{x}';''')
        toFormat.append(cursor.fetchone())

    # 0 = Ability Name, 1 = Description, 2 = Cost, 3 = Priority, 4 = Latent

    for x in toFormat:
        if x[3] == 0 and x[4] == 0:
            toJoin = (f'{x[0]} (MP: {x[2]})\n> ^ {x[1]}')
        elif x[3] == 1:
            toJoin = (f'{x[0]} - (MP: {x[2]}) - PRIORITY\n> ^ {x[1]}')
        elif x[4] == 1:
            toJoin = (f'{x[0]} - (MP: {x[2]}) - LATENT\n> ^ {x[1]}')

        moveList = "\n".join((moveList, toJoin))

# --------------------------

    await message.channel.send(f'Here\'s your info:\nName: {info[0]} | Rating: {info[1]}\n--- Stats ---\n**HP:** {info[2]} | **ATK:** {info[3]} | **SPD:** {info[4]}'
                               f'\n--- Moves ---{moveList}')

    return

async def moveList(message):
    cursor.execute(f"""SELECT * FROM AbilityInfo;""")
    info = cursor.fetchall()
    moveList = ""

    #0 = Ability Name, 1 = Description, 2 = Cost, 3 = Priority, 4 = Latent

    for x in info:
        if x[3] == 0 and x[4] == 0:
            toJoin = (f'{x[0]} (MP: {x[2]})\n> ^ {x[1]}')
        elif x[3] == 1:
            toJoin = (f'{x[0]} - (MP: {x[2]}) - PRIORITY\n> ^ {x[1]}')
        elif x[4] == 1:
            toJoin = (f'{x[0]} - (MP: {x[2]}) - LATENT\n> ^ {x[1]}')

        moveList = "\n".join((moveList, toJoin))

    user = client.get_user(message.author.id)
    await user.send(f'|----- *Drysduel Move List* -----|{moveList}\n |--------------------------------|')

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
    p1MoveInfo = []

    cursor.execute(f"""SELECT Action1, Action2, Action3, Action4 FROM UserInfo WHERE UID={IDs[1]}""")
    p2Moves = cursor.fetchone()
    p2MoveInfo = []

    toJoin = ""

    for x in p1Moves:
        cursor.execute(f"""SELECT * FROM AbilityInfo WHERE abilityName = '{x}';""")
        move = cursor.fetchone()

        if (move[3] == 0) and (move[4] == 0):
            toJoin = (f'{move[0]} (MP: {move[2]})\n> {move[1]}')
        elif move[3] == 1:
            toJoin = (f'{move[0]} - (MP: {move[2]}) - PRIORITY\n> {move[1]}')
        elif move[4] == 1:
            toJoin = (f'{move[0]} - (MP: {move[2]}) - LATENT\n> {move[1]}')

        p1MoveInfo.append(toJoin)

    for x in p2Moves:
        cursor.execute(f"""SELECT * FROM AbilityInfo WHERE abilityName = '{x}';""")
        move = cursor.fetchone()

        if (move[3] == 0) and (move[4] == 0):
            toJoin = (f'{move[0]} (MP: {move[2]})\n> {move[1]}')
        elif move[3] == 1:
            toJoin = (f'{move[0]} - (MP: {move[2]}) - PRIORITY\n> {move[1]}')
        elif move[4] == 1:
            toJoin = (f'{move[0]} - (MP: {move[2]}) - LATENT\n> {move[1]}')

        p2MoveInfo.append(toJoin)


    user = client.get_user(int(IDs[0]))
    await user.send(f'What will you do this round? \n *--- STATS ---*\n **HP:** {battleInfo[0]} |  **MP:** {battleInfo[1]} \n **ATK:** {battleInfo[2]} | **SPD:** {battleInfo[3]}'
                    f'\n*--- MOVES ---*\n**1.** {p1MoveInfo[0]}\n**2.** {p1MoveInfo[1]}\n**3.** {p1MoveInfo[2]}\n**4.** {p1MoveInfo[3]}')
    user = client.get_user(int(IDs[1]))
    await user.send(f'What will you do this round? \n *--- STATS ---*\n **HP:** {battleInfo[4]} |  **MP:** {battleInfo[5]} \n **ATK:** {battleInfo[6]} | **SPD:** {battleInfo[7]}'
                    f'\n*--- MOVES ---*\n**1.** {p2MoveInfo[0]}\n**2.** {p2MoveInfo[1]}\n**3.** {p2MoveInfo[2]}\n**4.** {p2MoveInfo[3]}')

    return

async def replace(message):

    replaceNumber = int(message.content[11:13])

    replaceRequest = message.content[13:]

    cursor.execute("""SELECT abilityName FROM AbilityInfo""")
    abilityNames = cursor.fetchall()
    print(abilityNames)
    print(replaceRequest)

    cursor.execute(f"""SELECT inBattle FROM UserInfo WHERE UID = {message.author.id}""")
    inBattle = cursor.fetchone()[0]

    if replaceNumber not in range(1,5):
        await message.channel.send('Please specify an ability between 1-4.')
        return

    if replaceRequest not in [ability[0] for ability in abilityNames]:
        await message.channel.send('Please specify a valid ability.')
        return

    if inBattle == 1:
        await message.channel.send('You may not change abilities while in combat.')
        return

    cursor.execute(f"""UPDATE UserInfo SET Action{replaceNumber} = '{replaceRequest}' WHERE (UID={message.author.id});""")
    connection.commit()

    await message.channel.send('Ability successfully replaced.')

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

    player1 = client.get_user(int(actionState[0]))
    player2 = client.get_user(int(actionState[2]))

    if player == 1:
        await player2.send(f'{player1.name} is ready.')
    elif player == 2:
        await player1.send(f'{player2.name} is ready.')

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
        "Dodge": dodge,
        "Snare" : snare,
        "Empower" : empower,
        "Heal" : heal,
        "Quick Attack" : quick_attack,
        "Dull" : dull,
        "Quicken" : quicken
    }

    defensive_abilities = {
        "Defend": defend,
        "Dodge": dodge
    }

    currentGameState = 'first round'
    resolvedGameState = 0
    gameOver = 0
    channel = client.get_channel(int(initialState[13]))

    player1 = client.get_user(int(initialState[0]))
    player2 = client.get_user(int(initialState[1]))

    roundMessage = f'*--- ROUND {initialState[12]} ---*'
    await player1.send(roundMessage)
    await player2.send(roundMessage)

    currentGameState = await ability_list.get(goingFirst[1])(initialState, currentGameState, goingFirst[0])

    # check HPs
    if (currentGameState[2] <= 0) and (goingLast[1] not in defensive_abilities):
        await player1.send(f'Fight over! {player2.name} is the winner!')
        await player2.send(f'Fight over! {player2.name} is the winner!')
        gameOver = 1
        await endGame(initialState[0], initialState[1])
    elif (currentGameState[3] <=0) and (goingLast[1] not in defensive_abilities):
        await player1.send(f'Fight over! {player1.name} is the winner!')
        await player2.send(f'Fight over! {player1.name} is the winner!')
        gameOver = 1
        await endGame(initialState[0], initialState[1])

    resolvedGameState = currentGameState

    if (gameOver == 0) or (goingLast[1] in defensive_abilities):
        resolvedGameState = await ability_list.get(goingLast[1])(initialState, currentGameState, goingLast[0])

        if resolvedGameState[2] <= 0:
            await player1.send(f'Fight over! {player2.name} is the winner!')
            await player2.send(f'Fight over! {player2.name} is the winner!')
            gameOver = 1
            await endGame(initialState[0], initialState[1])
        elif resolvedGameState[3] <=0:
            await player1.send(f'Fight over! {player1.name} is the winner!')
            await player2.send(f'Fight over! {player1.name} is the winner!')
            gameOver = 1
            await endGame(initialState[0], initialState[1])

    cursor.execute(f'''SELECT HP FROM UserInfo WHERE UID={initialState[0]}''')
    p1maxHP = cursor.fetchone()

    cursor.execute(f'''SELECT HP FROM UserInfo WHERE UID={initialState[1]}''')
    p2maxHP = cursor.fetchone()

    if p1maxHP[0] == 0:
        await player1.send(f'\n{player1.name} HP: 0%\n{player2.name} HP: {(resolvedGameState[3] / p2maxHP[0]) * 100} %\n--------------------')
        await player2.send(f'\n{player1.name} HP: 0%\n{player2.name} HP: {(resolvedGameState[3] / p2maxHP[0]) * 100} %\n--------------------')
    elif p2maxHP[0] == 0:
        await player1.send(f'\n{player1.name} HP: {round(((resolvedGameState[2] / p1maxHP[0]) * 100),2)} %\n{player2.name} HP: 0%\n--------------------')
        await player2.send(f'\n{player1.name} HP: {round(((resolvedGameState[2] / p1maxHP[0]) * 100),2)} %\n{player2.name} HP: 0%\n--------------------')
    else:
        await player1.send(f'\n{player1.name} HP: {round(((resolvedGameState[2]/p1maxHP[0])*100),2)} %\n{player2.name} HP: {(resolvedGameState[3]/p2maxHP[0])*100} %\n--------------------')
        await player2.send(f'\n{player1.name} HP: {round(((resolvedGameState[2]/p1maxHP[0])*100),2)} %\n{player2.name} HP: {(resolvedGameState[3]/p2maxHP[0])*100} %\n--------------------')

    # commit round to database

    cursor.execute(f'''UPDATE BattleInfo SET p1HP = {resolvedGameState[2]}, p2HP = {resolvedGameState[3]}, 
                       p1MP = {resolvedGameState[4]+1}, p2MP = {resolvedGameState[5]+1}, 
                       p1ATK = {resolvedGameState[6]}, p2ATK = {resolvedGameState[7]}, 
                       p1SPD = {resolvedGameState[8]}, p2SPD = {resolvedGameState[9]}, 
                       p1Action = 'None', p2Action = 'None', rndCounter = {int(resolvedGameState[12])+1} 
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

async def attack(initialState, currentGameState, attackCaller):

# if this is the first action in the round

    player1 = client.get_user(int(initialState[0]))
    player2 = client.get_user(int(initialState[1]))

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]:
            modifiedGameState = initialState[:3] + ((initialState[3] - initialState[6]),) + initialState[4:]
            await player1.send(f'{player1.name} attacked {player2.name}, dealing {initialState[6]} damage.')
            await player2.send(f'{player1.name} attacked {player2.name}, dealing {initialState[6]} damage.')
        # if attack caller is p2
        else:
            modifiedGameState = initialState[:2] + ((initialState[2] - initialState[7]),) + initialState[3:]
            await player1.send(f'{player2.name} attacked {player1.name}, dealing {initialState[7]} damage.')
            await player2.send(f'{player2.name} attacked {player1.name}, dealing {initialState[7]} damage.')
# if this is the second action in the round
    else:
        # if attack caller is p1
        if attackCaller == initialState[0]:
            modifiedGameState = currentGameState[:3] + ((currentGameState[3] - currentGameState[6]),) + currentGameState[4:]
            await player1.send(f'{player1.name} attacked {player2.name}, dealing {initialState[6]} damage.')
            await player2.send(f'{player1.name} attacked {player2.name}, dealing {initialState[6]} damage.')
        # if attack caller is p2
        else:
            modifiedGameState = currentGameState[:2] + ((currentGameState[2] - currentGameState[7]),) + currentGameState[3:]
            await player1.send(f'{player2.name} attacked {player1.name}, dealing {initialState[7]} damage.')
            await player2.send(f'{player2.name} attacked {player1.name}, dealing {initialState[7]} damage.')

    return modifiedGameState

async def heavy_attack(initialState, currentGameState, attackCaller):
    # if this is the first action in the round

    player1 = client.get_user(int(initialState[0]))
    player2 = client.get_user(int(initialState[1]))

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]:
            modifiedGameState = initialState[:3] + ((initialState[3] - (initialState[6] * 1.5)),) + initialState[4:]
            await player1.send(f'{player1.name} heavy attacked {player2.name}, dealing {(initialState[6] * 1.5)} damage.')
            await player2.send(f'{player1.name} heavy attacked {player2.name}, dealing {(initialState[6] * 1.5)} damage.')
        # if attack caller is p2
        else:
            modifiedGameState = initialState[:2] + ((initialState[2] - (initialState[7] * 1.5)),) + initialState[3:]
            await player1.send(f'{player2.name} heavy attacked {player1.name}, dealing {(initialState[7] * 1.5)} damage.')
            await player2.send(f'{player2.name} heavy attacked {player1.name}, dealing {(initialState[7] * 1.5)} damage.')
    # if this is the second action in the round
    else:
        # if attack caller is p1
        if attackCaller == initialState[0]:
            modifiedGameState = currentGameState[:3] + (
            (currentGameState[3] - (currentGameState[6] * 2)),) + currentGameState[4:]
            await player1.send(f'{player1.name} heavy attacked {player2.name}, dealing {(initialState[6] * 1.5)} damage.')
            await player2.send(f'{player1.name} heavy attacked {player2.name}, dealing {(initialState[6] * 1.5)} damage.')
        # if attack caller is p2
        else:
            modifiedGameState = currentGameState[:2] + (
            (currentGameState[2] - (currentGameState[7] * 2)),) + currentGameState[3:]
            await player1.send(f'{player2.name} heavy attacked {player1.name}, dealing {(initialState[7] * 1.5)} damage.')
            await player2.send(f'{player2.name} heavy attacked {player1.name}, dealing {(initialState[7] * 1.5)} damage.')

    # perform attack on p2 HP if attack caller is p1

    return modifiedGameState

async def defend(initialState, currentGameState, attackCaller):

# if this is the first action in the round

    player1 = client.get_user(int(initialState[0]))
    player2 = client.get_user(int(initialState[1]))
    modifiedGameState = initialState

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]:
            await player1.send(f'{player1.name} attempted to defend, but there was no attack to defend against!')
            await player2.send(f'{player1.name} attempted to defend, but there was no attack to defend against!')
        # if attack caller is p2
        else:
            await player1.send(f'{player2.name} attempted to defend, but there was no attack to defend against!')
            await player2.send(f'{player2.name} attempted to defend, but there was no attack to defend against!')
# if this is the second action in the round
    else:
        modifiedGameState = currentGameState
        # if attack caller is p1
        if attackCaller == initialState[0]:
            if (currentGameState[2]<initialState[2]):
                # defend

                damageDealt = initialState[2] - currentGameState[2] # Find how much damage was dealt.
                defendAmount = initialState[6]/2 # Find how much to defend by.
                damageDealt = damageDealt-defendAmount # Lower damage dealt by defend amount.

                if damageDealt <= 0:
                    await player1.send(f'{player1.name} defended against {player2.name}\'s attack, negating all damage.')
                    await player2.send(f'{player1.name} defended against {player2.name}\'s attack, negating all damage.')
                    modifiedGameState = currentGameState[:2] + (initialState[2],) + currentGameState[3:]
                elif damageDealt > 0:
                    await player1.send(f'{player1.name} defended against {player2.name}\'s attack, negating {defendAmount} damage.')
                    await player2.send(f'{player1.name} defended against {player2.name}\'s attack, negating {defendAmount} damage.')
                    modifiedGameState = initialState[:2] + ((initialState[2] - damageDealt),) + initialState[3:]
            else:
                await player1.send(f'{player1.name} attempted to defend, but there was no attack to defend against!')
                await player2.send(f'{player1.name} attempted to defend, but there was no attack to defend against!')
        # if attack caller is p2
        else:
            if (currentGameState[3] < initialState[3]):
                # defend
                damageDealt = initialState[3] - currentGameState[3]  # Find how much damage was dealt.
                defendAmount = initialState[7] / 2  # Find how much to defend by.
                damageDealt = damageDealt - defendAmount  # Lower damage dealt by defend amount.

                if damageDealt <= 0:
                    await player1.send(f'{player2.name} defended against {player1.name}\'s attack, negating all damage.')
                    await player2.send(f'{player2.name} defended against {player1.name}\'s attack, negating all damage.')
                    modifiedGameState = currentGameState[:3] + (initialState[3],) + currentGameState[4:]
                elif damageDealt > 0:
                    await player1.send(f'{player2.name} defended against {player1.name}\'s attack, negating {defendAmount} damage.')
                    await player2.send(f'{player2.name} defended against {player1.name}\'s attack, negating {defendAmount} damage.')
                    modifiedGameState = initialState[:3] + ((initialState[3] - damageDealt),) + initialState[4:]
            else:
                await player1.send(f'{player2.name} attempted to defend, but there was no attack to defend against!')
                await player2.send(f'{player2.name} attempted to defend, but there was no attack to defend against!')

    return modifiedGameState

async def dodge(initialState, currentGameState, attackCaller):

# if this is the first action in the round

    player1 = client.get_user(int(initialState[0]))
    player2 = client.get_user(int(initialState[1]))
    modifiedGameState = initialState

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]:
            await player1.send(f'{player1.name} attempted to dodge, but there was no attack to dodge!')
            await player2.send(f'{player1.name} attempted to dodge, but there was no attack to dodge!')
        # if attack caller is p2
        else:
            await player1.send(f'{player2.name} attempted to dodge, but there was no attack to dodge!')
            await player2.send(f'{player2.name} attempted to dodge, but there was no attack to dodge!')
# if this is the second action in the round
    else:
        modifiedGameState = currentGameState
        # if attack caller is p1
        if attackCaller == initialState[0]:
            if (currentGameState[2]<initialState[2]):
                # defend

                dodgeChance = ((currentGameState[8] * 5) + 25)

                dodge = random.randint(0,100)

                if dodge < dodgeChance:
                    await player1.send(f'{player1.name} dodged {player2.name}\'s attack!')
                    await player2.send(f'{player1.name} dodged {player2.name}\'s attack!')
                    modifiedGameState = currentGameState[:2] + (initialState[2],) + currentGameState[3:]
                    print(modifiedGameState)
                else:
                    await player1.send(f'{player1.name} failed to dodge {player2.name}\'s attack!')
                    await player2.send(f'{player1.name} failed to dodge {player2.name}\'s attack!')
                    modifiedGameState = currentGameState

            else:
                await player1.send(f'{player1.name} attempted to dodge, but there was no attack to dodge!')
                await player2.send(f'{player1.name} attempted to dodge, but there was no attack to dodge!')
        # if attack caller is p2
        else:
            if (currentGameState[3] < initialState[3]):
                # defend
                dodgeChance = ((currentGameState[9] * 5) + 25)

                dodge = random.randint(0, 100)

                if dodge < dodgeChance:
                    await player1.send(f'{player2.name} dodged {player1.name}\'s attack!')
                    await player2.send(f'{player2.name} dodged {player1.name}\'s attack!')
                    modifiedGameState = currentGameState[:3] + (initialState[3],) + currentGameState[4:]
                    print(modifiedGameState)
                else:
                    await player1.send(f'{player2.name} failed to dodge {player1.name}\'s attack!')
                    await player2.send(f'{player2.name} failed to dodge {player1.name}\'s attack!')
                    modifiedGameState = currentGameState
            else:
                await player1.send(f'{player2.name} attempted to dodge, but there was no attack to dodge!')
                await player2.send(f'{player2.name} attempted to dodge, but there was no attack to dodge!')

    return modifiedGameState

async def snare(initialState, currentGameState, attackCaller):

# if this is the first action in the round

    player1 = client.get_user(int(initialState[0]))
    player2 = client.get_user(int(initialState[1]))
    modifiedGameState = initialState

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]: # = P1
            await player1.send(f'{player1.name} snared {player2.name}, reducing their SPD to 2!')
            await player2.send(f'{player1.name} snared {player2.name}, reducing their SPD to 2!')
            modifiedGameState = initialState[:9] + (2,) + initialState[10:]
        # if attack caller is p2
        else:
            await player1.send(f'{player2.name} snared {player1.name}, reducing their SPD to 2!')
            await player2.send(f'{player2.name} snared {player1.name}, reducing their SPD to 2!')
            modifiedGameState = initialState[:8] + (2,) + initialState[9:]
# if this is the second action in the round
    else:
        # if attack caller is p1
        if attackCaller == initialState[0]:  # = P1
            await player1.send(f'{player1.name} snared {player2.name}, reducing their SPD to 2!')
            await player2.send(f'{player1.name} snared {player2.name}, reducing their SPD to 2!')
            modifiedGameState = currentGameState[:9] + (2,) + currentGameState[10:]
        # if attack caller is p2
        else:
            await player1.send(f'{player2.name} snared {player1.name}, reducing their SPD to 2!')
            await player2.send(f'{player2.name} snared {player1.name}, reducing their SPD to 2!')
            modifiedGameState = currentGameState[:8] + (2,) + currentGameState[9:]

    return modifiedGameState

async def quicken(initialState, currentGameState, attackCaller):

# if this is the first action in the round

    player1 = client.get_user(int(initialState[0]))
    player2 = client.get_user(int(initialState[1]))
    modifiedGameState = initialState

    cursor.execute(f"""SELECT SPD FROM UserInfo WHERE UID = {initialState[0]} """)
    p1Spd = cursor.fetchone()
    p1Boost = p1Spd[0]*0.5

    cursor.execute(f"""SELECT SPD FROM UserInfo WHERE UID = {initialState[1]} """)
    p2Spd = cursor.fetchone()
    p2Boost = p2Spd[0]*0.5

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]: # = P1
            await player1.send(f'{player1.name} quickened themselves, increasing their SPD!')
            await player2.send(f'{player1.name} quickened themselves, increasing their SPD!')
            modifiedGameState = initialState[:8] + ((initialState[8] + p1Boost),) + initialState[9:]
        # if attack caller is p2
        else:
            await player1.send(f'{player2.name} quickened themselves, increasing their SPD!')
            await player2.send(f'{player2.name} quickened themselves, increasing their SPD!')
            modifiedGameState = initialState[:9] + ((initialState[9] + p2Boost),) + initialState[10:]
# if this is the second action in the round
    else:
        # if attack caller is p1
        if attackCaller == initialState[0]:  # = P1
            await player1.send(f'{player1.name} quickened themselves, increasing their SPD!')
            await player2.send(f'{player1.name} quickened themselves, increasing their SPD!')
            modifiedGameState = currentGameState[:8] + ((currentGameState[8] + p1Boost),) + currentGameState[8:]
        # if attack caller is p2
        else:
            await player1.send(f'{player2.name} quickened themselves, increasing their SPD!')
            await player2.send(f'{player2.name} quickened themselves, increasing their SPD!')
            modifiedGameState = currentGameState[:9] + ((currentGameState[9] + p2Boost),) + currentGameState[10:]

    return modifiedGameState

async def empower(initialState, currentGameState, attackCaller):

# if this is the first action in the round

    player1 = client.get_user(int(initialState[0]))
    player2 = client.get_user(int(initialState[1]))
    modifiedGameState = initialState

    cursor.execute(f"""SELECT ATK FROM UserInfo WHERE UID = {initialState[0]} """)
    p1Atk = cursor.fetchone()
    p1Boost = p1Atk[0]*0.5

    cursor.execute(f"""SELECT ATK FROM UserInfo WHERE UID = {initialState[1]} """)
    p2Atk = cursor.fetchone()
    p2Boost = p2Atk[0]*0.5

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]: # = P1
            await player1.send(f'{player1.name} empowered themselves, increasing their ATK!')
            await player2.send(f'{player1.name} empowered themselves, increasing their ATK!')
            modifiedGameState = initialState[:6] + ((initialState[6] + p1Boost),) + initialState[7:]
        # if attack caller is p2
        else:
            await player1.send(f'{player2.name} empowered themselves, increasing their ATK!')
            await player2.send(f'{player2.name} empowered themselves, increasing their ATK!')
            modifiedGameState = initialState[:7] + ((initialState[7] + p2Boost),) + initialState[8:]
# if this is the second action in the round
    else:
        # if attack caller is p1
        if attackCaller == initialState[0]:  # = P1
            await player1.send(f'{player1.name} empowered themselves, increasing their ATK!')
            await player2.send(f'{player1.name} empowered themselves, increasing their ATK!')
            modifiedGameState = currentGameState[:6] + ((currentGameState[6] + p1Boost),) + currentGameState[7:]
        # if attack caller is p2
        else:
            await player1.send(f'{player2.name} empowered themselves, increasing their ATK!')
            await player2.send(f'{player2.name} empowered themselves, increasing their ATK!')
            modifiedGameState = currentGameState[:7] + ((currentGameState[7] + p2Boost),) + currentGameState[8:]

    return modifiedGameState

async def dull(initialState, currentGameState, attackCaller):

# if this is the first action in the round

    player1 = client.get_user(int(initialState[0]))
    player2 = client.get_user(int(initialState[1]))
    modifiedGameState = initialState

    cursor.execute(f"""SELECT ATK FROM UserInfo WHERE UID = {initialState[0]} """)
    p1Atk = cursor.fetchone()
    p1Dull = p1Atk[0]*0.5

    cursor.execute(f"""SELECT ATK FROM UserInfo WHERE UID = {initialState[1]} """)
    p2Atk = cursor.fetchone()
    p2Dull = p2Atk[0]*0.5

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]: # = P1
            await player1.send(f'{player1.name} dulled {player2.name}, decreasing their ATK!')
            await player2.send(f'{player1.name} dulled {player2.name}, decreasing their ATK!')
            modifiedGameState = initialState[:7] + ((initialState[7] - p2Dull),) + initialState[8:]
        # if attack caller is p2
        else:
            await player1.send(f'{player2.name} dulled {player1.name}, decreasing their ATK!')
            await player2.send(f'{player2.name} dulled {player1.name}, decreasing their ATK!')
            modifiedGameState = initialState[:6] + ((initialState[6] + p1Dull),) + initialState[7:]
# if this is the second action in the round
    else:
        modifiedGameState = currentGameState
        # if attack caller is p1
        if attackCaller == initialState[0]:  # = P1
            await player1.send(f'{player1.name} dulled {player2.name}, decreasing their ATK!')
            await player2.send(f'{player1.name} dulled {player2.name}, decreasing their ATK!')
            modifiedGameState = currentGameState[:7] + ((currentGameState[7] - p2Dull),) + currentGameState[8:]
        # if attack caller is p2
        else:
            await player1.send(f'{player2.name} dulled {player1.name}, decreasing their ATK!')
            await player2.send(f'{player2.name} dulled {player1.name}, decreasing their ATK!')
            modifiedGameState = currentGameState[:6] + ((currentGameState[6] + p1Dull),) + currentGameState[7:]

    if modifiedGameState[6] < 1:
        modifiedGameState = modifiedGameState[:6] + (1,) + modifiedGameState[7:]
        await player1.send(f'{player1.name}\'s ATK cannot be lowered below 1!')
        await player2.send(f'{player1.name}\'s ATK cannot be lowered below 1!')

    if modifiedGameState[7] < 1:
        modifiedGameState = modifiedGameState[:7] + (1,) + modifiedGameState[8:]
        await player1.send(f'{player2.name}\'s ATK cannot be lowered below 1!')
        await player2.send(f'{player2.name}\'s ATK cannot be lowered below 1!')

    return modifiedGameState

async def heal(initialState, currentGameState, attackCaller):

# if this is the first action in the round

    player1 = client.get_user(int(initialState[0]))
    player2 = client.get_user(int(initialState[1]))
    modifiedGameState = initialState

    cursor.execute(f"""SELECT HP FROM UserInfo WHERE UID = {initialState[0]} """)
    p1MaxHP = cursor.fetchone()

    cursor.execute(f"""SELECT HP FROM UserInfo WHERE UID = {initialState[1]} """)
    p2MaxHP = cursor.fetchone()

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]: # = P1

            modifiedGameState = initialState[:2] + ((initialState[2] + initialState[6]),) + initialState[3:]

            if modifiedGameState[2]>p1MaxHP[0]:
                modifiedGameState = initialState[:2] + (p1MaxHP[0],) + initialState[3:]

            healAmount = modifiedGameState[2] - initialState[2]

            await player1.send(f'{player1.name} healed themselves for {healAmount} HP!')
            await player2.send(f'{player1.name} healed themselves for {healAmount} HP!')

        # if attack caller is p2
        else:

            modifiedGameState = initialState[:3] + ((initialState[3] + initialState[7]),) + initialState[4:]

            if modifiedGameState[3]>p2MaxHP[0]:
                modifiedGameState = initialState[:3] + (p2MaxHP[0],) + initialState[4:]

            healAmount = modifiedGameState[3] - initialState[3]

            await player1.send(f'{player2.name} healed themselves for {healAmount} HP!')
            await player2.send(f'{player2.name} healed themselves for {healAmount} HP!')

# if this is the second action in the round
    else:
        modifiedGameState = currentGameState
        # if attack caller is p1
        if attackCaller == initialState[0]:  # = P1

            modifiedGameState = currentGameState[:2] + ((currentGameState[2] + currentGameState[6]),) + currentGameState[3:]

            if modifiedGameState[2]>p1MaxHP[0]:
                modifiedGameState = currentGameState[:2] + (p1MaxHP[0],) + currentGameState[3:]

            healAmount = modifiedGameState[2] - currentGameState[2]

            await player1.send(f'{player1.name} healed themselves for {healAmount} HP!')
            await player2.send(f'{player1.name} healed themselves for {healAmount} HP!')

        # if attack caller is p2
        else:

            modifiedGameState = currentGameState[:3] + ((currentGameState[3] + currentGameState[7]),) + currentGameState[4:]

            if modifiedGameState[3]>p2MaxHP[0]:
                modifiedGameState = currentGameState[:3] + (p2MaxHP[0],) + currentGameState[4:]

            healAmount = modifiedGameState[3] - currentGameState[3]

            await player1.send(f'{player2.name} healed themselves for {healAmount} HP!')
            await player2.send(f'{player2.name} healed themselves for {healAmount} HP!')

    return modifiedGameState

async def quick_attack(initialState, currentGameState, attackCaller):

# if this is the first action in the round

    player1 = client.get_user(int(initialState[0]))
    player2 = client.get_user(int(initialState[1]))

    if currentGameState == 'first round':
        # if attack caller is p1
        if attackCaller == initialState[0]:
            modifiedGameState = initialState[:3] + ((initialState[3] - (initialState[6]/2)),) + initialState[4:]
            await player1.send(f'{player1.name} quick attacked {player2.name}, dealing {initialState[6]/2} damage.')
            await player2.send(f'{player1.name} quick attacked {player2.name}, dealing {initialState[6]/2} damage.')
        # if attack caller is p2
        else:
            modifiedGameState = initialState[:2] + ((initialState[2] - (initialState[7]/2)),) + initialState[3:]
            await player1.send(f'{player2.name} quick attacked {player1.name}, dealing {initialState[7]/2} damage.')
            await player2.send(f'{player2.name} quick attacked {player1.name}, dealing {initialState[7]/2} damage.')
# if this is the second action in the round
    else:
        # if attack caller is p1
        if attackCaller == initialState[0]:
            modifiedGameState = currentGameState[:3] + ((currentGameState[3] - (currentGameState[6]/2)),) + currentGameState[4:]
            await player1.send(f'{player1.name} quick attacked {player2.name}, dealing {initialState[6]/2} damage.')
            await player2.send(f'{player1.name} quick attacked {player2.name}, dealing {initialState[6]/2} damage.')
        # if attack caller is p2
        else:
            modifiedGameState = currentGameState[:2] + ((currentGameState[2] - (currentGameState[7]/2)),) + currentGameState[3:]
            await player1.send(f'{player2.name} quick attacked {player1.name}, dealing {initialState[7]/2} damage.')
            await player2.send(f'{player2.name} quick attacked {player1.name}, dealing {initialState[7]/2} damage.')

    # perform attack on p2 HP if attack caller is p1

    return modifiedGameState

# This function awaits a message, and if the message starts with !d, it proceeds to act on the command.
@client.event
async def on_message(message: object):

    if message.content.startswith('!d'):
        command = (message.content.split(' ')[1])

        command_list = {
            "registerMe": registerMe,
            "showInfo": showInfo,
            "challenge": challenge,
            "leaveFight": leaveFight,
            "replace": replace,
            "choose": chooseAttack,
            "moveList": moveList,
            "help": helpUser
        }

        await command_list.get(command, invalid_command)(message)

@client.event
async def on_ready():
    async def on_ready():
        print('Logged in as\n' + client.user.name + '\n' + client.user.id )

client.run(os.getenv('DISCORD_TOKEN')) # go online