from flask import Flask, redirect, request, session, url_for
from discord.ext import commands
import requests
import discord
import asyncio


import json

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to a secure secret key
client_id = "1207763757715951646"
client_secret = "pKtPqB8PcqRGDOE0NpLmtGBlSNfzVVrF"
redirect_uri = "https://5b5af42a-a5d8-4f74-b2f9-509a2de7b9fe-00-1bxu3pv3nu2b1.picard.replit.dev/callback"
discord_api_url = "https://discord.com/api"
bot_token = ""

intents = discord.Intents.all()
intents.guilds = True  # Required to receive guild-related events
intents.members = True  # Required to receive member-related events

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command(name='helpe')
async def help_command(ctx):
    help_message = (
        "Welcome to the Bot!\n"
        "`!help`: Display this message.\n"
        "`!server_info <server_id>`: Display information about a specific server.\n"
        "`!manage_server <server_id>`: Manage a specific server.\n"
        "`!logout`: Log out and redirect to the home page."
    )
    await ctx.send(help_message)

@bot.command(name='ping')
async def ping_command(ctx):
    await ctx.send('Pong! Latency is {:.2f}ms'.format(bot.latency * 1000))

from discord import Embed
@bot.command(name='dashboard')
async def dashboard_command(ctx):
    embed = Embed(
        title='Dashboard Link',
        description='Click the button below to access the dashboard:',
        color=discord.Color.blue()
    )
    embed.add_field(name='Dashboard Link:', value='[Access Dashboard](https://your-dashboard-link-here)', inline=False)
    embed.set_footer(text='Enjoy managing your servers!')
    await ctx.send(embed=embed)

from discord.ext.commands import CommandOnCooldown
from discord.ext.commands import cooldown

@bot.event
@cooldown(1, 60)  # 1 message per 60 seconds (1 minute)
async def on_message(message):
    if message.author.bot:
        return  # Ignore messages from bots

    try:
        await bot.process_commands(message)  # Process the command

    except CommandOnCooldown as e:
        await message.channel.send(f"Please slow down your messages to prevent spam. Try again in {e.retry_after:.2f} seconds.")

from discord.ext import commands
from discord.ext.commands import has_permissions
from discord import Permissions

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick_command(ctx, member: discord.Member, *, reason=None):
    try:
        await member.kick(reason=reason)
        await ctx.send(f'{member.display_name} has been kicked from the server.')
    except discord.Forbidden:
        await ctx.send("I do not have permission to kick members.")
    except discord.HTTPException:
        await ctx.send("An error occurred while trying to kick the member.")
    except discord.InvalidArgument:
        await ctx.send("Invalid member provided.")




@bot.command(name='members')
async def members_command(ctx):
    members = ctx.guild.members
    member_list = "\n".join([member.name for member in members])
    await ctx.send(f"Members in this server:\n{member_list}")

@bot.command(name='serverinfo')
async def serverinfo_command(ctx):
    server = ctx.guild
    total_members = server.member_count
    server_name = server.name
    server_owner = server.owner
    verification_level = server.verification_level
    
    info_message = f"Server Name: {server_name}\nOwner: {server_owner}\nVerification Level: {verification_level}\nTotal Members: {total_members}"
    
    await ctx.send(info_message)

@bot.event
async def on_command(ctx):
    server_id = ctx.guild.id
    user_id = ctx.author.id
    command_used = ctx.message.content

    data = {
        'server_id': server_id,
        'user_id': user_id,
        'command_used': command_used
    }

    with open('commands.json', 'a') as file:
        json.dump(data, file)
        file.write('\n')


@app.route("/")
def home():
    if "discord_token" in session:
        user_info = get_user_info(session["discord_token"])

        # Access the user's email from the session
        user_email = session.get("user_email", "Email not available")

        servers = get_user_servers(session["discord_token"])

        # Save server data to a JSON file (Replace with your own logic)
        server_data = [
            {"id": server["id"], "name": server["name"], "email": user_email} 
            for server in servers
        ]

        with open("server_data.json", "w") as json_file:
            json.dump(server_data, json_file)

        # Generate HTML cards for each server
        server_cards = ""
        for server in servers:
            server_cards += f"""
                <div class="server-card">
                    <h3>{server["name"]}</h3>
                    <p>ID: {server["id"]}</p>
                    {get_manage_server_button(server["id"])}
                </div>
            """

        return f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Dashboard</title>
                <style>
                    .server-card {{
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        padding: 10px;
                        margin-bottom: 10px;
                    }}
                </style>
            </head>
            <body>
                <h1>Welcome, {user_info['username']}!</h1>
                <p>Your servers:</p>
                {server_cards}
                <a href="/logout">Logout</a>
            </body>
            </html>
        """
    else:
        return "<a href='/login'>Login with Discord</a>"

@app.route("/server_info/<server_id>")
def server_info_route(server_id):
    server_info = get_server_info(server_id)
    user_count = server_info.get("user_count", "User count not available")
    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Server Info</title>
        </head>
        <body>
            <h1>Server Info: {server_info['name']}</h1>
            <p>User Count: {total_members}</p>
            <button onclick="window.open('/manage_server_settings/{server_id}', '_blank')">Open Server Settings</button>
        </body>
        </html>
    """

