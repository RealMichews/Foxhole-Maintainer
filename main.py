import discord
from discord.ext import commands
from discord.ext import tasks
from discord.utils import get
import sqlite3
import time

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

# TODO change this before pushing pls
TEST = False

configDBGlobal = sqlite3.connect('config.db')
configCursorGlobal = configDBGlobal.cursor()
queryGlobal = f'SELECT * FROM TGUILDDATA'
configCursorGlobal.execute(queryGlobal)
guildList = configCursorGlobal.fetchall()
configDBGlobal.close()


def calculate_timestamp(hourlyUsage, gsupps):
    hours = int(gsupps) / int(hourlyUsage)
    currentTime = int(time.time())
    newTime = currentTime + (hours * 60 * 60)
    return int(newTime)


def get_db_name(guildID):
    return f'foxdb{guildID}.db'


def get_war(dbName):
    guildDB = sqlite3.connect(dbName)
    guildCursor = guildDB.cursor()
    query = f'SELECT CONTENT FROM TGENERIC WHERE ATTRIBUTE = \'CURRENT_WAR\''
    guildCursor.execute(query)
    currentWar = int(guildCursor.fetchall()[0][0])
    guildDB.close()
    return currentWar


def check_channel_allowed(guildID, targetChannelID):
    checkChannelID = None
    for guild in guildList:
        if guild[0] == guildID:
            checkChannelID = guild[1]
    if checkChannelID:
        return targetChannelID == checkChannelID
    return False


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    auto_list_bunkers.start()


@bot.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send('Hey there! this is the Foxhole Maintainer. To set me up please use !set_admin_role'
                               ' and !set_bot_channel or the bot will not work. \n!set_admin_role will set the '
                               'required role for admin actions of the bot. (Admin Only) \n!set_bot_channel will set '
                               'the channel the bot reacts to. (Can only be done by people that have the previously'
                               ' set role with !set_admin_role)')
        break

    # Connect or Setup database
    guildID = str(guild.id)
    dbname = get_db_name(guildID)
    guildDB = sqlite3.connect(dbname)
    guildCursor = guildDB.cursor()
    # init DB
    guildCursor.execute('''
                    CREATE TABLE IF NOT EXISTS TBUNKER(
                    ID INT,
                    NAME TEXT,
                    WAR INT,
                    HOURLY_USAGE INT,
                    EXPIRY_DATE INT
                    )
                    ''')
    guildCursor.execute('''
                    CREATE TABLE IF NOT EXISTS TGENERIC(
                    ATTRIBUTE TEXT,
                    CONTENT TEXT
                    )
                    ''')
    query = f'SELECT * FROM TGENERIC WHERE ATTRIBUTE = \'CURRENT_WAR\''
    guildCursor.execute(query)
    result = guildCursor.fetchall()
    if result:
        pass
    else:
        query = f'INSERT INTO TGENERIC (ATTRIBUTE) VALUES (\'CURRENT_WAR\')'
        guildCursor.execute(query)
    # TODO: think of good way to store embed pics by hex
    '''
    query = f'SELECT * FROM TGENERIC WHERE ATTRIBUTE = \'EMBED_PICTURE\''
    guildCursor.execute(query)
    result = guildCursor.fetchall()
    if result:
        pass
    else:
        query = f'INSERT INTO TGENERIC (ATTRIBUTE) VALUES (\'EMBED_PICTURE\')'
        guildCursor.execute(query)
        '''
    guildDB.commit()
    guildDB.close()
    configDB = sqlite3.connect('config.db')
    configCursor = configDB.cursor()
    query = f'SELECT * FROM TGUILDDATA WHERE GUILDID = {guildID}'
    configCursor.execute(query)
    result = configCursor.fetchall()
    if result:
        query = f'UPDATE TGUILDDATA SET FL_AUTOMATION = 0 WHERE GUILDID = {guildID}'
        configCursor.execute(query)
    else:
        query = f'INSERT INTO TGUILDDATA (GUILDID, CHANNELID, FL_AUTOMATION) VALUES ({guildID}, 0, 0)'
        configCursor.execute(query)
    query = f'SELECT * FROM TGUILDDATA'
    configCursor.execute(query)
    global guildList
    guildList = configCursor.fetchall()
    configDB.commit()
    configDB.close()


