# -*- coding: utf-8 -*-
import os
import time
import datetime
import xml.etree.ElementTree as ET
from caches import check_databases, clean_databases
from caches.trakt_cache import clear_trakt_list_contents_data
from apis.trakt_api import trakt_sync_activities
from modules import kodi_utils, settings
from modules.nav_utils import sync_MyAccounts
from modules.settings_reader import get_setting, set_setting, make_settings_dict

logger = kodi_utils.logger
ls, monitor, path_exists, translate_path, is_playing = kodi_utils.local_string, kodi_utils.monitor, kodi_utils.path_exists, kodi_utils.translate_path, kodi_utils.player.isPlaying
get_property, set_property, clear_property, get_visibility = kodi_utils.get_property, kodi_utils.set_property, kodi_utils.clear_property, kodi_utils.get_visibility

class InitializeDatabases:
	def run(self):
		logger('B99', 'InitializeDatabases Service Starting')
		check_databases()
		return logger('B99', 'InitializeDatabases Service Finished')

class CheckSettingsFile:
	def run(self):
		logger('B99', 'CheckSettingsFile Service Starting')
		clear_property('B99_settings')
		profile_dir = translate_path('special://profile/addon_data/plugin.video.B99/')
		if not path_exists(profile_dir): kodi_utils.make_directorys(profile_dir)
		settings_xml = translate_path('special://profile/addon_data/plugin.video.B99/settings.xml')
		if not path_exists(settings_xml):
			__addon__ = kodi_utils.addon()
			addon_version = __addon__.getAddonInfo('version')
			__addon__.setSetting('version_number', addon_version)
			monitor.waitForAbort(0.5)
		make_settings_dict()
		set_property('B99_kodi_menu_cache', get_setting('kodi_menu_cache'))
		return logger('B99', 'CheckSettingsFile Service Finished')

class SyncMyAccounts:
	def run(self):
		logger('B99', 'SyncMyAccounts Service Starting')
		sync_MyAccounts(silent=True)
		return logger('B99', 'SyncMyAccounts Service Finished')

class ClearSubs:
	def run(self):
		logger('B99', 'Clear Subtitles Service Starting')
		sub_formats = ('.srt', '.ssa', '.smi', '.sub', '.idx')
		subtitle_path = 'special://temp/%s'
		files = kodi_utils.list_dirs(translate_path('special://temp/'))[1]
		for i in files:
			if i.startswith('B99Subs_') or i.endswith(sub_formats): kodi_utils.delete_file(translate_path(subtitle_path % i))
		return logger('B99', 'Clear Subtitles Service Finished')

class ReuseLanguageInvokerCheck:
	def run(self):
		logger('B99', 'ReuseLanguageInvokerCheck Service Starting')
		addon_xml = translate_path('special://home/addons/plugin.video.B99/addon.xml')
		tree = ET.parse(addon_xml)
		root = tree.getroot()
		current_addon_setting = get_setting('reuse_language_invoker', 'true')
		refresh, text = True, '%s\n%s' % (ls(33021), ls(33020))
		for item in root.iter('reuselanguageinvoker'):
			if item.text == current_addon_setting: refresh = False; break
			item.text = current_addon_setting
			tree.write(addon_xml)
			break
		if refresh and kodi_utils.confirm_dialog(text=text): kodi_utils.execute_builtin('LoadProfile(%s)' % kodi_utils.get_infolabel('system.profilename'))
		return logger('B99', 'ReuseLanguageInvokerCheck Service Finished')

class ViewsSetWindowProperties:
	def run(self):
		logger('B99', 'ViewsSetWindowProperties Service Starting')
		kodi_utils.set_view_properties()
		return logger('B99', 'ViewsSetWindowProperties Service Finished')

class AutoRun:
	def run(self):
		logger('B99', 'AutoRun Service Starting')
		if settings.auto_start_B99(): kodi_utils.execute_builtin('RunAddon(plugin.video.B99)')
		return logger('B99', 'AutoRun Service Finished')

class DatabaseMaintenance:
	def run(self):
		time = datetime.datetime.now()
		current_time = self._get_timestamp(time)
		due_clean = int(get_setting('database.maintenance.due', '0'))
		if current_time >= due_clean:
			logger('B99', 'Database Maintenance Service Starting')
			monitor.waitForAbort(10)
			clean_databases(current_time, database_check=False, silent=True)
			next_clean = str(int(self._get_timestamp(time + datetime.timedelta(days=3))))
			set_setting('database.maintenance.due', next_clean)
			return logger('B99', 'Database Maintenance Service Finished')

	def _get_timestamp(self, date_time):
		return int(time.mktime(date_time.timetuple()))

class TraktMonitor:
	def run(self):
		logger('B99', 'TraktMonitor Service Starting')
		trakt_service_string = 'TraktMonitor Service Update %s - %s'
		update_string = 'Next Update in %s minutes...'
		if not kodi_utils.get_property('B99_traktmonitor_first_run') == 'true':
			clear_trakt_list_contents_data('user_lists')
			kodi_utils.set_property('B99_traktmonitor_first_run', 'true')
		while not monitor.abortRequested():
			while is_playing() or get_visibility('Container().isUpdating') or get_property('B99_pause_services') == 'true': monitor.waitForAbort(10)
			if not kodi_utils.get_property('B99_traktmonitor_first_run') == 'true': monitor.waitForAbort(5)
			value, interval = settings.trakt_sync_interval()
			next_update_string = update_string % value
			status = trakt_sync_activities()
			if status == 'success':
				logger('B99', trakt_service_string % ('B99 TraktMonitor - Success', 'Trakt Update Performed'))
				if settings.trakt_sync_refresh_widgets():
					kodi_utils.widget_refresh()
					logger('B99', trakt_service_string % ('B99 TraktMonitor - Widgets Refresh', 'Setting Activated. Widget Refresh Performed'))
				else: logger('B99', trakt_service_string % ('B99 TraktMonitor - Widgets Refresh', 'Setting Disabled. Skipping Widget Refresh'))
			elif status == 'no account':
				logger('B99', trakt_service_string % ('B99 TraktMonitor - Aborted. No Trakt Account Active', next_update_string))
			elif status == 'failed':
				logger('B99', trakt_service_string % ('B99 TraktMonitor - Failed. Error from Trakt', next_update_string))
			else:# 'not needed'
				logger('B99', trakt_service_string % ('B99 TraktMonitor - Success. No Changes Needed', next_update_string))
			monitor.waitForAbort(interval)
		return logger('B99', 'TraktMonitor Service Finished')
