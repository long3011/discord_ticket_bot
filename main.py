import discord

MY_GUILD = discord.Object(id=1335651270681428102)
intents = discord.Intents.default()
intents.message_content = True

# Load bot token from a file
try:
    with open('token.txt') as f:
        bot_token = f.readline()
        f.close()
except FileNotFoundError:
    print('TOKEN.txt not found')

class CustomClient(discord.Client):
    # initiate variables for the bot
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        # Syncs command tree to the guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


class OpenTicket(discord.ui.View):
    #creating the view for initial buttons
    def __init__(self,category):
        super().__init__()
        self.category = category

    @discord.ui.button(label='Open Ticket', style=discord.ButtonStyle.green)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel=await open_ticket(interaction,self.category)
        await interaction.response.send_message(f"ticket opened, go to {channel.mention}", ephemeral=True)
class CloseTicket(discord.ui.View):
    #creating view for closing ticket
    def __init__(self,user:discord.Member,channel:discord.TextChannel):
        super().__init__()
        self.user = user
        self.channel = channel

    @discord.ui.button(label='Close Ticket', style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await close_ticket(self.user,self.channel)
        await interaction.response.send_message(f"ticket closed", ephemeral=True)


client = CustomClient()

async def open_ticket(interaction:discord.Interaction, category:discord.CategoryChannel):
    #overwrites permission members
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        #make sure all other members cant see the ticket
        interaction.user: discord.PermissionOverwrite(read_messages=True),
        #give the person opening the ticket permission to view
        category.guild.me: discord.PermissionOverwrite(read_messages=True),
        #give the bot permission to view the ticket
    }

    channel = await category.create_text_channel(f'ticket-{len(category.text_channels)}', overwrites=overwrites)
    view = CloseTicket(interaction.user, channel)
    owner= await category.guild.fetch_member(category.guild.owner_id)
    #find owner member from id because guild.owner is broken
    await channel.send(f'{interaction.user.mention} ticket opened\n'
                       f'{owner.mention} will respond to you when '
                       f'available',view=view) #ping the person to respond to the ticket
    return channel

async def close_ticket(user:discord.Member, channel:discord.TextChannel):
    overwrites = {
        #revoke viewing message from user opening the ticket
        user: discord.PermissionOverwrite(read_messages=False),
        # make sure all other members cant see the ticket
        channel.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        # give the bot permission to view the ticket
        channel.guild.me: discord.PermissionOverwrite(read_messages=True),
    }
    await channel.edit(overwrites=overwrites)


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
    view=OpenTicket(message.channel.category)
    await interaction.response.send_message("Ticket setup successful.\n"
                                            "If you want to make a new ticket message "
                                            "simply delete the old ticket message", ephemeral=True)
    await message.channel.send(embed=embed, view=view)
    await message.delete()

@client.tree.command()
async def help(interaction:discord.Interaction):
    """Give instruction on how to set up the ticket system"""
    embed = discord.Embed(title='Setting up Ticket')
    embed.description=(f"Start by writing a message that you want the bot to display for the Ticket\n"
                       f"Then right click the message, in app and convert message to ticket\n"
                       f"The bot should work and will create ticket channels in the same category where the message is in")
    await interaction.response.send_message(embed=embed, ephemeral=True)

try:
    client.run(bot_token)
except RuntimeError:
    print('Token expired')