def get_manage_server_button(server_id):
    if bot_is_in_server(server_id):
        return f"""
            <button id="manageServerBtn" onclick="openManageServerPage({server_id})">Manage Server</button>
            <script>
                function openManageServerPage(server_id) {{
                    window.open(`/manage_server/${server_id}`, '_blank');
                }}
            </script>
        """
    else:
        invite_url = generate_invite_url()
        return f'<a href="{invite_url}"><button>Invite Bot</button></a>'

def bot_is_in_server(server_id):
    guild = bot.get_guild(int(server_id))
    return guild is not None

def generate_invite_url():
    # Replace 'YOUR_CLIENT_ID' with your bot's client ID
    return f"https://discord.com/oauth2/authorize?client_id=1207763757715951646&scope=bot&permissions=8"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

# The

@app.route("/login")
def login():
    return redirect(f"{discord_api_url}/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=identify%20guilds%20email")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token = get_access_token(code)
    
    # Get user info, including email
    user_info = get_user_info(token)
    
    # Save email and token in the session
    session["discord_token"] = token
    session["user_email"] = user_info.get("email", None)

    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.pop("discord_token", None)
    return redirect(url_for("home"))

def get_access_token(code):
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "scope": "identify guilds"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(f"{discord_api_url}/oauth2/token", data=data, headers=headers)
    return response.json()["access_token"]

def get_user_info(token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "scope": "identify email"
    }
    response = requests.get(f"{discord_api_url}/users/@me", headers=headers, params=params)
    return response.json()

def get_user_servers(token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"{discord_api_url}/users/@me/guilds", headers=headers)
    servers = response.json()
    admin_servers = [server for server in servers if (server['permissions'] & 0x8) == 0x8]  # Check if the user has the Administrator permission
    return admin_servers

# ... (existing code)

@app.route("/manage_server/<server_id>")
def manage_server(server_id):
    server_info = get_server_info(server_id)
    
    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Manage Server</title>
        </head>
        <body>
            <h1>Manage Server: {server_info['name']}</h1>
            <p>Owner: {server_info['owner']}</p>
            <p>Total Members: {server_info['user_count']}</p>

            <!-- Link to logs page -->
            <a href="/logs/{server_id}"><button>View Logs</button></a>
        </body>
        </html>
    """

@app.route("/logs/<server_id>")
def logs_page(server_id):
    try:
        # Fetch logs from 'commands.json' based on the provided server_id
        with open('commands.json', 'r') as file:
            logs = [json.loads(line) for line in file if str(json.loads(line).get('server_id')).lstrip('$') == server_id]
        
        # Display logs
        logs_html = "<h2>Command Logs:</h2>"
        for log in logs:
            logs_html += f"<p>User {log['user_id']} used command: {log['command_used']}</p>"

        return logs_html

    except FileNotFoundError:
        return "Logs file not found."

# ... (remaining code)

def get_server_info(server_id):
    server_id = server_id.lstrip('$')  # Remove the '$' prefix
    
    try:
        guild = bot.get_guild(int(server_id))
    except ValueError:
        return {
            "name": "Invalid Server ID",
            "owner": "Owner not available",
            "user_count": "User count not available"
        }

    if not guild:
        return {
            "name": "Server not found",
            "owner": "Owner not available",
            "user_count": "User count not available"
        }
    
    server_info = {
        "name": guild.name,
        "owner": guild.owner,
        "user_count": guild.member_count
    }
    
    if hasattr(guild, 'region'):
        server_info['region'] = guild.region
    else:
        server_info['region'] = "Region not available"
    
    return server_info


if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor
    import threading

    # Define a function to run the Flask app
    def run_flask():
        app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Wait for a moment to ensure Flask has started
    import time
    time.sleep(2)

    # Start the Discord bot
    bot.run(bot_token)
