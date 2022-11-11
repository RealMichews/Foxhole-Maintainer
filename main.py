import discord
from discord.ext import commands
from discord.utils import get
import sqlite3
import time

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

db = sqlite3.connect('foxdb.db')
cursor = db.cursor()
query = f'SELECT CONTENT FROM TGENERIC WHERE ATTRIBUTE = \'CURRENT_WAR\''
cursor.execute(query)
currentWar = cursor.fetchall()[0][0]
db.close()


def calculate_timestamp(hourlyUsage, gsupps):
    hours = int(gsupps) / int(hourlyUsage)
    currentTime = int(time.time())
    newTime = currentTime + (hours * 60 * 60)
    return int(newTime)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.command()
async def set_war(ctx, *args):
    channel = ctx.message.channel.name
    if channel in ["test", "maintenance-bot"]:
        roles = ctx.author.roles
        if 'Harbour Officials' not in str(roles):
            await ctx.send(f'You are not allowed to run this command.')
        else:
            db = sqlite3.connect('foxdb.db')
            cursor = db.cursor()

            if len(args) == 0:
                await ctx.send('Please enter the current war number.')
            if len(args) > 1:
                await ctx.send('Please only enter one number.')
            if len(args) == 1:
                try:
                    tmp = int(args[0])
                    query = f'UPDATE TGENERIC SET CONTENT = \'{args[0]}\' WHERE ATTRIBUTE = \'CURRENT_WAR\''
                    cursor.execute(query)
                    db.commit()
                    db.close()
                    await ctx.send(f'The current war has been set to {args[0]}')
                except:
                    await ctx.send('Please use a number.')