@bot.command()
async def helpme(ctx, *args):
    targetChannelID = ctx.message.channel.id
    guildID = ctx.message.guild.id
    if check_channel_allowed(guildID, targetChannelID):
        if len(args) == 0:
            embed = discord.Embed(title="These are the currently available commands")
            embed.add_field(name="!add_bunker", value="This command adds a new bunker and can take between 1 to 3 "
                                                      "parameters. \nSyntax: !add_bunker NAME GSUPP/H GSUPPAMOUNT - "
                                                      "Just Name OR Name + gsupp/H are possible\nWhen naming a bunker "
                                                      "only use one continuous string. OK: SOSIG_HQ NOK: "
                                                      "SOSIG HQ'", inline=False)
            embed.add_field(name="!update_bunker", value="This command updates an existing bunker - only takes 3 para"
                                                         "meters. \nSyntax: !update_bunker NAME GSUPP/H "
                                                         "GSUPPAMOUNT", inline=False)
            embed.add_field(name="!update_gsupps", value="This command lets you update the gsupp amount for an "
                                                         "existing bunker - only takes 2 parameters. \nSyntax: "
                                                         "!update_gsupps NAME GSUPPAMOUNT", inline=False)
            embed.add_field(name="!delete_bunker", value="This command is for Officials only. Deletes an existing bun"
                                                         "ker - only takes 1 parameter. \nSyntax: !delete_bunker "
                                                         "NAME", inline=False)
            embed.add_field(name="!list_bunkers", value="This command lists all bunkers for the current or selected "
                                                        "war. It can take 0 to 1 parameters. \nSyntax: !list_bunkers "
                                                        "69 - If you do not specify a war the current war will be "
                                                        "selected.", inline=False)
            embed.add_field(name="!set_war", value="This command is for Officials only. Updates the current war to "
                                                   "distinguish bunkers between wars. \nSyntax: "
                                                   "!set_war 69", inline=False)
            await ctx.send(embed=embed)
        if len(args) > 0:
            await ctx.send(f'Why the fuck did you pass a parameter to the help command?')


def check_admin(userRoles, guildID):
    configDB = sqlite3.connect("config.db")
    configCursor = configDB.cursor()
    query = f'SELECT ADMIN_ROLES FROM TGUILDDATA WHERE GUILDID = {guildID}'
    configCursor.execute(query)
    result = configCursor.fetchall()[0][0]
    isAdmin = False
    for role in userRoles:
        if str(role.id) in str(result):
            isAdmin = True
    return isAdmin


@bot.command()
async def set_admin_role(ctx, *args):
    userRoles = ctx.author.roles
    guildID = ctx.message.guild.id
    isAdmin = check_admin(userRoles, guildID)
    if ctx.author.guild_permissions.administrator or isAdmin:
        if len(args) > 1:
            await ctx.send("This command can only do one role at the same time")
        if len(args) == 0:
            await ctx.send("Explanation")
        if len(args) == 1:
            newAdminRole = str(args[0]).replace("@", "").replace("&", "").replace("<", "").replace(">", "")
            configDB = sqlite3.connect("config.db")
            configCursor = configDB.cursor()
            query = f'SELECT ADMIN_ROLES FROM TGUILDDATA WHERE GUILDID = {guildID}'
            configCursor.execute(query)
            result = configCursor.fetchall()[0][0]
            if not result:
                query = f'UPDATE TGUILDDATA SET ADMIN_ROLES = \'{newAdminRole}\' WHERE GUILDID = {guildID}'
                configCursor.execute(query)
                configDB.commit()
            else:
                if newAdminRole in str(result):
                    await ctx.send("Role is already registered as admin.")
                else:
                    newAdminRoles = f'{result},{newAdminRole}'
                    query = f'UPDATE TGUILDDATA SET ADMIN_ROLES = \'{newAdminRoles}\' WHERE GUILDID = {guildID}'
                    configCursor.execute(query)
                    configDB.commit()
            query = f'SELECT * FROM TGUILDDATA'
            configCursor.execute(query)
            global guildList
            guildList = configCursor.fetchall()
            configDB.close()
    else:
        await ctx.send("This command can only be used by administrators.")


