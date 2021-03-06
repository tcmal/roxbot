import time
import discord
import datetime
from discord.ext import commands
from discord.ext.commands import bot

import roxbot
from roxbot import guild_settings as gs


def _is_admin_or_mod(message):
	if message.author.id == roxbot.owner:
		return True
	perm_roles = gs.get(message.channel.guild).perm_roles
	for role in message.author.roles:
		if role.id in perm_roles.get("admin") or role.id in perm_roles.get("mod"):
			return True
	return False


class Admin():
	"""
	Admin Commands for those admins
	"""
	def __init__(self, bot_client):
		self.bot = bot_client
		self.slow_mode = False
		self.slow_mode_channels = {}
		self.users = {}

	async def on_message(self, message):
		# Slow Mode Code
		channel = message.channel
		author = message.author

		if not author == self.bot.user:
			if (self.slow_mode and channel.id in self.slow_mode_channels) and not _is_admin_or_mod(message):
				if author.id not in self.users[channel.id]:
					# If user hasn't sent a message in this channel after slow mode was turned on
					self.users[channel.id][author.id] = message.created_at
				else:
					# Else, check when their last message was and if time is smaller than the timer, delete the message.
					timer = datetime.timedelta(seconds=self.slow_mode_channels[channel.id])
					if message.created_at - self.users[channel.id][author.id] < timer:
						await message.delete()
					else:
						self.users[message.channel.id][author.id] = message.created_at
			else:
				pass

	@roxbot.checks.is_admin_or_mod()
	@commands.guild_only()
	@commands.bot_has_permissions(manage_messages=True)
	@bot.command()
	async def slowmode(self, ctx, seconds):
		"""Puts the current channel in slowmode.
		Usage:
			;slowmode [time/"off"]
			seconds =  number of seconds for the cooldown between messages a user has.
			off = turns off slowmode for this channel"""
		if seconds == "off" and self.slow_mode:  # Turn Slow Mode off
			self.slow_mode = False
			self.slow_mode_channels.pop(ctx.channel.id)
			self.users.pop(ctx.channel.id)
			return await ctx.send("Slowmode off")

		elif seconds.isdigit() and not self.slow_mode:  # Turn Slow Mode On
			self.users[ctx.channel.id] = {}
			self.slow_mode_channels[ctx.channel.id] = int(seconds)
			self.slow_mode = True
			return await ctx.send("Slowmode on :snail: ({} seconds)".format(seconds))

		elif seconds.isdigit and self.slow_mode:  # Change value of Slow Mode timer
			self.slow_mode_channels[ctx.channel.id] = int(seconds)
			return await ctx.send("Slowmode set to :snail: ({} seconds)".format(seconds))

		else:
			pass

	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True, read_message_history=True)
	@commands.cooldown(1, 5)
	@bot.command()
	async def purge(self, ctx, limit=0, *, author: roxbot.converters.UserConverter=None):
		"""Purges messages from the text channel.
		Limit = Limit of messages to be deleted
		Author (optional) =  If given, roxbot will selectively only delete this user's messages."""
		# TODO: To sort out the limit == how many to delete for the author, and not just a limit.
		if author:
			predicate = lambda message: message.author.id == author.id and message.id != ctx.message.id
		else:
			predicate = lambda message: message.id != ctx.message.id
		messages = await ctx.channel.purge(limit=limit, check=predicate)
		return await ctx.send("{} message(s) purged from chat.".format(len(messages)))

	@roxbot.checks.is_admin_or_mod()
	@commands.group(case_insensitive=True)
	async def warn(self, ctx):
		"""Group of commands handling warnings"""
		if ctx.invoked_subcommand is None:
			return await ctx.send('Missing Argument')

	@warn.command()
	async def add(self, ctx, user: discord.User=None, *, warning=""):
		"""Adds a warning to a user."""
		# Warning in the settings is a dictionary of user ids. The user ids are equal to a list of dictionaries.
		settings = gs.get(ctx.guild)
		warning_limit = 2
		warning_dict = {
			"warned-by": ctx.author.id,
			"date": time.time(),
			"warning": warning
		}
		user_id = str(user.id)

		if user_id not in settings.warnings:
			settings.warnings[user_id] = []

		settings.warnings[user_id].append(warning_dict)
		settings.update(settings.warnings, "warnings")

		amount_warnings = len(settings.warnings[user_id])
		if amount_warnings > warning_limit:
			await ctx.author.send("{} has been reported {} time(s). This is a reminder that this is over the set limit of {}.".format(
					str(user), amount_warnings, warning_limit))

		return await ctx.send("Reported {}.".format(str(user)))

	@warn.command()
	async def list(self, ctx, *, user: roxbot.converters.UserConverter=None):
		"""Lists all or just the warnings for one user."""
		settings = gs.get(ctx.guild)

		if user is None:
			output = ""
			for member in settings.warnings:
				# Remove users with no warning here instead of remove cause im lazy
				if not settings.warnings[member]:
					settings.warnings.pop(member)
				else:
					member_obj = discord.utils.get(ctx.guild.members, id=int(member))
					if member_obj:
						output += "{}: {} Warning(s)\n".format(str(member_obj), len(
							settings.warnings[member]))
					else:
						output += "{}: {} Warning(s)\n".format(member, len(
							settings.warnings[member]))
			if not output:
				return await ctx.send("No warnings on record.")
			return await ctx.send(output)

		user_id = str(user.id)

		if not settings.warnings.get(user_id):
			return await ctx.send("This user doesn't have any warning on record.")

		if not settings.warnings[user_id]:
			settings.warnings.pop(user_id)
			settings.update(settings.warnings, "warnings")
		
		em = discord.Embed(title="Warnings for {}".format(str(user)), colour=roxbot.EmbedColours.pink)
		em.set_thumbnail(url=user.avatar_url)
		x = 1
		userlist = settings.warnings[user_id]
		for warning in userlist:
			try:
				warned_by = str(await self.bot.get_user_info(warning["warned-by"]))
			except discord.ext.commands.CommandInvokeError:
				warned_by = warning["warned-by"]
			date = datetime.datetime.fromtimestamp(warning["date"]).strftime('%c')
			warn_reason = warning["warning"]
			em.add_field(name="Warning %s" % x, value="Warned by: {}\nTime: {}\nReason: {}".format(warned_by, date, warn_reason))
			x += 1
		return await ctx.send(embed=em)

	@warn.command()
	async def remove(self, ctx, user: roxbot.converters.UserConverter=None, index=None):
		"""Removes one or all of the warnings for a user."""
		user_id = str(user.id)
		settings = gs.get(ctx.guild)

		if index:
			try:
				index = int(index)
				index -= 1
				settings.warnings[user_id].pop(index)
				if not settings.warnings[user_id]:
					settings.warnings.pop(user_id)

				settings.update(settings.warnings, "warnings")
				return await ctx.send("Removed Warning {} from {}".format(index+1, str(user)))

			except Exception as e:
				if isinstance(e, IndexError):
					return await ctx.send(":warning: Index Error.")
				elif isinstance(e, KeyError):
					return await ctx.send("Could not find user in warning list.")
				elif isinstance(e, ValueError):
					return await ctx.send("Please enter a valid index number.")
				else:
					raise e
		else:
			try:
				settings.warnings.pop(user_id)
				settings.update(settings.warnings, "warnings")
				return await ctx.send("Removed all warnings for {}".format(str(user)))
			except KeyError:
				return await ctx.send("Could not find user in warning list.")

	@commands.bot_has_permissions(ban_members=True)
	@warn.command()
	async def prune(self, ctx, dry_run=0):
		"""Purges banned users from the warn list. Add a 1 at the end to do a dry run."""
		settings = gs.get(ctx.guild)
		warnings = settings.warnings.copy()
		count = 0
		for ban in await ctx.guild.bans():
			for user in warnings:
				if int(user) == ban.user.id:
					if dry_run == 0:
						settings.warnings.pop(user)
					count += 1
		settings.update(settings.warnings, "warnings")
		return await ctx.send("Purged {} banned users from the warn list.".format(count))

	@commands.has_permissions(kick_members=True)
	@commands.bot_has_permissions(kick_members=True)
	@bot.command()
	async def kick(self, ctx, member: discord.Member, *, reason=""):
		"""Kicks mentioned user. Allows you to give a reason."""
		try:
			await member.kick(reason=reason)
			return await ctx.send("Kicked {} with reason: '{}'".format(member, reason))
		except discord.Forbidden:
			return await ctx.send("I can't kick the owner or users higher or equal to me.")

	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	@bot.command()
	async def ban(self, ctx, member: discord.Member, *, reason=""):
		"""Bans mentioned user. Allows you to give a reason."""
		try:
			await member.ban(reason=reason, delete_message_days=0)
			return await ctx.send("Banned {} with reason: '{}'".format(member, reason))
		except discord.Forbidden:
			return await ctx.send("I can't kick the owner or users higher or equal to me.")

	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	@bot.command()
	async def unban(self, ctx, member: roxbot.converters.UserConverter, *, reason=""):
		"""Unbans user with given ID. Allows you to give a reason."""
		mem = None
		for ban in await ctx.guild.bans():
			if ban.user.id == member.id:
				mem = ban.user
		if mem is None:
			raise bot.CommandError("User not found in bans.")
		try:
			await ctx.guild.unban(mem, reason=reason)
			return await ctx.send("Unbanned {} with reason: '{}'".format(mem, reason))
		except discord.Forbidden:
			return await ctx.send("I can't kick the owner or users higher or equal to me.")


def setup(bot_client):
	bot_client.add_cog(Admin(bot_client))
