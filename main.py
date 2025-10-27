import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import asyncio

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

warnings_db = {}
mutes_db = {}
tickets_db = {}

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

@bot.tree.command(name="rename", description="Renommer un ticket")
@app_commands.describe(nom="Le nouveau nom du ticket")
async def rename_ticket(interaction: discord.Interaction, nom: str):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ Cette commande ne peut être utilisée que dans un ticket.", ephemeral=True)
        return
    
    clean_name = "".join(c for c in nom if c.isalnum() or c in ('-', '_')).lower()
    await interaction.channel.edit(name=f"ticket-{clean_name}")
    await interaction.response.send_message(f"✅ Ticket renommé en **ticket-{clean_name}**")

@bot.tree.command(name="add", description="Ajouter un membre au ticket")
@app_commands.describe(membre="Le membre à ajouter")
async def add_to_ticket(interaction: discord.Interaction, membre: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ Cette commande ne peut être utilisée que dans un ticket.", ephemeral=True)
        return
    
    await interaction.channel.set_permissions(membre, read_messages=True, send_messages=True)
    
    embed = discord.Embed(
        description=f"✅ {membre.mention} a été ajouté au ticket par {interaction.user.mention}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="remove", description="Retirer un membre du ticket")
@app_commands.describe(membre="Le membre à retirer")
async def remove_from_ticket(interaction: discord.Interaction, membre: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ Cette commande ne peut être utilisée que dans un ticket.", ephemeral=True)
        return
    
    await interaction.channel.set_permissions(membre, overwrite=None)
    
    embed = discord.Embed(
        description=f"✅ {membre.mention} a été retiré du ticket par {interaction.user.mention}",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="reserv-ticket", description="Réserver le ticket aux opérateurs")
async def reserv_ticket(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Seuls ceux qui ont la permission de ban peuvent utiliser cette commande.", ephemeral=True)
        return
    
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ Cette commande ne peut être utilisée que dans un ticket.", ephemeral=True)
        return
    
    guild = interaction.guild
    operator_role = guild.get_role(CONFIG["OPERATOR_ROLE_ID"])
    
    channel_id = str(interaction.channel.id)
    ticket_data = tickets_db.get(channel_id)
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        operator_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    
    if ticket_data:
        creator = guild.get_member(int(ticket_data["user_id"]))
        if creator:
            overwrites[creator] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    
    await interaction.channel.edit(overwrites=overwrites)
    
    embed = discord.Embed(
        title="🔒 Ticket Réservé",
        description=f"Ce ticket a été réservé aux Opérateurs par {interaction.user.mention}",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    await interaction.response.send_message(embed=embed)

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

@bot.tree.command(name="rank", description="Promouvoir un joueur à un grade")
@app_commands.describe(joueur="Le joueur à promouvoir", grade="Le nom du grade")
async def rank(interaction: discord.Interaction, joueur: discord.Member, grade: str):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    announce_role = interaction.guild.get_role(CONFIG["ANNOUNCE_ROLE_ID"])
    
    embed = discord.Embed(
        title="⭐ Nouvelle Promotion !",
        description=f"Félicitations à {joueur.mention} qui vient d'être promu !",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    embed.add_field(name="👤 Joueur", value=joueur.mention, inline=True)
    embed.add_field(name="🎖️ Nouveau Grade", value=grade, inline=True)
    embed.add_field(name="👨‍💼 Promu par", value=interaction.user.mention, inline=True)
    embed.set_thumbnail(url=joueur.display_avatar.url)
    embed.set_footer(text="Bonne continuation dans tes nouvelles fonctions !")
    
    await interaction.response.send_message(
        content=f"{announce_role.mention}",
        embed=embed
    )

@bot.tree.command(name="derank", description="Rétrograder un joueur")
@app_commands.describe(joueur="Le joueur à rétrograder")
async def derank(interaction: discord.Interaction, joueur: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        return
    
    announce_role = interaction.guild.get_role(CONFIG["ANNOUNCE_ROLE_ID"])
    
    embed = discord.Embed(
        title="📉 Rétrogradation",
        description=f"{joueur.mention} a été rétrogradé.",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.add_field(name="👤 Joueur", value=joueur.mention, inline=True)
    embed.add_field(name="👨‍💼 Rétrogradé par", value=interaction.user.mention, inline=True)
    embed.set_thumbnail(url=joueur.display_avatar.url)
    
    await interaction.response.send_message(
        content=f"{announce_role.mention}",
        embed=embed
    )

@bot.tree.command(name="botinfo", description="Informations sur le bot")
async def botinfo(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌙 LunaBot - Informations",
        description="Bot de modération et gestion de tickets",
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )
    embed.add_field(name="👥 Serveurs", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="📊 Membres", value=str(len(bot.users)), inline=True)
    embed.add_field(name="🏓 Latence", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="⚠️ Warns actifs", value=str(len(warnings_db)), inline=True)
    embed.add_field(name="🎫 Tickets ouverts", value=str(len(tickets_db)), inline=True)
    embed.set_footer(text="Développé pour ton serveur")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Liste des commandes disponibles")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Commandes de LunaBot",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🛡️ Modération",
        value="`/warn` - Avertir un membre\n"
              "`/warnings` - Voir les warns\n"
              "`/clearwarns` - Effacer les warns\n"
              "`/mute` - Rendre muet\n"
              "`/unmute` - Retirer le mute\n"
              "`/kick` - Expulser un membre\n"
              "`/ban` - Bannir un membre\n"
              "`/unban` - Débannir un utilisateur",
        inline=False
    )
    
    embed.add_field(
        name="🎫 Tickets",
        value="`/ticket-panel` - Créer le panel\n"
              "`/rename` - Renommer le ticket\n"
              "`/add` - Ajouter un membre\n"
              "`/remove` - Retirer un membre\n"
              "`/reserv-ticket` - Réserver aux ops",
        inline=False
    )
    
    embed.add_field(
        name="🎖️ Grades",
        value="`/rank` - Promouvoir un joueur\n"
              "`/derank` - Rétrograder un joueur",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ Informations",
        value="`/botinfo` - Infos sur le bot\n"
              "`/help` - Cette commande\n"
              "`/ping` - Latence du bot",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ping", description="Vérifier la latence du bot")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    
    if latency < 100:
        color = discord.Color.green()
        status = "Excellent"
    elif latency < 200:
        color = discord.Color.orange()
        status = "Correct"
    else:
        color = discord.Color.red()
        status = "Lent"
    
    embed = discord.Embed(
        title="🏓 Pong !",
        description=f"**Latence:** {latency}ms\n**Status:** {status}",
        color=color
    )
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"✅ {bot.user.name} est connecté !")
    print(f"📊 ID: {bot.user.id}")
    print(f"🌐 Serveurs: {len(bot.guilds)}")
    print(f"👥 Utilisateurs: {len(bot.users)}")
    print("=" * 50)
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes synchronisées")
    except Exception as e:
        print(f"❌ Erreur de synchronisation: {e}")
    
    bot.add_view(TicketView())
    bot.add_view(TicketButton())
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="le serveur 🌙"
        ),
        status=discord.Status.online
    )
    print("✅ Bot prêt à l'utilisation !")
    print("=" * 50)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"❌ Erreur: {error}")


from flask import Flask
import threading
import os


app = Flask('')

@app.route('/')
def home():
    return "✅ LunaBot est en ligne !"

def run():
    app.run(host='0.0.0.0', port=8080)


threading.Thread(target=run).start()

print("🚀 Démarrage de LunaBot...")

TOKEN = os.getenv("DISCORD_TOKEN")  

if not TOKEN:
    print("❌ ERREUR : Token Discord non trouvé !")
    print("⚠️  Ajoute une variable d'environnement DISCORD_TOKEN sur Render.com")
else:
    try:
        bot.run(TOKEN)
    except Exception as e:

        print(f"❌ Erreur de démarrage: {e}")