@bot.command()
async def set_bot_channel(ctx, *args):
    userRoles = ctx.author.roles
    guildID = ctx.message.guild.id
    isAdmin = check_admin(userRoles, guildID)
    if ctx.author.guild_permissions.administrator or isAdmin:
        configDB = sqlite3.connect('config.db')
        configCursor = configDB.cursor()

        if len(args) == 0:
            await ctx.send('Please enter the bot channel id (Copy Link, last set of numbers after the slash).')
        if len(args) > 1:
            await ctx.send('Please only enter one number.')
        if len(args) == 1:
            try:
                tmp = int(args[0])
                query = f'UPDATE TGUILDDATA SET CHANNELID = \'{args[0]}\' WHERE GUILDID = \'{guildID}\''
                configCursor.execute(query)
                query = f'SELECT * FROM TGUILDDATA'
                configCursor.execute(query)
                global guildList
                guildList = configCursor.fetchall()
                configDB.commit()
                configDB.close()
                await ctx.send(f'The bot channel has been set to <#{args[0]}>')
            except:
                await ctx.send('Please use a number.')
    else:
        await ctx.send(f'You are not allowed to run this command.')


@bot.command()
async def set_war(ctx, *args):
    targetChannelID = ctx.message.channel.id
    guildID = ctx.message.guild.id
    if check_channel_allowed(guildID, targetChannelID):
        userRoles = ctx.author.roles
        guildID = ctx.message.guild.id
        isAdmin = check_admin(userRoles, guildID)
        if ctx.author.guild_permissions.administrator or isAdmin:
            dbName = get_db_name(guildID)
            guildDB = sqlite3.connect(dbName)
            guildCursor = guildDB.cursor()

            if len(args) == 0:
                await ctx.send('Please enter the current war number.')
            if len(args) > 1:
                await ctx.send('Please only enter one number.')
            if len(args) == 1:
                try:
                    tmp = int(args[0])
                    query = f'UPDATE TGENERIC SET CONTENT = \'{args[0]}\' WHERE ATTRIBUTE = \'CURRENT_WAR\''
                    guildCursor.execute(query)
                    guildDB.commit()
                    guildDB.close()
                    await ctx.send(f'The current war has been set to {args[0]}')
                except:
                    await ctx.send('Unable to update current war. Please try to use a number.')
        else:
            await ctx.send(f'You are not allowed to run this command.')

    else:
        print("Channel not allowed")