@bot.command()
async def add_bunker(ctx, *args):
    """
    !add_bunker NAME GSUPP_PER_HOUR CURRENT_GSUPPS
    Example:
    !add_bunker SOSIG_HQ 100 5000
    """

    channel = ctx.message.channel.name
    if channel in ["test", "maintenance-bot"]:

        db = sqlite3.connect('foxdb.db')
        cursor = db.cursor()

        def check_name(name):

            query = f'SELECT * FROM TBUNKER WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
            cursor.execute(query)
            return cursor.fetchall()

        def generate_ID():

            # Find missing IDs
            def find_missing(lst):
                if len(lst) > 1:
                    return [x for x in range(lst[0], lst[-1] + 1)
                            if x not in lst]

            query = f'SELECT ID FROM TBUNKER ORDER BY ID'
            cursor.execute(query)
            result = cursor.fetchall()
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
            cursor.execute(query)
            db.commit()
            db.close()
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
                query = f'INSERT INTO TBUNKER (ID, NAME, WAR, HOURLY_USAGE) VALUES ({ID}, \'{name}\', \'{currentWar}\', ' \
                        f'\'{args[1]}\')'
                cursor.execute(query)
                db.commit()
                db.close()
                await ctx.send(f'{ctx.author} has created the new bunker {args[0]} with a Garrison Supply consumption of '
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
                cursor.execute(query)
                db.commit()
                db.close()
                await ctx.send(f'{ctx.author} has created the new bunker {args[0]} with a Garrison Supply consumption '
                               f'of {args[1]} per hour. With the current amount of {args[2]} Garrison Supplies it is '
                               f'maintained until <t:{timestamp}:f>')
            except:
                await ctx.send('Please use a number for the hourly usage and amount of garrison supplies.')


        if len(args) > 3:
            await ctx.send('You used the command wrong. Example: !add_bunker SOSIG_HQ 100 5000')


@bot.command()
async def update_bunker(ctx, *args):

    channel = ctx.message.channel.name
    if channel in ["test", "maintenance-bot"]:
        db = sqlite3.connect('foxdb.db')
        cursor = db.cursor()

        def check_name(name):
            query = f'SELECT * FROM TBUNKER WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
            cursor.execute(query)
            return cursor.fetchall()

        if len(args) == 0:
            await ctx.send('Explanation')
        if len(args) == 1:
            await ctx.send('Please enter additional Variables, Explanation')
        if len(args) == 2:
            await ctx.send('Please enter additional Variables, Explanation')
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
                    query = f'UPDATE TBUNKER SET HOURLY_USAGE = \'{hourlyUsage}\', EXPIRY_DATE = \'{timestamp}\' WHERE NAME = ' \
                            f'\'{name}\' AND WAR = \'{currentWar}\''
                    print(query)
                    cursor.execute(query)
                    db.commit()
                    db.close()
                    await ctx.send(f'The Bunker {name} in war {currentWar} has been updated to use {hourlyUsage} Garrison '
                                   f'Supplies per hour. With the current amount of {gsupps} Garrison Supplies it is '
                                   f'maintained until <t:{timestamp}:f>')
                except:
                    await ctx.send('Please use a number for the hourly usage and amount of garrison supplies.')




@bot.command()
async def update_gsupps(ctx, *args):

    channel = ctx.message.channel.name
    if channel in ["test", "maintenance-bot"]:
        db = sqlite3.connect('foxdb.db')
        cursor = db.cursor()

        def check_name(name):
            query = f'SELECT * FROM TBUNKER WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
            cursor.execute(query)
            return cursor.fetchall()

        def check_hourly_usage(name):
            query = f'SELECT HOURLY_USAGE FROM TBUNKER WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
            cursor.execute(query)
            return cursor.fetchall()[0][0]

        if len(args) == 0:
            await ctx.send('Explanation')
        if len(args) == 1:
            await ctx.send('Please enter additional Variables, Explanation')
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
                    cursor.execute(query)
                    db.commit()
                    db.close()
                    await ctx.send(
                        f'The Bunker {name} in war {currentWar} has been updated to the current amount of {gsupps} '
                        f'Garrison Supplies it is maintained until <t:{timestamp}:f>')
                except:
                    await ctx.send('Please use a number for the amount of garrison supplies.')


@bot.command()
async def delete_bunker(ctx, *args):

    channel = ctx.message.channel.name
    if channel in ["test", "maintenance-bot"]:
        db = sqlite3.connect('foxdb.db')
        cursor = db.cursor()

        if len(args) == 0:
            await ctx.send('Explanation')

        if len(args) == 1:

            roles = ctx.author.roles
            Officials = get(ctx.guild.roles, name ='Harbour Officials')

            if 'Harbour Officials' not in str(roles):
                await ctx.send(f'You are not allowed to run this command {Officials.mention}')
            else:
                name = args[0]

                def check_name(name):
                    query = f'SELECT * FROM TBUNKER WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
                    cursor.execute(query)
                    return cursor.fetchall()

                if not check_name(name):
                    await ctx.send(f'The bunker {name} does not exist.')
                else:
                    query = f'DELETE FROM TBUNKER WHERE NAME = \'{name}\' AND WAR = \'{currentWar}\''
                    cursor.execute(query)
                    db.commit()
                    db.close()
                    await ctx.send(f'The bunker {name} has been deleted')
        if len(args) > 1:
            await ctx.send('Please use only one argument (Bunker name)')


@bot.command()
async def list_bunkers(ctx, *args):

    channel = ctx.message.channel.name
    if channel in ["test", "maintenance-bot"]:
        db = sqlite3.connect('foxdb.db')
        cursor = db.cursor()

        if len(args) == 0:
            query = f'SELECT * FROM TBUNKER WHERE WAR = \'{currentWar}\''
            cursor.execute(query)
            result = cursor.fetchall()
            await ctx.send(f'Showing bunkers for the current war {currentWar}')
            for bunker in result:
                await ctx.send(f'\n{bunker[1]} is supplied until <t:{bunker[4]}:f> at a rate of {bunker[3]} Garrison '
                               f'Supplies per hour.')
        if len(args) == 1:
            try:
                tmp = int(args[0])
                query = f'SELECT * FROM TBUNKER WHERE WAR = \'{args[0]}\''
                cursor.execute(query)
                result = cursor.fetchall()
                await ctx.send(f'Showing bunkers for the war {args[0]}')
                for bunker in result:
                    await ctx.send(f'{bunker[1]} is supplied until <t:{bunker[4]}:f> at a rate of {bunker[3]} Garrison '
                                   f'Supplies per hour.')
            except:
                await ctx.send('Please use a number.')

        if len(args) > 1:
            await ctx.send('Please only use one number.')


with open('iamsosecure.txt') as f:
    content = f.readlines()[0]

bot.run(content)
