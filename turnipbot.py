#turnip tracker and queue bot version 1.0
#4/19/2020

import discord
from discord.ext import commands, tasks
import datetime as dt
import pytz, time
from collections import deque

#simple namespace to keep track of status
class Status:
    maximum = 0
    minimum = -1
    min_users = []
    max_users = []
    data = {}
    dates = {}
    dodo = None
    start = False
    owner = None

#just a few global variables
client = commands.Bot(command_prefix="!")
client.remove_command("help")
#channels to allow bot commands in 
whitelist_chan = ("stalk-market-prices", "market", "island-is-open", "general")
restricted = "restricted channel"
stat = Status()
line = deque()


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))

#background task that dm dodo code every 2 minutes
@tasks.loop(minutes=2)
async def process_line():
    if len(line)!=0 and stat.dodo != None and stat.start == True:
        user = line.popleft()
        print(len(line))
        await user.send("Your turn. DODO code is {}".format(stat.dodo))
    elif len(line)==0:
        print(pytz.utc.localize(dt.datetime.utcnow()).astimezone(pytz.timezone("America/Los_Angeles")).isoformat())

#check wait time
@client.command()
async def wait(ctx):
    try:
        n = line.index(ctx.author)
        await ctx.send("you are #{} in line, about {} minutes".format(n+1,(n+1)*2))
    except ValueError:
        n = len(line)
        await ctx.send("there are {} users in line".format(n))

@client.command()
async def owner(ctx):
    if stat.start and stat.owner:
        await ctx.send("The line for {} is active.".format(stat.owner))
    elif stat.owner and not stat.start:
        await ctx.send("the line for {} is paused.".format(stat.owner))
    else:
        await ctx.send("no line started")

#join sender to line
@client.command()
async def joinq(ctx):
    if ctx.author in line:
        await ctx.send("you're already in line")
    else:
        line.append(ctx.author)
        if stat.owner:
            await ctx.send("you are #{} in {}'s line".format(len(line), stat.owner))
        else:
            await ctx.send("you are #{} in line".format(len(line)))

#leave sender from line
@client.command()
async def leaveq(ctx):
    try:
        line.remove(ctx.author)
        await ctx.send("{} left the line.".format(ctx.author))
    except ValueError:
        await ctx.send("You weren't in line.")

#start processing the line via dm to bot must provide dodo code
@client.command()
async def startq(ctx, msg):
    if type(ctx.channel) == discord.channel.DMChannel:
        if len(str(msg)) == 5:
            stat.dodo = msg
            stat.owner = ctx.author
            stat.start = True
            print(stat.dodo)
            print(ctx.author)
            await ctx.send("dodo code set")
        else:
            await ctx.send("invalid code")        
    else:
        await ctx.send(restricted)

#stop/pause processing line
@client.command()
async def stopq(ctx):
    stat.start = False
    await ctx.send("stopping line")

#register turnip prices
@client.command()
async def turnip(ctx, msg):
    if str(ctx.channel) in whitelist_chan:
        try:
            bells = int(msg)
            user = ctx.author.name
            pst_now = pytz.utc.localize(dt.datetime.utcnow()).astimezone(pytz.timezone("America/Los_Angeles")).isoformat()

            stat.data[user] = bells    
            stat.dates[user] = pst_now
            maxkey = max(stat.data, key=stat.data.get)
            maxbell = stat.data[maxkey]
            minkey = min(stat.data, key=stat.data.get)
            minbell = stat.data[minkey]

            stat.max_users.clear()
            stat.maximum = maxbell
            stat.min_users.clear()
            stat.minimum = minbell    

            for k, v in stat.data.items():
                if v == stat.maximum:
                    stat.max_users.append(k)
                if v == stat.minimum:
                    stat.min_users.append(k)

            await ctx.send("{}'s turnips were registered".format(ctx.author))
        except ValueError:
            print(ValueError)
            await ctx.send("error, not a number")
    else:
        await ctx.send(restricted)

#get who has highest
@client.command(aliases=["max", "high"])
async def maxt(ctx):
    if str(ctx.channel) in whitelist_chan:
        body = "Highest Turnip Price: {}".format(stat.maximum)
        if stat.max_users:
            comma = ", "
            all = ""
            if len(stat.max_users) == 1:
                all = stat.max_users[0]
            else:
                all = comma.join(stat.max_users)
            body += "\n"
            body += "From: "
            body += all
            body += "\n"
            body += "Last Updated: "
            body += stat.dates[stat.max_users[-1]]
        await ctx.send(body)
    else:
        await ctx.send(restricted)

#get who has lowest
@client.command(aliases=["min", "low"])
async def mint(ctx):
    if str(ctx.channel) in whitelist_chan:
        body = "Lowest Turnip Price: {}".format(stat.minimum)
        if stat.min_users:
            comma = ", "
            all = ""
            if len(stat.min_users) == 1:
                all = stat.min_users[0]
            else:
                all = comma.join(stat.min_users)
            body += "\n"
            body += "From: "
            body += all
            body += "\n"
            body += "Last Updated: "
            body += stat.dates[stat.min_users[-1]]
        await ctx.send(body)
    else:
        await ctx.send(restricted)

#help message
@client.command(aliases=["helpbot"])
async def help(ctx):
    body  = """type '!turnip' $$$ to register your turnip price.
type '!max' or '!high' to get highest price.
type '!min' or 'low' to get lowest price.
DM the bot with '!startq' XXXXX (dodo code) to start the line.
type '!joinq' to add yourself to the line.
type '!wait' to get your wait time.
type '!stopq' to stop/pause the line.
type '!leaveq' to leave the line.
type '!owner' to see who started the line
Time format 'YYYY-MM-DDTHH:mm:ss+tz.
"""
    await ctx.send(body)

# debug command  
# @client.command()
# async def _test(ctx):
#     print("Dodo:",stat.dodo)
#     print("Line:",len(line))
#     print("Strt:",stat.start)
#     print("Clse:",client.is_closed())
#     print("Late:",client.latency)

#hello world
@client.command()
async def greet(ctx):
   await ctx.send("hello {}".format(ctx.author))


if __name__ == '__main__':
    process_line.start()
    token = "Your Token Goes Here" #Please follow instructions for registering your bot with discord and getting token: https://discordpy.readthedocs.io/en/latest/discord.html#
    client.run(token, reconnect=True)