@bot.command()
async def add_bunker(ctx, *args):
    guildID = ctx.message.guild.id
    targetChannelID = ctx.message.channel.id
    if check_channel_allowed(guildID, targetChannelID):
        dbName = get_db_name(guildID)
        currentWar = get_war(dbName)
        guildDB = sqlite3.connect(dbName)
        guildCursor = guildDB.cursor()

        def check_name(name):

            query = f'SELECT * FROM TBUNKER WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
            guildCursor.execute(query)
            return guildCursor.fetchall()

        def generate_ID():

            # Find missing IDs
            def find_missing(lst):
                if len(lst) > 1:
                    return [x for x in range(lst[0], lst[-1] + 1)
                            if x not in lst]

            query = f'SELECT ID FROM TBUNKER ORDER BY ID'
            guildCursor.execute(query)
            result = guildCursor.fetchall()
            IDs = [i[0] for i in result]
            nextIDs = find_missing(IDs)
            if nextIDs:
                return nextIDs[0]
            elif result:
                return result[-1][0] + 1
            else:
                return '1'

        if len(args) == 0:
            await ctx.send('This command adds bunkers to our database. The syntax is !add_bunker BUNKERNAME '
                           'GSUPPCONSUMPTION/H CURRENTAMOUNTGSUPPS. \nExamples: \n!add_bunker SOSIG_HQ 100 5000 \n'
                           '!add_bunker SOSIG_HQ 50 \n!add_bunker SOSIG_HQ')

        if len(args) == 1:
            '''
            Add new bunker (Name Only)
            '''
            name = args[0]

            # Check name for this war
            if check_name(name):
                await ctx.send(f'The Bunker {name} already exists for War {currentWar}. No changes were made.')
                return

            # Searching next ID
            ID = generate_ID()
            # Inserting into DB
            query = f'INSERT INTO TBUNKER (ID, NAME, WAR) VALUES ({ID}, \'{name}\', \'{currentWar}\')'
            guildCursor.execute(query)
            guildDB.commit()
            guildDB.close()
            await ctx.send(f'{ctx.author} has created the new bunker {name}')

        if len(args) == 2:
            '''
            Add new bunker (Name and Consumption)
            '''
            name = args[0]

            # Check name for this war
            if check_name(name):
                await ctx.send(f'The Bunker {name} already exists for War {currentWar}. No changes were made.')
                return

            try:
                tmp = int(args[1])
                # Searching next ID to insert new Bunker
                ID = generate_ID()
                # Inserting into DB
                query = f'INSERT INTO TBUNKER (ID, NAME, WAR, HOURLY_USAGE) VALUES ({ID}, \'{name}\', ' \
                        f'\'{currentWar}\', \'{args[1]}\')'
                guildCursor.execute(query)
                guildDB.commit()
                guildDB.close()
                await ctx.send(
                    f'{ctx.author} has created the new bunker {args[0]} with a Garrison Supply consumption of '
                    f'{args[1]} per hour.')
            except:
                await ctx.send('Please use a number for the hourly usage and amount of garrison supplies.')

        if len(args) == 3:
            # Add new bunker (Name, Consumption and Gsupp Level)
            name = args[0]
            # Check name for this war
            if check_name(name):
                await ctx.send(f'The Bunker {name} already exists for War {currentWar}. No changes were made.')
                return

            try:
                tmp = int(args[1])
                tmp = int(args[2])
                # Searching next ID to insert new Bunker
                ID = generate_ID()
                timestamp = calculate_timestamp(args[1], args[2])
                # Inserting into DB
                query = f'INSERT INTO TBUNKER (ID, NAME, WAR, HOURLY_USAGE, EXPIRY_DATE) VALUES ({ID}, \'{name}\', ' \
                        f'\'{currentWar}\', \'{args[1]}\', \'{timestamp}\')'
                guildCursor.execute(query)
                guildDB.commit()
                guildDB.close()
                await ctx.send(f'{ctx.author} has created the new bunker {args[0]} with a Garrison Supply consumption '
                               f'of {args[1]} per hour. With the current amount of {args[2]} Garrison Supplies it is '
                               f'maintained until <t:{timestamp}:f>')
            except:
                await ctx.send('Please use a number for the hourly usage and amount of garrison supplies.')

        if len(args) > 3:
            await ctx.send(f'Please enter less Variables, this command takes 1 to 3 parameters. Syntax:\n'
                           f'!add_bunker NAME GSUPP/H GSUPPAMOUNT\nExamples:\n!add_bunker SOSIG_HQ 100 5000 \n'
                           '!add_bunker SOSIG_HQ 50 \n!add_bunker SOSIG_HQ')


