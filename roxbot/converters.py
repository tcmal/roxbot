from discord.ext import commands


class UserConverter(commands.UserConverter):
	"""Overriding the discord version to add a slower global look up for when it is a requirement to return a user who has left the guild.

	Converts to a :class:`User`.

	All lookups are via the global user cache. (Excluding the last one which makes an api call to discord.

	The lookup strategy is as follows (in order):

	1. Lookup by ID.
	2. Lookup by mention.
	3. Lookup by name#discrim
	4. Lookup by name
	5. Lookup by get_user_info
	"""
	async def convert(self, ctx, argument):
		try:
			result = await super().convert(ctx, argument)
		except commands.BadArgument as e:
			try:
				result = await ctx.bot.get_user_info(argument)
			except:  # Bare except or otherwise it will raise its own BadArgument and have a pretty shitty error message that isn't useful.
				raise e

		return result


class EmojiConverter(commands.EmojiConverter):
	"""Just like the normla EmojiConverter class but with a custom error message and planned extra feature."""
	async def convert(self, ctx, argument):
		try:
			return await super().convert(ctx, argument)
		except:  # Same as above
			return argument


class AvatarURL(commands.UserConverter):
	"""
	Overriding the discord version to make it a converter appropriate for the image cog.
	
	Converts the input into a avatar url or url to an image provided. Either through URL or Attachments.

	1. Look up if argument is a URL
	3. Look up if argument is user
	
	Will do a user lookup, if that fails, then tries to parse the argument for a link
	"""
	async def convert(self, ctx, argument):
		if any(x in argument.split(".")[-1] for x in ("png", "jpg", "jpeg")):
			return argument
		else:
			try:
				user = await super().convert(ctx, argument)
				return user.avatar_url_as(format="png")
			except:  # Same as above
				raise commands.BadArgument("No valid image/user given.")


# TODO: Make functions that work like converters but aren't so they actually work in other areas too.
