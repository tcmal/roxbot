import json
# TODO: Make the convert stuff seperate but cant do that now cause it would require how you interact with the guild settings api.
# Cause a settings dict would be split into two more instead of just the settings.

guild_template = {
			"example": {
				"greets": {
					"enabled": 0,
					"convert": {"enabled": "bool", "welcome-channel": "channel"},
					"welcome-channel": 0,
					"member-role": "",
					"custom-message": "",
					"default-message": "Be sure to read the rules."
				},
				"goodbyes": {
					"enabled": 0,
					"convert": {"enabled": "bool", "goodbye-channel": "channel"},
					"goodbye-channel": 0,
				},
				"self_assign": {
					"enabled": 0,
					"convert": {"enabled": "bool", "roles": "role"},
					"roles": []
				},
				"twitch": {
					"enabled": 0,
					"convert": {"enabled": "bool", "channel": "channel", "whitelist_enabled": "bool", "whitelist": "user"},
					"channel": 0,
					"whitelist_enabled": 0,
					"whitelist": []
				},
				"nsfw": {
					"enabled": 0,
					"channels": [],
					"convert": {"enabled": "bool", "channels": "channel"},
					"blacklist": []
				},
				"perm_roles": {
					"convert": {"admin": "role", "mod": "role"},
					"admin": [],
					"mod": []
				},
				"custom_commands": {
					"0": {},
					"1": {}
				},
				"gss": {
					"log_channel": "",
					"required_days": "",
					"required_score": "",
				},
				"warnings": {},
				"is_anal": {"y/n": 0},
				"logging": {
					"enabled": 0,
					"convert": {"enabled": "bool", "channel": "channel"},
					"channel": 0
				},
				"voice": {
					"need_perms": 0,
					"skip_voting": 0,
					"skip_ratio": 0.6,
					"convert": {"need_perms": "bool", "skip_voting": "bool"},
					"max_length": 600
				}
			}
}


def _open_config():
	"""
	Opens the guild settings file
	:return settings file: :type dict:
	"""
	with open('roxbot/settings/servers.json', 'r') as config_file:
		return json.load(config_file)


def _write_changes(config):
	"""
	Writes given config to disk.
	:param config: :type dict:
	:return:
	"""
	with open('roxbot/settings/servers.json', 'w') as conf_file:
		json.dump(config, conf_file)


def backup(config, name):
	with open('roxbot/settings/backups/{}.json'.format(name), "w") as f:
		json.dump(config, f)


def remove_guild(guild):
	settings = _open_config()
	settings.pop(str(guild.id))
	_write_changes(settings)


def add_guild(guild):
	settings = _open_config()
	settings[str(guild.id)] = guild_template["example"]
	_write_changes(settings)


def error_check(servers):
	settings = _open_config()
	for server in servers:
		# Server ID needs to be made a string for this statement because keys have to be strings in JSON. Which is annoying now we use int for ids.
		server_id = str(server.id)
		if str(server_id) not in settings:
			settings[server_id] = guild_template["example"]
			_write_changes(settings)
			print(
				"WARNING: The settings file for {} was not found. A template has been loaded and saved. All cogs are turned off by default.".format(
					server.name.upper()))
		else:
			for cog_setting in guild_template["example"]:
				if cog_setting not in settings[server_id]:
					settings[server_id][cog_setting] = guild_template["example"][
						cog_setting]
					_write_changes(settings)
					print(
						"WARNING: The settings file for {} was missing the {} cog. This has been fixed with the template version. It is disabled by default.".format(
							server.name.upper(), cog_setting.upper()))
				for setting in guild_template["example"][cog_setting]:
					if setting not in settings[server_id][cog_setting]:
						settings[server_id][cog_setting][setting] = guild_template["example"][
							cog_setting][setting]
						_write_changes(settings)
						print(
							"WARNING: The settings file for {} was missing the {} setting in the {} cog. This has been fixed with the template version. It is disabled by default.".format(
								server.name.upper(), setting.upper(), cog_setting.upper()))


def get_all(guilds):
	"""
	Returns a list of GuildSettings for all guilds the bot can see.
	:param guilds:
	:return list of GuildSettings: :type list:
	"""
	error_check(guilds)
	guild_list = []
	for guild in guilds:
		guild = GuildSettings(guild)
		guild_list.append(guild)
	return guild_list


def get(guild):
	"""
	Gets a single GuildSettings Object representing the settings of that guild
	:param guild:
	:return Single GuildSettings Object: :type GuildSettings:
	"""
	return GuildSettings(guild)


def get_guild(guilds, wanted_guild):
	for guild in guilds:
		if guild.id == wanted_guild.id:
			return guild
	return None


class GuildSettings(object):
	"""
	An Object to store all settings for one guild.
	The goal is to make editing settings a lot easier and make it so you don't have to handle things like ID's which caused a lot of issues when moving over to discord.py 1.0
	"""
	__slots__ = ["settings", "id", "name", "logging", "nsfw", "self_assign", "greets", "goodbyes", "twitch", "perm_roles", "custom_commands", "warnings", "is_anal", "voice", "gss"]

	def __init__(self, guild):
		self.id = guild.id
		self.name = str(guild)
		self.settings = self.refresh()

		self.get_settings()

	def __str__(self):
		return self.name

	def __iter__(self):
		list_settings = list(self.settings)
		list_settings.sort()
		for setting in list_settings:
			yield setting

	@staticmethod
	def _convert(settings, option="int"):
		for key, setting in settings.items():
			if setting.get("convert"):
				for x in setting["convert"].keys():
					if setting["convert"][x] != "bool":
						if isinstance(setting[x], list):
							for y, value in enumerate(setting[x]):
								if option == "str":
									setting[x][y] = str(value)
								else:
									setting[x][y] = int(value)
						else:
							if option == "str":
								setting[x] = str(setting[x])
							else:
								setting[x] = int(setting[x])
			settings[key] = setting
		return settings

	def refresh(self):
		settings = _open_config()[str(self.id)]
		self._convert(settings)
		return settings

	def get_settings(self):
		self.logging = self.settings["logging"]
		self.nsfw = self.settings["nsfw"]
		self.self_assign = self.settings["self_assign"]
		self.greets = self.settings["greets"]
		self.goodbyes = self.settings["goodbyes"]
		self.twitch = self.settings["twitch"]
		self.perm_roles = self.settings["perm_roles"]
		self.custom_commands = self.settings["custom_commands"]
		self.warnings = self.settings["warnings"]
		self.is_anal = self.settings["is_anal"]
		self.voice = self.settings["voice"]
		# Add custom cog settings loading here
		self.gss = self.settings["gss"]

	def update(self, changed_dict, setting = None):
		self.settings = self.refresh()
		self.get_settings()
		if setting is not None:
			self.settings[setting] = changed_dict
		else:
			self.settings = changed_dict
		settings = self.settings.copy()
		self._convert(settings, "str")
		json = _open_config()
		json[str(self.id)] = settings
		_write_changes(json)
		self.get_settings()