@bot.command()
async def update_bunker(ctx, *args):
    guildID = ctx.message.guild.id
    targetChannelID = ctx.message.channel.id
    if check_channel_allowed(guildID, targetChannelID):
        dbName = get_db_name(guildID)
        currentWar = get_war(dbName)
        guildDB = sqlite3.connect(dbName)
        guildCursor = guildDB.cursor()

        def check_name(name):
            query = f'SELECT * FROM TBUNKER WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
            guildCursor.execute(query)
            return guildCursor.fetchall()

        if len(args) == 0:
            await ctx.send(f'This command updates an existing bunker - only takes 3 parameters. Syntax:\n'
                           f'!update_bunker NAME GSUPP/H GSUPPAMOUNT')
        if len(args) == 1:
            await ctx.send(f'Please enter additional Variables, this command only takes exactly 3 parameters. Syntax:\n'
                           f'!update_bunker NAME GSUPP/H GSUPPAMOUNT')
        if len(args) == 2:
            await ctx.send(f'Please enter additional Variables, this command only takes exactly 3 parameters. Syntax:\n'
                           f'!update_bunker NAME GSUPP/H GSUPPAMOUNT')
        if len(args) > 3:
            await ctx.send(f'Please enter less Variables, this command only takes exactly 3 parameters. Syntax:\n'
                           f'!update_bunker NAME GSUPP/H GSUPPAMOUNT')
        if len(args) == 3:
            name = args[0]
            hourlyUsage = args[1]
            gsupps = args[2]
            if not check_name(name):
                await ctx.send(f'The Bunker \'{name}\' does not exist in the database for war \'{currentWar}\'')
            else:
                try:
                    tmp = int(args[1])
                    tmp = int(args[2])
                    timestamp = calculate_timestamp(hourlyUsage, gsupps)
                    query = f'UPDATE TBUNKER SET HOURLY_USAGE = \'{hourlyUsage}\', EXPIRY_DATE = \'{timestamp}\' ' \
                            f'WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
                    guildCursor.execute(query)
                    guildDB.commit()
                    guildDB.close()
                    await ctx.send(
                        f'The Bunker {name} in war {currentWar} has been updated to use {hourlyUsage} Garrison '
                        f'Supplies per hour. With the current amount of {gsupps} Garrison Supplies it is '
                        f'maintained until <t:{timestamp}:f>')
                except:
                    await ctx.send('Please use a number for the hourly usage and amount of garrison supplies.')


@bot.command()
async def update_gsupps(ctx, *args):
    guildID = ctx.message.guild.id
    targetChannelID = ctx.message.channel.id
    if check_channel_allowed(guildID, targetChannelID):
        dbName = get_db_name(guildID)
        currentWar = get_war(dbName)
        guildDB = sqlite3.connect(dbName)
        guildCursor = guildDB.cursor()

        # Wtf is this function
        def check_name(name):
            query = f'SELECT * FROM TBUNKER WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
            guildCursor.execute(query)
            return guildCursor.fetchall()

        def check_hourly_usage(name):
            query = f'SELECT HOURLY_USAGE FROM TBUNKER WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
            guildCursor.execute(query)
            return guildCursor.fetchall()[0][0]

        if len(args) == 0:
            await ctx.send(f'This command lets you update the gsupp amount for an existing bunker - '
                           f'only takes 2 parameters. Syntax:\n'
                           f'!update_gsupps NAME GSUPPAMOUNT')
        if len(args) == 1:
            await ctx.send('Please enter additional Variables, this command only takes 2 parameters. Syntax:\n'
                           f'!update_gsupps NAME GSUPPAMOUNT')
        if len(args) > 2:
            await ctx.send('Please enter less Variables, this command only takes 2 parameters. Syntax:\n'
                           f'!update_gsupps NAME GSUPPAMOUNT')
        if len(args) == 2:
            name = args[0]
            gsupps = args[1]
            if not check_name(name):
                await ctx.send(f'The Bunker \'{name}\' does not exist in the database for war \'{currentWar}\'')
            else:
                try:
                    tmp = int(args[1])
                    hourlyUsage = check_hourly_usage(name)
                    timestamp = calculate_timestamp(hourlyUsage, gsupps)
                    query = f'UPDATE TBUNKER SET HOURLY_USAGE = \'{hourlyUsage}\', EXPIRY_DATE = \'{timestamp}\' ' \
                            f'WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
                    guildCursor.execute(query)
                    guildDB.commit()
                    guildDB.close()
                    await ctx.send(
                        f'The Bunker {name} in war {currentWar} has been updated to the current amount of {gsupps} '
                        f'Garrison Supplies it is maintained until <t:{timestamp}:f>')
                except:
                    await ctx.send('Please use a number for the amount of garrison supplies.')


