import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import asyncio
import os
import threading
from flask import Flask

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

CONFIG = {
    "GUILD_ID": 1409483536620064788,
    "WELCOME_CHANNEL_ID": 1409790891090116668,
    "TICKET_CATEGORY_ID": 1409492768388157500,
    "TRANSCRIPT_CHANNEL_ID": 1410130626614394980,
    "MODERATOR_ROLE_ID": 1409484870106873988,
    "GUIDE_ROLE_ID": 1416290757370708018,
    "OPERATOR_ROLE_ID": 1409484767614734346,
    "ANNOUNCE_ROLE_ID": 1409894288925397135,
}

# Structure des équipes (stockage en mémoire)
TEAMS = {
    'F': {
        'name': 'Fondateur',
        'description': 'Fonde le serveur, finance le serveur !',
        'members': []
    },
    'G': {
        'name': 'Gérant',
        'description': 'Il gère tout ce qui est externe au serveur',
        'members': []
    },
    'R': {
        'name': 'Équipe Réponsable',
        'description': "Il s'occupe de tout le staff en général et du serveur",
        'members': []
    },
    'C': {
        'name': 'Community Manager',
        'description': 'Il gère la communication du serveur',
        'members': []
    },
    'A': {
        'name': 'Administrateur',
        'description': 'Il gère tout ce qui est nouveauté, staff, etc.',
        'members': []
    },
    'E': {
        'name': 'Équipe Création',
        'description': 'Il contribue au développement du serveur',
        'members': []
    },
    'S': {
        'name': 'Super Modérateur',
        'description': "Il aide l'équipe réponsable dans leur travail",
        'members': []
    },
    'M': {
        'name': 'Équipe Modérations',
        'description': "Il modère le tchat, s'occupe de sanctionner si nécessaire",
        'members': []
    },
    'GU': {
        'name': 'Guide',
        'description': 'Il guide les joueurs en répondant aux questions',
        'members': []
    },
    'B': {
        'name': 'Builders',
        'description': 'Il contribue au build du serveur',
        'members': []
    }
}

warnings_db = {}
mutes_db = {}
tickets_db = {}
team_messages = {}

