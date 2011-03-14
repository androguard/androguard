# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.org>
# All rights reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of  
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.

DVM_PERMISSIONS = { 
"REBOOT" = {
	"android.os.RecoverySystem" : [
		("F", "installPackage", "(Landroid/content/Context;Ljava/io/File;)V"),
		("F", "rebootWipeUserData", "(Landroid/content/Context;)V"),
	],
	"android.content.Intent" : [
		("C", "IntentResolution", "Ljava/lang/String;"),
		("C", "ACTION_REBOOT", "Ljava/lang/String;"),
	],
	"android.os.PowerManager" : [
		("F", "reboot", "(Ljava/lang/String;)V"),
	],
},
"RECORD_AUDIO" = {
	"android.net.sip.SipAudioCall" : [
		("F", "startAudio", "()V"),
	],
},
"BIND_INPUT_METHOD" = {
	"android.view.inputmethod.InputMethod" : [
		("C", "SERVICE_INTERFACE", "Ljava/lang/String;"),
	],
},
"DUMP" = {
	"android.os.Debug" : [
		("F", "dumpService", "(Ljava/lang/String;Ljava/io/FileDescriptor;[Ljava/lang/String;)B"),
	],
	"android.os.IBinder" : [
		("C", "DUMP_TRANSACTION", "I"),
	],
},
"ACCESS_MOCK_LOCATION" = {
	"android.location.LocationManager" : [
		("F", "addTestProvider", "(Ljava/lang/String;BBBBBBBII)V"),
		("F", "clearTestProviderEnabled", "(Ljava/lang/String;)V"),
		("F", "clearTestProviderLocation", "(Ljava/lang/String;)V"),
		("F", "clearTestProviderStatus", "(Ljava/lang/String;)V"),
		("F", "removeTestProvider", "(Ljava/lang/String;)V"),
		("F", "setTestProviderEnabled", "(Ljava/lang/String;B)V"),
		("F", "setTestProviderLocation", "(Ljava/lang/String;Landroid/location/Location;)V"),
		("F", "setTestProviderStatus", "(Ljava/lang/String;ILandroid/os/Bundle;J)V"),
	],
},
"GLOBAL_SEARCH" = {
	"android.app.SearchManager" : [
		("C", "EXTRA_SELECT_QUERY", "Ljava/lang/String;"),
		("C", "INTENT_ACTION_GLOBAL_SEARCH", "Ljava/lang/String;"),
	],
},
"ACCOUNT_MANAGER" = {
	"android.accounts.AccountManager" : [
		("C", "KEY_ACCOUNT_MANAGER_RESPONSE", "Ljava/lang/String;"),
	],
},
"WAKE_LOCK" = {
	"android.net.sip.SipAudioCall" : [
		("F", "startAudio", "()V"),
	],
	"android.media.MediaPlayer" : [
		("F", "setWakeMode", "(Landroid/content/Context;I)V"),
	],
	"android.os.PowerManager" : [
		("C", "ACQUIRE_CAUSES_WAKEUP", "I"),
		("C", "FULL_WAKE_LOCK", "I"),
		("C", "ON_AFTER_RELEASE", "I"),
		("C", "PARTIAL_WAKE_LOCK", "I"),
		("C", "SCREEN_BRIGHT_WAKE_LOCK", "I"),
		("C", "SCREEN_DIM_WAKE_LOCK", "I"),
		("F", "newWakeLock", "(ILjava/lang/String;)"),
	],
},
"GET_TASKS" = {
	"android.app.ActivityManager" : [
		("F", "getRecentTasks", "(II)Ljava/util/List;"),
		("F", "getRunningTasks", "(I)Ljava/util/List;"),
	],
},
"VIBRATE" = {
	"android.provider.Settings.System" : [
		("C", "VIBRATE_ON", "Ljava/lang/String;"),
	],
	"android.app.Notification" : [
		("C", "DEFAULT_VIBRATE", "I"),
		("C", "defaults", "I"),
	],
	"android.app.Notification.Builder" : [
		("F", "setDefaults", "(I)"),
	],
	"android.media.AudioManager" : [
		("C", "EXTRA_RINGER_MODE", "Ljava/lang/String;"),
		("C", "EXTRA_VIBRATE_SETTING", "Ljava/lang/String;"),
		("C", "EXTRA_VIBRATE_TYPE", "Ljava/lang/String;"),
		("C", "FLAG_REMOVE_SOUND_AND_VIBRATE", "I"),
		("C", "FLAG_VIBRATE", "I"),
		("C", "RINGER_MODE_VIBRATE", "I"),
		("C", "VIBRATE_SETTING_CHANGED_ACTION", "Ljava/lang/String;"),
		("C", "VIBRATE_SETTING_OFF", "I"),
		("C", "VIBRATE_SETTING_ON", "I"),
		("C", "VIBRATE_SETTING_ONLY_SILENT", "I"),
		("C", "VIBRATE_TYPE_NOTIFICATION", "I"),
		("C", "VIBRATE_TYPE_RINGER", "I"),
		("F", "getRingerMode", "()I"),
		("F", "getVibrateSetting", "(I)I"),
		("F", "setRingerMode", "(I)V"),
		("F", "setVibrateSetting", "(II)V"),
		("F", "shouldVibrate", "(I)B"),
	],
},
"REORDER_TASKS" = {
	"android.app.ActivityManager" : [
		("F", "moveTaskToFront", "(II)V"),
	],
},
"ACCESS_COARSE_LOCATION" = {
	"android.telephony.TelephonyManager" : [
		("F", "getCellLocation", "()Landroid/telephony/CellLocation;"),
	],
	"android.telephony.PhoneStateListener" : [
		("C", "LISTEN_CELL_LOCATION", "I"),
	],
	"android.location.LocationManager" : [
		("C", "NETWORK_PROVIDER", "Ljava/lang/String;"),
	],
},
"BIND_DEVICE_ADMIN" = {
	"android.app.admin.DeviceAdminReceiver" : [
		("C", "ACTION_DEVICE_ADMIN_ENABLED", "Ljava/lang/String;"),
	],
},
"GET_ACCOUNTS" = {
	"android.accounts.AccountManager" : [
		("F", "getAccounts", "()"),
		("F", "getAccountsByType", "(Ljava/lang/String;)"),
		("F", "getAccountsByTypeAndFeatures", "(Ljava/lang/String;[Ljava/lang/String;[Landroid/accounts/AccountManagerCallback<android/accounts/Account[;Landroid/os/Handler;)Landroid/accounts/AccountManagerFuture;"),
		("F", "hasFeatures", "(Landroid/accounts/Account;[Ljava/lang/String;Landroid/accounts/AccountManagerCallback<java/lang/Boolean>;Landroid/os/Handler;)Landroid/accounts/AccountManagerFuture;"),
	],
},
"READ_HISTORY_BOOKMARKS" = {
	"android.provider.Browser" : [
		("C", "BOOKMARKS_URI", "Landroid/net/Uri;"),
		("C", "SEARCHES_URI", "Landroid/net/Uri;"),
		("F", "addSearchUrl", "(Landroid/content/ContentResolver;Ljava/lang/String;)V"),
		("F", "canClearHistory", "(Landroid/content/ContentResolver;)B"),
		("F", "getAllBookmarks", "(Landroid/content/ContentResolver;)Landroid/database/Cursor;"),
		("F", "getAllVisitedUrls", "(Landroid/content/ContentResolver;)Landroid/database/Cursor;"),
		("F", "requestAllIcons", "(Landroid/content/ContentResolver;Ljava/lang/String;Landroid/webkit/WebIconDatabase/IconListener;)V"),
		("F", "truncateHistory", "(Landroid/content/ContentResolver;)V"),
		("F", "updateVisitedHistory", "(Landroid/content/ContentResolver;Ljava/lang/String;B)V"),
	],
},
"NFC" = {
	"android.inputmethodservice.InputMethodService" : [
		("C", "SoftInputView", "I"),
		("C", "CandidatesView", "I"),
		("C", "FullscreenMode", "I"),
		("C", "GeneratingText", "I"),
	],
	"android.nfc.tech.NfcA" : [
		("F", "close", "()V"),
		("F", "connect", "()V"),
		("F", "get", "(Landroid/nfc/Tag;)"),
		("F", "transceive", "([B)[B"),
	],
	"android.nfc.tech.NfcB" : [
		("F", "close", "()V"),
		("F", "connect", "()V"),
		("F", "get", "(Landroid/nfc/Tag;)"),
		("F", "transceive", "([B)[B"),
	],
	"android.nfc.NfcAdapter" : [
		("C", "ACTION_TECH_DISCOVERED", "Ljava/lang/String;"),
		("F", "disableForegroundDispatch", "(Landroid/app/Activity;)V"),
		("F", "disableForegroundNdefPush", "(Landroid/app/Activity;)V"),
		("F", "enableForegroundDispatch", "(Landroid/app/Activity;Landroid/app/PendingIntent;[Landroid/content/IntentFilter;[[Ljava/lang/String[];)V"),
		("F", "enableForegroundNdefPush", "(Landroid/app/Activity;Landroid/nfc/NdefMessage;)V"),
		("F", "getDefaultAdapter", "()"),
		("F", "getDefaultAdapter", "(Landroid/content/Context;)"),
		("F", "isEnabled", "()B"),
	],
	"android.nfc.tech.NfcF" : [
		("F", "close", "()V"),
		("F", "connect", "()V"),
		("F", "get", "(Landroid/nfc/Tag;)"),
		("F", "transceive", "([B)[B"),
	],
	"android.nfc.tech.NdefFormatable" : [
		("F", "close", "()V"),
		("F", "connect", "()V"),
		("F", "format", "(Landroid/nfc/NdefMessage;)V"),
		("F", "formatReadOnly", "(Landroid/nfc/NdefMessage;)V"),
	],
	"android.app.Activity" : [
		("C", "Fragments", "I"),
		("C", "ActivityLifecycle", "I"),
		("C", "ConfigurationChanges", "I"),
		("C", "StartingActivities", "I"),
		("C", "SavingPersistentState", "I"),
		("C", "Permissions", "I"),
		("C", "ProcessLifecycle", "I"),
	],
	"android.nfc.tech.MifareClassic" : [
		("C", "KEY_NFC_FORUM", "[B"),
		("F", "authenticateSectorWithKeyA", "(I[B)B"),
		("F", "authenticateSectorWithKeyB", "(I[B)B"),
		("F", "close", "()V"),
		("F", "connect", "()V"),
		("F", "decrement", "(II)V"),
		("F", "increment", "(II)V"),
		("F", "readBlock", "(I)[B"),
		("F", "restore", "(I)V"),
		("F", "transceive", "([B)[B"),
		("F", "transfer", "(I)V"),
		("F", "writeBlock", "(I[B)V"),
	],
	"android.nfc.Tag" : [
		("F", "getTechList", "()[Ljava/lang/String;"),
	],
	"android.app.Service" : [
		("C", "WhatIsAService", "I"),
		("C", "ServiceLifecycle", "I"),
		("C", "Permissions", "I"),
		("C", "ProcessLifecycle", "I"),
		("C", "LocalServiceSample", "I"),
		("C", "RemoteMessengerServiceSample", "I"),
	],
	"android.nfc.NfcManager" : [
		("F", "getDefaultAdapter", "()"),
	],
	"android.nfc.tech.MifareUltralight" : [
		("F", "close", "()V"),
		("F", "connect", "()V"),
		("F", "readPages", "(I)[B"),
		("F", "transceive", "([B)[B"),
		("F", "writePage", "(I[B)V"),
	],
	"android.nfc.tech.NfcV" : [
		("F", "close", "()V"),
		("F", "connect", "()V"),
		("F", "get", "(Landroid/nfc/Tag;)"),
		("F", "transceive", "([B)[B"),
	],
	"android.nfc.tech.TagTechnology" : [
		("F", "close", "()V"),
		("F", "connect", "()V"),
	],
	"android.preference.PreferenceActivity" : [
		("C", "SampleCode", "Ljava/lang/String;"),
	],
	"android.content.pm.PackageManager" : [
		("C", "FEATURE_NFC", "Ljava/lang/String;"),
	],
	"android.content.Context" : [
		("C", "NFC_SERVICE", "Ljava/lang/String;"),
	],
	"android.nfc.tech.Ndef" : [
		("C", "NFC_FORUM_TYPE_1", "Ljava/lang/String;"),
		("C", "NFC_FORUM_TYPE_2", "Ljava/lang/String;"),
		("C", "NFC_FORUM_TYPE_3", "Ljava/lang/String;"),
		("C", "NFC_FORUM_TYPE_4", "Ljava/lang/String;"),
		("F", "close", "()V"),
		("F", "connect", "()V"),
		("F", "getType", "()Ljava/lang/String;"),
		("F", "isWritable", "()B"),
		("F", "makeReadOnly", "()B"),
		("F", "writeNdefMessage", "(Landroid/nfc/NdefMessage;)V"),
	],
	"android.nfc.tech.IsoDep" : [
		("F", "close", "()V"),
		("F", "connect", "()V"),
		("F", "setTimeout", "(I)V"),
		("F", "transceive", "([B)[B"),
	],
},
"WRITE_EXTERNAL_STORAGE" = {
	"android.os.Build.VERSION_CODES" : [
		("C", "DONUT", "I"),
	],
	"android.app.DownloadManager.Request" : [
		("F", "setDestinationUri", "(Landroid/net/Uri;)Landroid/app/DownloadManager/Request;"),
	],
},
"SET_TIME" = {
	"android.app.AlarmManager" : [
		("F", "setTime", "(J)V"),
		("F", "setTimeZone", "(Ljava/lang/String;)V"),
	],
},
"AUTHENTICATE_ACCOUNTS" = {
	"android.accounts.AccountManager" : [
		("F", "addAccountExplicitly", "(Landroid/accounts/Account;Ljava/lang/String;Landroid/os/Bundle;)B"),
		("F", "getPassword", "(Landroid/accounts/Account;)Ljava/lang/String;"),
		("F", "getUserData", "(Landroid/accounts/Account;Ljava/lang/String;)Ljava/lang/String;"),
		("F", "peekAuthToken", "(Landroid/accounts/Account;Ljava/lang/String;)Ljava/lang/String;"),
		("F", "setAuthToken", "(Landroid/accounts/Account;Ljava/lang/String;Ljava/lang/String;)V"),
		("F", "setPassword", "(Landroid/accounts/Account;Ljava/lang/String;)V"),
		("F", "setUserData", "(Landroid/accounts/Account;Ljava/lang/String;Ljava/lang/String;)V"),
	],
},
"FACTORY_TEST" = {
	"android.content.pm.ApplicationInfo" : [
		("C", "FLAG_FACTORY_TEST", "I"),
		("C", "flags", "I"),
	],
	"android.content.Intent" : [
		("C", "IntentResolution", "Ljava/lang/String;"),
		("C", "ACTION_FACTORY_TEST", "Ljava/lang/String;"),
	],
},
"PROCESS_OUTGOING_CALLS" = {
	"android.content.Intent" : [
		("C", "ACTION_NEW_OUTGOING_CALL", "Ljava/lang/String;"),
	],
},
"READ_PHONE_STATE" = {
	"android.telephony.TelephonyManager" : [
		("C", "ACTION_PHONE_STATE_CHANGED", "Ljava/lang/String;"),
		("F", "getDeviceId", "()Ljava/lang/String;"),
		("F", "getDeviceSoftwareVersion", "()Ljava/lang/String;"),
		("F", "getLine1Number", "()Ljava/lang/String;"),
		("F", "getSimSerialNumber", "()Ljava/lang/String;"),
		("F", "getSubscriberId", "()Ljava/lang/String;"),
		("F", "getVoiceMailAlphaTag", "()Ljava/lang/String;"),
		("F", "getVoiceMailNumber", "()Ljava/lang/String;"),
	],
	"android.telephony.PhoneStateListener" : [
		("C", "LISTEN_CALL_FORWARDING_INDICATOR", "I"),
		("C", "LISTEN_CALL_STATE", "I"),
		("C", "LISTEN_DATA_ACTIVITY", "I"),
		("C", "LISTEN_MESSAGE_WAITING_INDICATOR", "I"),
		("C", "LISTEN_SIGNAL_STRENGTH", "I"),
	],
	"android.os.Build.VERSION_CODES" : [
		("C", "DONUT", "I"),
	],
},
"READ_LOGS" = {
	"android.os.DropBoxManager" : [
		("C", "ACTION_DROPBOX_ENTRY_ADDED", "Ljava/lang/String;"),
		("F", "getNextEntry", "(Ljava/lang/String;J)"),
	],
},
"BROADCAST_STICKY" = {
	"android.content.Context" : [
		("F", "removeStickyBroadcast", "(Landroid/content/Intent;)V"),
		("F", "sendStickyBroadcast", "(Landroid/content/Intent;)V"),
	],
	"android.content.ContextWrapper" : [
		("F", "removeStickyBroadcast", "(Landroid/content/Intent;)V"),
		("F", "sendStickyBroadcast", "(Landroid/content/Intent;)V"),
	],
},
"BIND_WALLPAPER" = {
	"android.service.wallpaper.WallpaperService" : [
		("C", "SERVICE_INTERFACE", "Ljava/lang/String;"),
	],
},
"KILL_BACKGROUND_PROCESSES" = {
	"android.app.ActivityManager" : [
		("F", "killBackgroundProcesses", "(Ljava/lang/String;)V"),
	],
},
"SET_TIME_ZONE" = {
	"android.app.AlarmManager" : [
		("F", "setTimeZone", "(Ljava/lang/String;)V"),
	],
},
"BLUETOOTH_ADMIN" = {
	"android.bluetooth.BluetoothAdapter" : [
		("F", "cancelDiscovery", "()B"),
		("F", "disable", "()B"),
		("F", "enable", "()B"),
		("F", "setName", "(Ljava/lang/String;)B"),
		("F", "startDiscovery", "()B"),
	],
},
"STATUS_BAR" = {
	"android.view.View.OnSystemUiVisibilityChangeListener" : [
		("F", "onSystemUiVisibilityChange", "(I)V"),
	],
	"android.view.View" : [
		("C", "STATUS_BAR_HIDDEN", "I"),
		("C", "STATUS_BAR_VISIBLE", "I"),
	],
	"android.view.WindowManager.LayoutParams" : [
		("C", "TYPE_STATUS_BAR", "I"),
		("C", "TYPE_STATUS_BAR_PANEL", "I"),
		("C", "systemUiVisibility", "I"),
		("C", "type", "I"),
	],
},
"BLUETOOTH" = {
	"android.bluetooth.BluetoothAdapter" : [
		("C", "ACTION_CONNECTION_STATE_CHANGED", "Ljava/lang/String;"),
		("C", "ACTION_DISCOVERY_FINISHED", "Ljava/lang/String;"),
		("C", "ACTION_DISCOVERY_STARTED", "Ljava/lang/String;"),
		("C", "ACTION_LOCAL_NAME_CHANGED", "Ljava/lang/String;"),
		("C", "ACTION_REQUEST_DISCOVERABLE", "Ljava/lang/String;"),
		("C", "ACTION_REQUEST_ENABLE", "Ljava/lang/String;"),
		("C", "ACTION_SCAN_MODE_CHANGED", "Ljava/lang/String;"),
		("C", "ACTION_STATE_CHANGED", "Ljava/lang/String;"),
		("F", "cancelDiscovery", "()B"),
		("F", "disable", "()B"),
		("F", "enable", "()B"),
		("F", "getAddress", "()Ljava/lang/String;"),
		("F", "getBondedDevices", "()Ljava/util/Set;"),
		("F", "getName", "()Ljava/lang/String;"),
		("F", "getScanMode", "()I"),
		("F", "getState", "()I"),
		("F", "isDiscovering", "()B"),
		("F", "isEnabled", "()B"),
		("F", "listenUsingInsecureRfcommWithServiceRecord", "(Ljava/lang/String;Ljava/util/UUID;)Landroid/bluetooth/BluetoothServerSocket;"),
		("F", "listenUsingRfcommWithServiceRecord", "(Ljava/lang/String;Ljava/util/UUID;)Landroid/bluetooth/BluetoothServerSocket;"),
		("F", "setName", "(Ljava/lang/String;)B"),
		("F", "startDiscovery", "()B"),
	],
	"android.bluetooth.BluetoothHeadset" : [
		("C", "ACTION_AUDIO_STATE_CHANGED", "Ljava/lang/String;"),
		("C", "ACTION_CONNECTION_STATE_CHANGED", "Ljava/lang/String;"),
		("C", "ACTION_VENDOR_SPECIFIC_HEADSET_EVENT", "Ljava/lang/String;"),
		("F", "getConnectedDevices", "()Ljava/util/List;"),
		("F", "getConnectionState", "(Landroid/bluetooth/BluetoothDevice;)I"),
		("F", "getDevicesMatchingConnectionStates", "([I)Ljava/util/List;"),
		("F", "isAudioConnected", "(Landroid/bluetooth/BluetoothDevice;)B"),
		("F", "startVoiceRecognition", "(Landroid/bluetooth/BluetoothDevice;)B"),
		("F", "stopVoiceRecognition", "(Landroid/bluetooth/BluetoothDevice;)B"),
	],
	"android.bluetooth.BluetoothDevice" : [
		("C", "ACTION_ACL_CONNECTED", "Ljava/lang/String;"),
		("C", "ACTION_ACL_DISCONNECTED", "Ljava/lang/String;"),
		("C", "ACTION_ACL_DISCONNECT_REQUESTED", "Ljava/lang/String;"),
		("C", "ACTION_BOND_STATE_CHANGED", "Ljava/lang/String;"),
		("C", "ACTION_CLASS_CHANGED", "Ljava/lang/String;"),
		("C", "ACTION_FOUND", "Ljava/lang/String;"),
		("C", "ACTION_NAME_CHANGED", "Ljava/lang/String;"),
		("F", "createInsecureRfcommSocketToServiceRecord", "(Ljava/util/UUID;)Landroid/bluetooth/BluetoothSocket;"),
		("F", "createRfcommSocketToServiceRecord", "(Ljava/util/UUID;)Landroid/bluetooth/BluetoothSocket;"),
		("F", "getBluetoothClass", "()"),
		("F", "getBondState", "()I"),
		("F", "getName", "()Ljava/lang/String;"),
	],
	"android.content.pm.PackageManager" : [
		("C", "FEATURE_BLUETOOTH", "Ljava/lang/String;"),
	],
	"android.bluetooth.BluetoothAssignedNumbers" : [
		("C", "BLUETOOTH_SIG", "I"),
	],
	"android.bluetooth.BluetoothA2dp" : [
		("C", "ACTION_CONNECTION_STATE_CHANGED", "Ljava/lang/String;"),
		("C", "ACTION_PLAYING_STATE_CHANGED", "Ljava/lang/String;"),
		("F", "getConnectedDevices", "()Ljava/util/List;"),
		("F", "getConnectionState", "(Landroid/bluetooth/BluetoothDevice;)I"),
		("F", "getDevicesMatchingConnectionStates", "([I)Ljava/util/List;"),
		("F", "isA2dpPlaying", "(Landroid/bluetooth/BluetoothDevice;)B"),
	],
	"android.provider.Settings.System" : [
		("C", "AIRPLANE_MODE_RADIOS", "Ljava/lang/String;"),
		("C", "BLUETOOTH_DISCOVERABILITY", "Ljava/lang/String;"),
		("C", "BLUETOOTH_DISCOVERABILITY_TIMEOUT", "Ljava/lang/String;"),
		("C", "BLUETOOTH_ON", "Ljava/lang/String;"),
		("C", "RADIO_BLUETOOTH", "Ljava/lang/String;"),
		("C", "VOLUME_BLUETOOTH_SCO", "Ljava/lang/String;"),
	],
	"android.bluetooth.BluetoothProfile" : [
		("F", "getConnectedDevices", "()Ljava/util/List;"),
		("F", "getConnectionState", "(Landroid/bluetooth/BluetoothDevice;)I"),
		("F", "getDevicesMatchingConnectionStates", "([I)Ljava/util/List;"),
	],
	"android.os.Process" : [
		("C", "BLUETOOTH_GID", "I"),
	],
	"android.provider.Settings" : [
		("C", "ACTION_BLUETOOTH_SETTINGS", "Ljava/lang/String;"),
	],
	"android.media.AudioManager" : [
		("C", "ROUTE_BLUETOOTH", "I"),
		("C", "ROUTE_BLUETOOTH_A2DP", "I"),
		("C", "ROUTE_BLUETOOTH_SCO", "I"),
	],
	"android.provider.Settings.Secure" : [
		("C", "BLUETOOTH_ON", "Ljava/lang/String;"),
	],
},
"ACCESS_WIFI_STATE" = {
	"android.net.sip.SipAudioCall" : [
		("F", "startAudio", "()V"),
	],
},
"CAMERA" = {
	"android.hardware.Camera.ErrorCallback" : [
		("F", "onError", "(ILandroid/hardware/Camera;)V"),
	],
	"android.bluetooth.BluetoothClass.Device" : [
		("C", "AUDIO_VIDEO_VIDEO_CAMERA", "I"),
	],
	"android.content.pm.PackageManager" : [
		("C", "FEATURE_CAMERA", "Ljava/lang/String;"),
		("C", "FEATURE_CAMERA_AUTOFOCUS", "Ljava/lang/String;"),
		("C", "FEATURE_CAMERA_FLASH", "Ljava/lang/String;"),
		("C", "FEATURE_CAMERA_FRONT", "Ljava/lang/String;"),
	],
	"android.view.KeyEvent" : [
		("C", "KEYCODE_CAMERA", "I"),
	],
	"android.provider.MediaStore" : [
		("C", "INTENT_ACTION_STILL_IMAGE_CAMERA", "Ljava/lang/String;"),
		("C", "INTENT_ACTION_VIDEO_CAMERA", "Ljava/lang/String;"),
	],
	"android.hardware.Camera.CameraInfo" : [
		("C", "CAMERA_FACING_BACK", "I"),
		("C", "CAMERA_FACING_FRONT", "I"),
		("C", "facing", "I"),
	],
	"android.provider.ContactsContract.StatusColumns" : [
		("C", "CAPABILITY_HAS_CAMERA", "I"),
	],
	"android.hardware.Camera.Parameters" : [
		("F", "setRotation", "(I)V"),
	],
	"android.media.MediaRecorder.VideoSource" : [
		("C", "CAMERA", "I"),
	],
	"android.content.Intent" : [
		("C", "IntentResolution", "Ljava/lang/String;"),
		("C", "ACTION_CAMERA_BUTTON", "Ljava/lang/String;"),
	],
	"android.hardware.Camera" : [
		("C", "CAMERA_ERROR_SERVER_DIED", "I"),
		("C", "CAMERA_ERROR_UNKNOWN", "I"),
		("F", "setDisplayOrientation", "(I)V"),
	],
},
"SET_WALLPAPER" = {
	"android.content.Intent" : [
		("C", "IntentResolution", "Ljava/lang/String;"),
		("C", "ACTION_SET_WALLPAPER", "Ljava/lang/String;"),
	],
	"android.app.WallpaperManager" : [
		("C", "WALLPAPER_PREVIEW_META_DATA", "Ljava/lang/String;"),
	],
},
"INTERNET" = {
	"android.drm.DrmErrorEvent" : [
		("C", "TYPE_NO_INTERNET_CONNECTION", "I"),
	],
},
"ACCESS_FINE_LOCATION" = {
	"android.telephony.TelephonyManager" : [
		("F", "getCellLocation", "()Landroid/telephony/CellLocation;"),
	],
	"android.location.LocationManager" : [
		("C", "GPS_PROVIDER", "Ljava/lang/String;"),
		("C", "NETWORK_PROVIDER", "Ljava/lang/String;"),
		("C", "PASSIVE_PROVIDER", "Ljava/lang/String;"),
		("F", "addGpsStatusListener", "(Landroid/location/GpsStatus/Listener;)B"),
		("F", "addNmeaListener", "(Landroid/location/GpsStatus/NmeaListener;)B"),
	],
},
"MODIFY_AUDIO_SETTINGS" = {
	"android.net.sip.SipAudioCall" : [
		("F", "setSpeakerMode", "(B)V"),
	],
	"android.media.AudioManager" : [
		("F", "startBluetoothSco", "()V"),
		("F", "stopBluetoothSco", "()V"),
	],
},
"MANAGE_ACCOUNTS" = {
	"android.accounts.AccountManager" : [
		("F", "addAccount", "(Ljava/lang/String;Ljava/lang/String;[Ljava/lang/String;Landroid/os/Bundle;Landroid/app/Activity;Landroid/accounts/AccountManagerCallback<android/os/Bundle>;Landroid/os/Handler;)Landroid/accounts/AccountManagerFuture;"),
		("F", "clearPassword", "(Landroid/accounts/Account;)V"),
		("F", "confirmCredentials", "(Landroid/accounts/Account;Landroid/os/Bundle;Landroid/app/Activity;Landroid/accounts/AccountManagerCallback<android/os/Bundle>;Landroid/os/Handler;)Landroid/accounts/AccountManagerFuture;"),
		("F", "editProperties", "(Ljava/lang/String;Landroid/app/Activity;Landroid/accounts/AccountManagerCallback<android/os/Bundle>;Landroid/os/Handler;)Landroid/accounts/AccountManagerFuture;"),
		("F", "getAuthTokenByFeatures", "(Ljava/lang/String;Ljava/lang/String;[Ljava/lang/String;Landroid/app/Activity;Landroid/os/Bundle;Landroid/os/Bundle;Landroid/accounts/AccountManagerCallback<android/os/Bundle>;Landroid/os/Handler;)Landroid/accounts/AccountManagerFuture;"),
		("F", "invalidateAuthToken", "(Ljava/lang/String;Ljava/lang/String;)V"),
		("F", "removeAccount", "(Landroid/accounts/Account;Landroid/accounts/AccountManagerCallback<java/lang/Boolean>;Landroid/os/Handler;)Landroid/accounts/AccountManagerFuture;"),
		("F", "updateCredentials", "(Landroid/accounts/Account;Ljava/lang/String;Landroid/os/Bundle;Landroid/app/Activity;Landroid/accounts/AccountManagerCallback<android/os/Bundle>;Landroid/os/Handler;)Landroid/accounts/AccountManagerFuture;"),
	],
},
"USE_CREDENTIALS" = {
	"android.accounts.AccountManager" : [
		("F", "blockingGetAuthToken", "(Landroid/accounts/Account;Ljava/lang/String;B)Ljava/lang/String;"),
		("F", "getAuthToken", "(Landroid/accounts/Account;Ljava/lang/String;Landroid/os/Bundle;Landroid/app/Activity;Landroid/accounts/AccountManagerCallback<android/os/Bundle>;Landroid/os/Handler;)Landroid/accounts/AccountManagerFuture;"),
		("F", "getAuthToken", "(Landroid/accounts/Account;Ljava/lang/String;BLandroid/accounts/AccountManagerCallback<android/os/Bundle>;Landroid/os/Handler;)Landroid/accounts/AccountManagerFuture;"),
		("F", "invalidateAuthToken", "(Ljava/lang/String;Ljava/lang/String;)V"),
	],
},
"WRITE_HISTORY_BOOKMARKS" = {
	"android.provider.Browser" : [
		("C", "BOOKMARKS_URI", "Landroid/net/Uri;"),
		("C", "SEARCHES_URI", "Landroid/net/Uri;"),
		("F", "addSearchUrl", "(Landroid/content/ContentResolver;Ljava/lang/String;)V"),
		("F", "clearHistory", "(Landroid/content/ContentResolver;)V"),
		("F", "clearSearches", "(Landroid/content/ContentResolver;)V"),
		("F", "deleteFromHistory", "(Landroid/content/ContentResolver;Ljava/lang/String;)V"),
		("F", "deleteHistoryTimeFrame", "(Landroid/content/ContentResolver;JJ)V"),
		("F", "truncateHistory", "(Landroid/content/ContentResolver;)V"),
		("F", "updateVisitedHistory", "(Landroid/content/ContentResolver;Ljava/lang/String;B)V"),
	],
},
"RECEIVE_BOOT_COMPLETED" = {
	"android.content.Intent" : [
		("C", "ACTION_BOOT_COMPLETED", "Ljava/lang/String;"),
	],
},
"SET_ALARM" = {
	"android.provider.AlarmClock" : [
		("C", "ACTION_SET_ALARM", "Ljava/lang/String;"),
		("C", "EXTRA_HOUR", "Ljava/lang/String;"),
		("C", "EXTRA_MESSAGE", "Ljava/lang/String;"),
		("C", "EXTRA_MINUTES", "Ljava/lang/String;"),
		("C", "EXTRA_SKIP_UI", "Ljava/lang/String;"),
	],
},
}