@bot.command()
async def delete_bunker(ctx, *args):
    guildID = ctx.message.guild.id
    targetChannelID = ctx.message.channel.id
    if check_channel_allowed(guildID, targetChannelID):
        dbName = get_db_name(guildID)
        currentWar = get_war(dbName)
        guildDB = sqlite3.connect(dbName)
        guildCursor = guildDB.cursor()

        if len(args) == 0:
            await ctx.send(f'!delete_bunker - This command is for Officials only. Deletes an existing bunker - only '
                           f'takes 1 parameter. Syntax:\ndelete_bunker NAME')

        if len(args) == 1:

            roles = ctx.author.roles
            Officials = get(ctx.guild.roles, name='Harbour Officials')

            if 'Harbour Officials' not in str(roles):
                await ctx.send(f'You are not allowed to run this command {Officials.mention}')
            else:
                name = args[0]

                # Wtf is this function
                def check_name(name):
                    query = f'SELECT * FROM TBUNKER WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
                    guildCursor.execute(query)
                    return guildCursor.fetchall()

                if not check_name(name):
                    await ctx.send(f'The bunker {name} does not exist.')
                else:
                    query = f'DELETE FROM TBUNKER WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
                    guildCursor.execute(query)
                    guildDB.commit()
                    guildDB.close()
                    await ctx.send(f'The bunker {name} has been deleted')
        if len(args) > 1:
            await ctx.send('Please use only one parameter (Bunker name)')



@bot.command()
async def set_picture(ctx, *args):
    #TODO make it so we can change the pic
    pass


def bunkers(title, description, war, dbName):
    guildDB = sqlite3.connect(dbName)
    cursor = guildDB.cursor()
    query = f'SELECT * FROM TBUNKER WHERE WAR = \'{war}\''
    cursor.execute(query)
    result = cursor.fetchall()

    embed = discord.Embed(title=title, description=description)
    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1038473765513855006/1046248642891235378/"
                            "SOSIG98.jpg?width=1618&height=910")
    gsupptotal = 0
    for bunker in result:
        currentTime = int(time.time())
        if bunker[3] and bunker[4]:
            if bunker[4] - currentTime < 0:
                name = f'{bunker[1]}:bangbang:'
                text = f'Actively decaying since <t:{bunker[4]}:f>. Last known usage is {bunker[3]} Garrison ' \
                       f'Supplies per hour.'
                embed.add_field(name=name, value=text, inline=False)
            elif bunker[4] - currentTime < 3600:
                name = f'{bunker[1]} :red_circle:'
                text = f'Supplied until <t:{bunker[4]}:f> at a rate of {bunker[3]} Garrison ' \
                       f'Supplies per hour.'
                embed.add_field(name=name, value=text, inline=False)
            elif bunker[4] - currentTime < 86400:
                name = f'{bunker[1]} :yellow_circle:'
                text = f'Supplied until <t:{bunker[4]}:f> at a rate of {bunker[3]} Garrison ' \
                       f'Supplies per hour.'
                embed.add_field(name=name, value=text, inline=False)
            else:
                name = f'{bunker[1]}'
                text = f'Supplied until <t:{bunker[4]}:f> at a rate of {bunker[3]} Garrison ' \
                       f'Supplies per hour.'
                embed.add_field(name=name, value=text, inline=False)
        elif bunker[3]:
            name = f'{bunker[1]} :question:'
            text = f'No gsupp amount information, uses a rate of {bunker[3]} Garrison Supplies per ' \
                   f'hour.'
            embed.add_field(name=name, value=text, inline=False)
        else:
            name = f'{bunker[1]} :question::question:'
            text = f'Saved in the database but has no gsupp values.'
            embed.add_field(name=name, value=text, inline=False)
        if bunker[3]:
            gsupptotal += bunker[3]
    dailyCrates = gsupptotal * 24 / 150
    text = f'Our current maintenance of {gsupptotal} Garrison Supplies per hour needs **{dailyCrates}** crates of ' \
           f'Garrison Supplies per day.'
    embed.add_field(name="Total Consumption and Crate Usage", value=text, inline=False)
    guildDB.close()
    return embed