# Créer l'embed de l'équipe
def create_team_embed():
    embed = discord.Embed(
        title='📋 Composition de l\'équipe',
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    for key, team in TEAMS.items():
        field_value = f"-# {team['description']}\n"
        
        if team['members']:
            field_value += '\n'.join([f"- <@{member_id}>" for member_id in team['members']])
        else:
            field_value += '*Aucun membre*'
        
        embed.add_field(
            name=f"{key} - {team['name']}",
            value=field_value,
            inline=False
        )
    
    return embed

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(CONFIG["WELCOME_CHANNEL_ID"])
    if channel:
        embed = discord.Embed(
            title="🌙 Bienvenue sur le serveur !",
            description=f"Hey {member.mention}, bienvenue parmi nous !\n\n"
                       f"Tu es le **{member.guild.member_count}ème** membre du serveur.\n"
                       f"N'oublie pas de lire les règles et de passer un bon moment !",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await channel.send(embed=embed)

# ========== COMMANDES TEAM ==========

@bot.tree.command(name='teammessage', description='Affiche l\'embed de l\'équipe')
@app_commands.checks.has_permissions(ban_members=True)
async def teammessage(interaction: discord.Interaction):
    embed = create_team_embed()
    await interaction.response.send_message(embed=embed)
    
    message = await interaction.original_response()
    team_messages[interaction.guild_id] = {
        'channel_id': interaction.channel_id,
        'message_id': message.id
    }

team_group = app_commands.Group(name='team', description='Gérer les membres de l\'équipe')

@team_group.command(name='add', description='Ajouter un membre à une équipe')
@app_commands.describe(
    joueur='Le joueur à ajouter',
    team='L\'équipe'
)
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.choices(team=[
    app_commands.Choice(name='F - Fondateur', value='F'),
    app_commands.Choice(name='G - Gérant', value='G'),
    app_commands.Choice(name='R - Équipe Réponsable', value='R'),
    app_commands.Choice(name='C - Community Manager', value='C'),
    app_commands.Choice(name='A - Administrateur', value='A'),
    app_commands.Choice(name='E - Équipe Création', value='E'),
    app_commands.Choice(name='S - Super Modérateur', value='S'),
    app_commands.Choice(name='M - Équipe Modérations', value='M'),
    app_commands.Choice(name='GU - Guide', value='GU'),
    app_commands.Choice(name='B - Builders', value='B')
])
async def team_add(interaction: discord.Interaction, joueur: discord.Member, team: str):
    if team not in TEAMS:
        await interaction.response.send_message('❌ Équipe invalide !', ephemeral=True)
        return
    
    if joueur.id in TEAMS[team]['members']:
        await interaction.response.send_message(
            f"❌ {joueur.mention} est déjà dans l'équipe {TEAMS[team]['name']} !",
            ephemeral=True
        )
        return
    
    TEAMS[team]['members'].append(joueur.id)
    
    await interaction.response.send_message(
        f"✅ {joueur.mention} a été ajouté à l'équipe {TEAMS[team]['name']} !",
        ephemeral=True
    )
    
    if interaction.guild_id in team_messages:
        try:
            channel = bot.get_channel(team_messages[interaction.guild_id]['channel_id'])
            message = await channel.fetch_message(team_messages[interaction.guild_id]['message_id'])
            new_embed = create_team_embed()
            await message.edit(embed=new_embed)
        except Exception as e:
            print(f'Erreur lors de la mise à jour du message: {e}')

@team_group.command(name='remove', description='Retirer un membre d\'une équipe')
@app_commands.describe(
    joueur='Le joueur à retirer',
    team='L\'équipe'
)
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.choices(team=[
    app_commands.Choice(name='F - Fondateur', value='F'),
    app_commands.Choice(name='G - Gérant', value='G'),
    app_commands.Choice(name='R - Équipe Réponsable', value='R'),
    app_commands.Choice(name='C - Community Manager', value='C'),
    app_commands.Choice(name='A - Administrateur', value='A'),
    app_commands.Choice(name='E - Équipe Création', value='E'),
    app_commands.Choice(name='S - Super Modérateur', value='S'),
    app_commands.Choice(name='M - Équipe Modérations', value='M'),
    app_commands.Choice(name='GU - Guide', value='GU'),
    app_commands.Choice(name='B - Builders', value='B')
])
async def team_remove(interaction: discord.Interaction, joueur: discord.Member, team: str):
    if team not in TEAMS:
        await interaction.response.send_message('❌ Équipe invalide !', ephemeral=True)
        return
    
    if joueur.id not in TEAMS[team]['members']:
        await interaction.response.send_message(
            f"❌ {joueur.mention} n'est pas dans l'équipe {TEAMS[team]['name']} !",
            ephemeral=True
        )
        return
    
    TEAMS[team]['members'].remove(joueur.id)
    
    await interaction.response.send_message(
        f"✅ {joueur.mention} a été retiré de l'équipe {TEAMS[team]['name']} !",
        ephemeral=True
    )
    
    if interaction.guild_id in team_messages:
        try:
            channel = bot.get_channel(team_messages[interaction.guild_id]['channel_id'])
            message = await channel.fetch_message(team_messages[interaction.guild_id]['message_id'])
            new_embed = create_team_embed()
            await message.edit(embed=new_embed)
        except Exception as e:
            print(f'Erreur lors de la mise à jour du message: {e}')

bot.tree.add_command(team_group)

# ========== COMMANDES MODERATION ==========

@bot.tree.command(name="warn", description="Avertir un membre")
@app_commands.describe(membre="Le membre à avertir", raison="La raison de l'avertissement")
async def warn(interaction: discord.Interaction, membre: discord.Member, raison: str):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    user_id = str(membre.id)
    if user_id not in warnings_db:
        warnings_db[user_id] = []
    
    warn_data = {
        "moderator": str(interaction.user.id),
        "moderator_name": interaction.user.display_name,
        "reason": raison,
        "timestamp": datetime.now().isoformat()
    }
    warnings_db[user_id].append(warn_data)
    
    embed = discord.Embed(
        title="⚠️ Avertissement",
        description=f"{membre.mention} a reçu un avertissement.",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    embed.add_field(name="Raison", value=raison, inline=False)
    embed.add_field(name="Modérateur", value=interaction.user.mention, inline=True)
    embed.add_field(name="Total d'avertissements", value=str(len(warnings_db[user_id])), inline=True)
    embed.set_footer(text=f"ID: {membre.id}")
    
    await interaction.response.send_message(embed=embed)
    
    try:
        dm_embed = discord.Embed(
            title="⚠️ Tu as reçu un avertissement",
            description=f"**Serveur:** {interaction.guild.name}\n**Raison:** {raison}",
            color=discord.Color.orange()
        )
        await membre.send(embed=dm_embed)
    except:
        pass

@bot.tree.command(name="warnings", description="Voir les avertissements d'un membre")
@app_commands.describe(membre="Le membre dont voir les avertissements")
async def warnings_cmd(interaction: discord.Interaction, membre: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    user_id = str(membre.id)
    user_warnings = warnings_db.get(user_id, [])
    
    embed = discord.Embed(
        title=f"📋 Avertissements de {membre.display_name}",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    if not user_warnings:
        embed.description = "Aucun avertissement."
    else:
        for i, warn in enumerate(user_warnings, 1):
            embed.add_field(
                name=f"Warn #{i}",
                value=f"**Raison:** {warn['reason']}\n**Par:** {warn['moderator_name']}\n**Date:** {warn['timestamp'][:10]}",
                inline=False
            )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clearwarns", description="Effacer les avertissements d'un membre")
@app_commands.describe(membre="Le membre dont effacer les warns")
async def clearwarns(interaction: discord.Interaction, membre: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    user_id = str(membre.id)
    if user_id in warnings_db:
        count = len(warnings_db[user_id])
        warnings_db[user_id] = []
        await interaction.response.send_message(f"✅ {count} avertissement(s) effacé(s) pour {membre.mention}")
    else:
        await interaction.response.send_message(f"{membre.mention} n'a aucun avertissement.", ephemeral=True)

@bot.tree.command(name="mute", description="Rendre muet un membre")
@app_commands.describe(membre="Le membre à mute", duree="Durée en minutes", raison="La raison du mute")
async def mute(interaction: discord.Interaction, membre: discord.Member, duree: int, raison: str):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    try:
        await membre.timeout(discord.utils.utcnow() + discord.timedelta(minutes=duree), reason=raison)
        
        user_id = str(membre.id)
        mutes_db[user_id] = {
            "moderator": str(interaction.user.id),
            "moderator_name": interaction.user.display_name,
            "reason": raison,
            "duration": duree,
            "timestamp": datetime.now().isoformat()
        }
        
        embed = discord.Embed(
            title="🔇 Membre Mute",
            description=f"{membre.mention} a été rendu muet.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Raison", value=raison, inline=False)
        embed.add_field(name="Durée", value=f"{duree} minutes", inline=True)
        embed.add_field(name="Modérateur", value=interaction.user.mention, inline=True)
        
        await interaction.response.send_message(embed=embed)
        
        try:
            dm_embed = discord.Embed(
                title="🔇 Tu as été rendu muet",
                description=f"**Serveur:** {interaction.guild.name}\n**Raison:** {raison}\n**Durée:** {duree} minutes",
                color=discord.Color.red()
            )
            await membre.send(embed=dm_embed)
        except:
            pass
            
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)

@bot.tree.command(name="unmute", description="Rendre la parole à un membre")
@app_commands.describe(membre="Le membre à unmute")
async def unmute(interaction: discord.Interaction, membre: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    try:
        await membre.timeout(None)
        embed = discord.Embed(
            title="🔊 Membre Unmute",
            description=f"{membre.mention} peut à nouveau parler.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)

@bot.tree.command(name="kick", description="Expulser un membre du serveur")
@app_commands.describe(membre="Le membre à expulser", raison="La raison de l'expulsion")
async def kick(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    if membre.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Tu ne peux pas expulser ce membre (rôle supérieur ou égal).", ephemeral=True)
        return
    
    try:
        await membre.kick(reason=raison)
        
        embed = discord.Embed(
            title="👢 Membre Expulsé",
            description=f"{membre.mention} a été expulsé du serveur.",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Raison", value=raison, inline=False)
        embed.add_field(name="Modérateur", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"ID: {membre.id}")
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)

@bot.tree.command(name="ban", description="Bannir un membre du serveur")
@app_commands.describe(membre="Le membre à bannir", raison="La raison du bannissement")
async def ban(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    if membre.top_role >= interaction.user.top_role:
        await interaction.response.send_message("❌ Tu ne peux pas bannir ce membre (rôle supérieur ou égal).", ephemeral=True)
        return
    
    try:
        await membre.ban(reason=raison, delete_message_days=1)
        
        embed = discord.Embed(
            title="🔨 Membre Banni",
            description=f"{membre.mention} a été banni du serveur.",
            color=discord.Color.dark_red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Raison", value=raison, inline=False)
        embed.add_field(name="Modérateur", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"ID: {membre.id}")
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)

@bot.tree.command(name="unban", description="Débannir un utilisateur")
@app_commands.describe(user_id="L'ID de l'utilisateur à débannir")
async def unban(interaction: discord.Interaction, user_id: str):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        
        embed = discord.Embed(
            title="✅ Membre Débanni",
            description=f"{user.mention} ({user.name}) a été débanni.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Modérateur", value=interaction.user.mention, inline=True)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)

# ========== SYSTÈME DE TICKETS ==========

class TicketModal(discord.ui.Modal, title="Créer un Ticket"):
    pseudo_ig = discord.ui.TextInput(
        label="Pseudo In-Game",
        placeholder="Ton pseudo dans le jeu...",
        required=True,
        max_length=50
    )
    
    faction = discord.ui.TextInput(
        label="Faction",
        placeholder="Ta faction...",
        required=True,
        max_length=50
    )
    
    explication = discord.ui.TextInput(
        label="Explication",
        placeholder="Explique ta demande en détail...",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        category = guild.get_channel(CONFIG["TICKET_CATEGORY_ID"])
        
        ticket_number = len([c for c in category.channels if c.name.startswith("ticket-")]) + 1
        channel_name = f"ticket-{ticket_number}"
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(CONFIG["MODERATOR_ROLE_ID"]): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(CONFIG["GUIDE_ROLE_ID"]): discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        
        ticket_channel = await category.create_text_channel(
            name=channel_name,
            overwrites=overwrites
        )
        
        tickets_db[str(ticket_channel.id)] = {
            "user_id": str(interaction.user.id),
            "user_name": interaction.user.display_name,
            "pseudo_ig": self.pseudo_ig.value,
            "faction": self.faction.value,
            "explication": self.explication.value,
            "created_at": datetime.now().isoformat(),
            "claimed_by": None,
            "claimed_by_name": None
        }
        
        embed = discord.Embed(
            title=f"🎫 Ticket #{ticket_number}",
            description=f"Ticket créé par {interaction.user.mention}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Pseudo IG", value=self.pseudo_ig.value, inline=True)
        embed.add_field(name="🏴 Faction", value=self.faction.value, inline=True)
        embed.add_field(name="📝 Explication", value=self.explication.value, inline=False)
        embed.set_footer(text=f"User ID: {interaction.user.id}")
        
        view = TicketView()
        
        mod_role = guild.get_role(CONFIG["MODERATOR_ROLE_ID"])
        guide_role = guild.get_role(CONFIG["GUIDE_ROLE_ID"])
        
        await ticket_channel.send(
            f"{mod_role.mention} {guide_role.mention}",
            embed=embed,
            view=view
        )
        
        await interaction.followup.send(
            f"✅ Ton ticket a été créé: {ticket_channel.mention}",
            ephemeral=True
        )

class ConfirmCloseView(discord.ui.View):
    def __init__(self, original_interaction):
        super().__init__(timeout=30)
        self.original_interaction = original_interaction
        self.value = None
    
    @discord.ui.button(label="Oui, fermer", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.original_interaction.user.id:
            await interaction.response.send_message("❌ Seul celui qui a cliqué sur fermer peut confirmer.", ephemeral=True)
            return
        
        self.value = True
        self.stop()
        
        await interaction.response.edit_message(content="⏳ Fermeture du ticket dans 5 secondes...", view=None, embed=None)
        await asyncio.sleep(5)
        
        channel_id = str(interaction.channel.id)
        if channel_id in tickets_db:
            del tickets_db[channel_id]
        
        await interaction.channel.delete()
    
    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.original_interaction.user.id:
            await interaction.response.send_message("❌ Seul celui qui a cliqué sur fermer peut annuler.", ephemeral=True)
            return
        
        self.value = False
        self.stop()
        await interaction.response.edit_message(content="✅ Fermeture annulée.", view=None, embed=None)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Réclamer", style=discord.ButtonStyle.green, custom_id="claim_ticket")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_id = str(interaction.channel.id)
        if channel_id in tickets_db:
            if tickets_db[channel_id]["claimed_by"]:
                await interaction.response.send_message("❌ Ce ticket a déjà été réclamé.", ephemeral=True)
                return
            
            tickets_db[channel_id]["claimed_by"] = str(interaction.user.id)
            tickets_db[channel_id]["claimed_by_name"] = interaction.user.display_name
            
            embed = discord.Embed(
                title="✅ Ticket Réclamé",
                description=f"{interaction.user.mention} a pris en charge ce ticket.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed)
    
    @discord.ui.button(label="Fermer", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚠️ Confirmation",
            description="Es-tu sûr de vouloir fermer ce ticket ?\n\n**Cette action est irréversible !**",
            color=discord.Color.orange()
        )
        
        view = ConfirmCloseView(interaction)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Ouvrir un Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())

@bot.tree.command(name="ticket-panel", description="Créer le panel de tickets")
async def ticket_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Seuls les administrateurs peuvent utiliser cette commande.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🎫 Système de Tickets",
        description="Clique sur le bouton ci-dessous pour ouvrir un ticket.\n\n"
                   "**Quand utiliser les tickets ?**\n"
                   "• Questions sur le serveur\n"
                   "• Signaler un problème\n"
                   "• Demande d'aide\n"
                   "• Autre demande",
        color=discord.Color.purple()
    )
    embed.set_footer(text="LunaBot • Système de Tickets")
    
    view = TicketButton()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ Panel de tickets créé !", ephemeral=True)

    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ Cette commande ne peut être utilisée que dans un ticket.", ephemeral=True)
        return

    try:
        await interaction.channel.edit(name=f"ticket-{nom}")
        await interaction.response.send_message(f"✅ Ticket renommé en **ticket-{nom}**", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur lors du renommage : {e}", ephemeral=True)

# ========== KEEP ALIVE SERVEUR FLASK (pour Render) ==========

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ LunaBot est en ligne !"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    thread = threading.Thread(target=run_web)
    thread.start()

# ========== ÉVÈNEMENT DE DÉMARRAGE ==========

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=CONFIG["GUILD_ID"]))
        print(f"🔁 {len(synced)} commandes synchronisées avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation des commandes : {e}")

# ========== LANCEMENT DU BOT ==========

if __name__ == "__main__":
    keep_alive()  # Garde le bot actif sur Render
    TOKEN = os.getenv("DISCORD_TOKEN")  # Ton token doit être dans les variables d'environnement Render
    bot.run(TOKEN)
