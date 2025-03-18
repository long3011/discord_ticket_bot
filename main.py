import discord
import json

MY_GUILD = discord.Object(id=1335651270681428102)
intents = discord.Intents.default()
intents.message_content = True

# Load bot token from a file
try:
    with open('token.txt') as f:
        bot_token = f.readline()
        f.close()
except FileNotFoundError:
    print('token.txt not found')
# Load list of saved server into variable
try:
    with open('server_id.json', 'r') as r:
        server_id = json.load(r)
        r.close()
except FileNotFoundError:
    print('server_id.txt not found')


#View object to save to the bot for persistent even after connection restart
class OpenTicket(discord.ui.View):
    #creating the view for initial buttons
    def __init__(self):
        super().__init__(timeout=None)
    #button for opening ticket
    @discord.ui.button(label='Open Ticket', style=discord.ButtonStyle.green, custom_id='ticket_bot:open')
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel=await open_ticket(interaction)
        await interaction.response.send_message(f"ticket opened, go to {channel.mention}", ephemeral=True)

#Ticket closing object, sent in every ticket channel creation to close the channel
class CloseTicket(discord.ui.View):
    #creating view for closing ticket
    def __init__(self):
        super().__init__(timeout=None)

    #button to grab the channel to close
    @discord.ui.button(label='Close Ticket', style=discord.ButtonStyle.red, custom_id='ticket_bot:open')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await close_ticket(interaction.channel)
        await interaction.response.send_message(f"ticket closed", ephemeral=True)



async def open_ticket(interaction:discord.Interaction):
    #overwrites permission members
    overwrites = {
        interaction.channel.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        #make sure all other members cant see the ticket
        interaction.user: discord.PermissionOverwrite(read_messages=True),
        #give the person opening the ticket permission to view
        interaction.channel.guild.me: discord.PermissionOverwrite(read_messages=True),
        #give the bot permission to view the ticket
    }

    #create the ticket channel and put it into channel var to send the message with the ticket closing button
    channel = await interaction.channel.category.create_text_channel(f'ticket-{len(interaction.channel.category.text_channels)}', overwrites=overwrites)
    view = CloseTicket()
    owner= await interaction.channel.category.guild.fetch_member(interaction.channel.category.guild.owner_id)
    #find owner member from id because guild.owner is broken
    await channel.send(f'{interaction.user.mention} ticket opened\n'
                       f'{owner.mention} will respond to you when '
                       f'available',view=view) #ping the person to respond to the ticket
    return channel

#closing the ticket channel
async def close_ticket(channel:discord.TextChannel):
    overwrites = {
        # revoke viewing from all member including person who opened the ticket
        channel.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        # give the bot permission to view the ticket
        channel.guild.me: discord.PermissionOverwrite(read_messages=True),
    }
    await channel.edit(overwrites=overwrites)

#Bot client object to store additional info and load info into the bot
class CustomClient(discord.Client):
    # initiate variables for the bot
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        global server_id
        # Syncs command tree to the guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        #load all saved ticket opening message with its id
        for i in server_id:
            self.add_view(OpenTicket(),message_id=int(server_id[i]))
        #load the rest of the view that doesnt have the id saved
        #only message that doesnt have id saved is the closing ticket message
        self.add_view(CloseTicket())
        await self.tree.sync(guild=MY_GUILD)

    async def on_ready(self):
        print('Bot is ready.')
    async def on_disconnect(self):
        print('Disconnected from Discord.')

client = CustomClient()

#setting up ticket from a given message
@client.tree.context_menu(name='Convert message to ticket')
async def ticket_setup(interaction:discord.Interaction, message:discord.Message):
    embed = discord.Embed(title='Open A Ticket!')
    #confirm no one but the owner can set up ticket opening
    if interaction.user.id != message.guild.owner_id:
        await interaction.response.send_message("You don't have permission to do that.", ephemeral=True)
        return
    #convert message content into embed
    if message.content:
        embed.description = message.content
    view=OpenTicket()
    await interaction.response.send_message("Ticket setup successful.\n"
                                            "If you want to make a new ticket message "
                                            "simply delete the old ticket message", ephemeral=True)
    #save ticket message into a file to "restart proof" it
    end_message=await message.channel.send(embed=embed, view=view)
    await message.delete()
    server_id[interaction.guild.id] = end_message.id
    with open("server_id.json", "r+") as outfile:
        data = json.load(outfile)
        data[str(interaction.guild.id)] = end_message.id
        outfile.seek(0)
        json.dump(data, outfile, indent=4)
        outfile.close()

@client.tree.context_menu(name='Refresh Ticket')
async def ticket_refresh(interaction:discord.Interaction, message:discord.Message):
    embed = message.embeds[0]
    #confirm no one but the owner can set up ticket opening
    if interaction.user.id != message.guild.owner_id:
        await interaction.response.send_message("You don't have permission to do that.", ephemeral=True)
        return

    view=OpenTicket()
    await interaction.response.send_message("Ticket Refreshed!", ephemeral=True)
    # save ticket message into a file to "restart proof" it
    end_message=await message.channel.send(embed=embed, view=view)
    await message.delete()
    server_id[str(interaction.guild.id)] = end_message.id
    with open("server_id.json", "r+") as outfile:
        data = json.load(outfile)
        data[interaction.guild.id] = end_message.id
        outfile.seek(0)
        json.dump(data, outfile, indent=4)
        outfile.close()

@client.tree.command()
async def help(interaction:discord.Interaction):
    """Give instruction on how to set up the ticket system"""
    #sending the help message with instruction
    embed = discord.Embed(title='Setting up Ticket')
    embed.description=(f"Start by writing a message that you want the bot to display for the Ticket\n"
                       f"Then right click the message, in app and convert message to ticket\n"
                       f"The bot should work and will create ticket channels in the same category where the message is in\n"
                       f"If the Ticket break, simply refresh the old ticket message")
    await interaction.response.send_message(embed=embed, ephemeral=True)

try:
    client.run(bot_token)
except RuntimeError:
    print('Token expired')