@bot.command()
async def list_bunkers(ctx, *args):
    guildID = ctx.message.guild.id
    dbName = get_db_name(guildID)
    currentWar = get_war(dbName)
    targetChannelID = ctx.message.channel.id
    targetChannel = ctx.message.channel
    if check_channel_allowed(guildID, targetChannelID):
        if len(args) > 1:
            await ctx.send('Please only use one number.')
        if len(args) == 0:
            title = f'Current Bunker List'
            description = f'Showing bunkers for the current war {currentWar}. Times shown are in your timezone. ' \
                          f'Timings can change as consumption fluctuates. Keep everything updated.\nBunkers with a ' \
                          f':yellow_circle: run out of gsupps in 1 day.\nBunkers with a :red_circle: run out of ' \
                          f'gsupps in 1 hour. \nBunkers with a :bangbang: are actively decaying.'
            await targetChannel.send(embed=bunkers(title, description, currentWar, dbName))
        if len(args) == 1:
            title = f'Current Bunker List'
            description = f'Showing bunkers for the current war {args[0]}. Times shown are in your timezone. Timings ' \
                          f'can change as consumption fluctuates. Keep everything updated.\nBunkers with a ' \
                          f':yellow_circle: run out of gsupps in 1 day.\nBunkers with a :red_circle: run out of ' \
                          f'gsupps in 1 hour. \nBunkers with a :bangbang: are actively decaying.'
            await targetChannel.send(embed=bunkers(title, description, args[0], dbName))
    else:
        print("checkChannelID not found. Problem")


# TODO change this before pushing
@tasks.loop(hours=1)
async def auto_list_bunkers():
    if guildList:
        for guild in guildList:
            if guild[2] == 1:
                guildID = guild[0]
                dbName = get_db_name(guildID)
                targetChannelID = guild[1]
                currentWar = get_war(dbName)
                channel = bot.get_channel(targetChannelID)
                title = f'Hourly Maintenance Update'
                description = f'Showing bunkers for the current war {currentWar}. Times shown are in your timezone. ' \
                              f'Timings can change as consumption fluctuates. Keep everything updated.\nBunkers with ' \
                              f'a :yellow_circle: run out of gsupps in 1 day.\nBunkers with a :red_circle: run out ' \
                              f'of gsupps in 1 hour. \nBunkers with a :bangbang: are actively decaying.'
                await channel.send(embed=bunkers(title, description, currentWar, dbName))
            else:
                pass


@bot.command()
async def start_bunker_updates(ctx):
    configDB = sqlite3.connect('config.db')
    configCursor = configDB.cursor()
    guildID = ctx.message.guild.id
    query = f'UPDATE TGUILDDATA SET FL_AUTOMATION = 1 WHERE GUILDID = {guildID}'
    configCursor.execute(query)
    query = f'SELECT * FROM TGUILDDATA'
    configCursor.execute(query)
    global guildList
    guildList = configCursor.fetchall()
    configDB.commit()
    configDB.close()


@bot.command()
async def stop_bunker_updates(ctx):
    configDB = sqlite3.connect('config.db')
    configCursor = configDB.cursor()
    guildID = ctx.message.guild.id
    query = f'UPDATE TGUILDDATA SET FL_AUTOMATION = 0 WHERE GUILDID = {guildID}'
    configCursor.execute(query)
    query = f'SELECT * FROM TGUILDDATA'
    configCursor.execute(query)
    global guildList
    guildList = configCursor.fetchall()
    configDB.commit()
    configDB.close()


@bot.command()
async def init_automation(ctx):
    auto_list_bunkers.start()


@bot.command()
async def kill_automation(ctx):
    auto_list_bunkers.stop()


if TEST:
    with open('iamsotesty.txt') as f:
        content = f.readlines()[0]
else:
    with open('iamsosecure.txt') as f:
        content = f.readlines()[0]

bot.run(content)
