# MASTG coverage reference (Androguard scan_vulns)

**Updated:** 2026-10-02  
**Scope:** all 94 Android demos under [OWASP MASTG `demos/android`](https://github.com/OWASP/mastg/tree/master/demos/android), built via [mas-app-android](https://github.com/cpholguera/mas-app-android).

This is the **single** reference document for MASTG ↔ Androguard security-scanner coverage (checked into `docs/`).
Machine JSON: `workspace/reports/mastg-scan-validate-2026-09-29.json`. Expectations: `scripts/mastg_expected.json`.

## Overall status

| status | count | meaning |
|--------|------:|---------|
| pass | 87 | Curated expectation matched |
| gap | 0 | Scanned; lesson not yet curated / uncovered |
| skip | 7 | No injectable sources |
| fail | 0 | Expectation missed |

**Total:** 94 demos · **Frida-oriented:** 18

## Frida demos — static detection

Frida demos are those whose title/docs/scripts use Frida. `scan_vulns` assessment is whether the **lesson** is visible statically.

| static | count |
|--------|------:|
| hit | 13 |
| partial | 4 |
| miss | 0 |
| n/a | 1 |

| Demo | Title | Validate | Static | Categories | Assessment |
|------|-------|----------|--------|------------|------------|
| MASTG-DEMO-0002 | External Storage APIs Tracing with Frida | `pass` | **hit** | `allow_backup, external_storage_write, hardcoded_secrets_review, logging_pii, manifest_debuggable` | external_storage_write (+ logging/secrets) — Frida traces the same storage APIs. |
| MASTG-DEMO-0027 | Runtime Use of KeyguardManager.isDeviceSecure an | `pass` | **hit** | `allow_backup, device_lock_api_check, manifest_debuggable, sdk_int_check` | device_lock_api_check — isDeviceSecure / canAuthenticate inventoried statically. |
| MASTG-DEMO-0030 | Uses of WebViews Allowing Content Access with Fr | `pass` | **hit** | `allow_backup, manifest_debuggable, webview_file_access` | webview_file_access — insecure WebView content/file settings. |
| MASTG-DEMO-0031 | Uses of WebViews Allowing Local File Access with | `pass` | **hit** | `allow_backup, manifest_debuggable, webview_file_access` | webview_file_access — local file access flags. |
| MASTG-DEMO-0038 | Detecting StrictMode Uses with Frida | `pass` | **hit** | `allow_backup, manifest_debuggable, sqlcipher_hardcoded_passphrase, strict_mode_policy` | strict_mode_policy via DEMO-0037 sources. |
| MASTG-DEMO-0058 | Using KeyGenParameterSpec with a Broken ECB Bloc | `pass` | **hit** | `allow_backup, hardcoded_crypto_secret, keystore_no_user_auth, manifest_debuggable, weak_crypto` | weak_crypto (AES/ECB) — Frida only observes. |
| MASTG-DEMO-0059 | Using SharedPreferences to Write Sensitive Data  | `pass` | **hit** | `allow_backup, hardcoded_crypto_secret, keystore_no_user_auth, manifest_debuggable, prefs_plaintext_secret` | prefs_plaintext_secret — plaintext tokens in SharedPreferences. |
| MASTG-DEMO-0060 | App Writing Sensitive Data to Sandbox using Encr | `pass` | **n/a** | `allow_backup, manifest_debuggable` | EncryptedSharedPreferences secure counterpart; prefs_plaintext_secret suppressed. |
| MASTG-DEMO-0072 | Runtime Use of Asymmetric Key Pairs Used For Mul | `pass` | **hit** | `allow_backup, keystore_multipurpose, keystore_no_user_auth, manifest_debuggable, non_random_source` | keystore_multipurpose via DEMO-0071 (sign+encrypt paddings). |
| MASTG-DEMO-0081 | Sensitive User Data Sent to Firebase Analytics w | `pass` | **partial** | `allow_backup, manifest_debuggable, tracker_fingerprint_api` | tracker_fingerprint_api inventories analytics; not event PII payloads. |
| MASTG-DEMO-0082 | WebView WebStorage Cleanup | `pass` | **partial** | `allow_backup, manifest_debuggable, webview_javascript_interface` | webview_javascript_interface related; not WebStorage cleanup. |
| MASTG-DEMO-0088 | Runtime Detection of Root Detection Mechanisms | `pass` | **partial** | `allow_backup, manifest_debuggable, rce_dynamic_loading, root_detection` | rce_dynamic_loading from root-check exec surfaces in 0087. |
| MASTG-DEMO-0106 | Extracting Sensitive Data from Cipher.doFinal vi | `pass` | **hit** | `allow_backup, hardcoded_crypto_secret, keystore_no_user_auth, manifest_debuggable` | hardcoded_crypto_secret — API key + Cipher.doFinal (hookable statically). |
| MASTG-DEMO-0107 | Detecting Frida hooks and terminating the applic | `pass` | **hit** | `allow_backup, anti_frida_maps, hardcoded_crypto_secret, keystore_no_user_auth, manifest_debuggable` | anti_frida_maps — /proc/self/maps + frida/gadget. |
| MASTG-DEMO-0108 | Bypassing Frida Detection in /proc/self/maps to  | `pass` | **hit** | `allow_backup, anti_frida_maps, hardcoded_crypto_secret, keystore_no_user_auth, manifest_debuggable` | Same anti-Frida surface as 0107 (bypass itself is dynamic). |
| MASTG-DEMO-0114 | Detecting Emulator Detection Checks with Frida | `pass` | **hit** | `allow_backup, dangerous_permission, emulator_detection, manifest_debuggable, root_detection, sdk_int_check` | emulator_detection — Build.* + emulator package/string markers. |
| MASTG-DEMO-0139 | Path Traversal via Malicious ContentProvider Fil | `pass` | **partial** | `hardcoded_secrets_review, implicit_intent_launch, implicit_intent_sensitive, manifest_debuggable` | implicit_intent_* on provider flow; path_traversal still weak. |
| MASTG-DEMO-0158 | Runtime Use of WebViewClient URL Loading Handler | `pass` | **hit** | `allow_backup, manifest_debuggable, webview_url_override` | webview_url_override from DEMO-0157 sources. |

### Detector categories for former Frida misses

| Category | Covers |
|----------|--------|
| `device_lock_api_check` | KeyguardManager.isDeviceSecure / BiometricManager.canAuthenticate |
| `strict_mode_policy` | StrictMode.setVmPolicy / setThreadPolicy |
| `prefs_plaintext_secret` | SharedPreferences putString* + secret markers (skips EncryptedSharedPreferences) |
| `keystore_multipurpose` | KeyGenParameterSpec with both signature + encryption paddings |
| `anti_frida_maps` | `/proc/self/maps` + frida/gadget string checks |
| `emulator_detection` | Build.* reads + emulator fingerprint/package markers |
| `hardcoded_crypto_secret` | Secret-like consts co-located with Cipher.doFinal |

## All demos

| Demo | MASVS | Status | Frida | Static | Found | Notes |
|------|-------|--------|:-----:|--------|-------|-------|
| MASTG-DEMO-0089 | MASVS-AUTH | `pass` |  |  | `allow_backup, biometric_without_crypto, logging_pii, manifest_debuggable` | BiometricPrompt with device credential fallback |
| MASTG-DEMO-0090 | MASVS-AUTH | `pass` |  |  | `allow_backup, biometric_without_crypto, hardcoded_crypto_secret, manifest_debuggable` | BiometricPrompt event-bound auth |
| MASTG-DEMO-0091 | MASVS-AUTH | `pass` |  |  | `allow_backup, biometric_without_crypto, hardcoded_crypto_secret, manifest_debuggable` | Shares DEMO-0090 sources (setInvalidatedByBiometricEnrollment) |
| MASTG-DEMO-0092 | MASVS-AUTH | `pass` |  |  | `allow_backup, biometric_without_crypto, hardcoded_crypto_secret, manifest_debuggable` | Shares DEMO-0090 sources |
| MASTG-DEMO-0093 | MASVS-AUTH | `pass` |  |  | `allow_backup, biometric_without_crypto, hardcoded_crypto_secret, manifest_debuggable` | Shares DEMO-0090 sources |
| MASTG-DEMO-0025 | MASVS-CODE | `pass` |  |  | `allow_backup, manifest_debuggable, sdk_int_check` | Build.VERSION.SDK_INT inventory |
| MASTG-DEMO-0050 | MASVS-CODE | `skip` |  |  | `—` | GAP: other demo with no injectable sources (Identifying Insecure Depen |
| MASTG-DEMO-0051 | MASVS-CODE | `skip` |  |  | `—` | GAP: other demo with no injectable sources (Identifying Insecure Depen |
| MASTG-DEMO-0100 | MASVS-CODE | `pass` |  |  | `allow_backup, manifest_debuggable, unsafe_deserialization` | Java Serializable deserialization |
| MASTG-DEMO-0102 | MASVS-CODE | `pass` |  |  | `allow_backup, manifest_debuggable, sql_injection` | SQL injection via ContentProvider |
| MASTG-DEMO-0136 | MASVS-CODE | `pass` |  |  | `exported_custom_action, icc_extra_flow, implicit_intent_sensitive, manifest_debuggable` | Internal activity via implicit Intent |
| MASTG-DEMO-0138 | MASVS-CODE | `pass` |  |  | `exported_custom_action, icc_extra_flow, implicit_intent_sensitive, manifest_debuggable` | Shares DEMO-0136 sources (implicit intent leak) |
| MASTG-DEMO-0139 | MASVS-CODE | `pass` | yes | partial | `hardcoded_secrets_review, implicit_intent_launch, implicit_intent_sensitive, manifest_debuggable` | Path traversal + Frida hooks; intent surface static |
| MASTG-DEMO-0140 | MASVS-CODE | `pass` |  |  | `exported_custom_action, manifest_debuggable` | Attacker activity exported for INTERNAL_ACTION |
| MASTG-DEMO-0141 | MASVS-CODE | `pass` |  |  | `exported_custom_action, manifest_debuggable, uri_permission_setresult_passthrough` | AttackerActivity setResult(getIntent()) URI grant passthrough for path |
| MASTG-DEMO-0156 | MASVS-CODE | `pass` |  |  | `allow_backup, manifest_debuggable, safebrowsing_disabled` | WebSettings.setSafeBrowsingEnabled(false) |
| MASTG-DEMO-0157 | MASVS-CODE | `pass` |  |  | `allow_backup, manifest_debuggable, webview_url_override` | WebViewClient URL loading handlers without host validation |
| MASTG-DEMO-0158 | MASVS-CODE | `pass` | yes | hit | `allow_backup, manifest_debuggable, webview_url_override` | Frida WebViewClient handlers; sources from 0157 |
| MASTG-DEMO-0007 | MASVS-CRYPTO | `pass` |  |  | `allow_backup, insecure_random, manifest_debuggable` | java.util.Random / Math.random for tokens/passwords |
| MASTG-DEMO-0008 | MASVS-CRYPTO | `pass` |  |  | `allow_backup, manifest_debuggable, non_random_source` | Date/Calendar used as token entropy |
| MASTG-DEMO-0012 | MASVS-CRYPTO | `pass` |  |  | `allow_backup, insufficient_key_length, manifest_debuggable` | RSA 1024 + AES 128 key generation (insufficient_key_length) |
| MASTG-DEMO-0017 | MASVS-CRYPTO | `pass` |  |  | `allow_backup, hardcoded_crypto_secret, manifest_debuggable, weak_crypto` | Hardcoded AES key in SecretKeySpec |
| MASTG-DEMO-0022 | MASVS-CRYPTO | `pass` |  |  | `allow_backup, hardcoded_crypto_secret, insecure_random, manifest_debuggable, weak_crypto` | Broken symmetric algorithms (DES/3DES/RC4) |
| MASTG-DEMO-0023 | MASVS-CRYPTO | `pass` |  |  | `allow_backup, hardcoded_crypto_secret, manifest_debuggable, weak_crypto` | Broken encryption modes (AES/ECB) |
| MASTG-DEMO-0058 | MASVS-CRYPTO | `pass` | yes | hit | `allow_backup, hardcoded_crypto_secret, keystore_no_user_auth, manifest_debuggable, weak_crypto` | AES/ECB KeyGenParameterSpec; Frida for observation |
| MASTG-DEMO-0071 | MASVS-CRYPTO | `pass` |  |  | `allow_backup, keystore_multipurpose, keystore_no_user_auth, manifest_debuggable, non_random_source` | RSA key PURPOSE_SIGN/VERIFY/ENCRYPT/DECRYPT |
| MASTG-DEMO-0072 | MASVS-CRYPTO | `pass` | yes | hit | `allow_backup, keystore_multipurpose, keystore_no_user_auth, manifest_debuggable, non_random_source` | Frida runtime of DEMO-0071 multipurpose key |
| MASTG-DEMO-0075 | MASVS-CRYPTO | `pass` |  |  | `allow_backup, explicit_security_provider, hardcoded_crypto_secret, insecure_random, manifest_debuggable, weak_crypto` | Security.addProvider(CustomProvider) |
| MASTG-DEMO-0048 | MASVS-NETWORK | `pass` |  |  | `allow_backup, manifest_debuggable, ssl_socket_no_hostname` | SSLSocket to wrong host without HostnameVerifier |
| MASTG-DEMO-0049 | MASVS-NETWORK | `pass` |  |  | `allow_backup, manifest_debuggable` | Negative: HostnameVerifier blocks wrong host |
| MASTG-DEMO-0054 | MASVS-NETWORK | `pass` |  |  | `allow_backup, manifest_debuggable, ssl_trust_all` | TrustManager that does not validate chains |
| MASTG-DEMO-0055 | MASVS-NETWORK | `pass` |  |  | `allow_backup, manifest_debuggable, ssl_trust_all` | HostnameVerifier that allows any hostname |
| MASTG-DEMO-0056 | MASVS-NETWORK | `pass` |  |  | `allow_backup, manifest_debuggable, ssl_trust_all` | WebView onReceivedSslError → SslErrorHandler.proceed |
| MASTG-DEMO-0057 | MASVS-NETWORK | `pass` |  |  | `allow_backup, manifest_debuggable, network_security_config_user_ca` | networkSecurityConfig trusts user CAs |
| MASTG-DEMO-0029 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, manifest_debuggable, webview_file_access` | WebView content access (semgrep sibling of 0030) |
| MASTG-DEMO-0030 | MASVS-PLATFORM | `pass` | yes | hit | `allow_backup, manifest_debuggable, webview_file_access` | WebView content/file access — Frida exploit path |
| MASTG-DEMO-0031 | MASVS-PLATFORM | `pass` | yes | hit | `allow_backup, manifest_debuggable, webview_file_access` | WebView local file access — Frida exploit path |
| MASTG-DEMO-0032 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, manifest_debuggable, webview_file_access` | WebView local file access (semgrep sibling of 0031) |
| MASTG-DEMO-0040 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, manifest_debuggable` | android:debuggable=true |
| MASTG-DEMO-0061 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, flag_secure, manifest_debuggable` | Window FLAG_SECURE inventory |
| MASTG-DEMO-0062 | MASVS-PLATFORM | `skip` |  |  | `—` | GAP: docs demo with no injectable sources (Enabling Screenshots in Rec |
| MASTG-DEMO-0063 | MASVS-PLATFORM | `skip` |  |  | `—` | GAP: docs demo with no injectable sources (Incorrectly Preventing Scre |
| MASTG-DEMO-0078 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, manifest_debuggable, notification_sensitive` | PII in Notification content |
| MASTG-DEMO-0079 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, compose_password_visible, manifest_debuggable` | SecureTextField with TextObfuscationMode.Visible |
| MASTG-DEMO-0082 | MASVS-PLATFORM | `pass` | yes | partial | `allow_backup, manifest_debuggable, webview_javascript_interface` | WebStorage demo; JS bridge is related static surface |
| MASTG-DEMO-0097 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, manifest_debuggable, webview_javascript_interface` | WebView addJavascriptInterface bridge exposure |
| MASTG-DEMO-0103 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, manifest_debuggable, overlay_protection_api` | setFilterTouchesWhenObscured inventory (mixed protected/unprotected vi |
| MASTG-DEMO-0104 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, implicit_intent_launch, manifest_debuggable, system_alert_window` | SYSTEM_ALERT_WINDOW permission |
| MASTG-DEMO-0105 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, manifest_debuggable, overlay_protection_api, sdk_int_check` | setHideOverlayWindows activity-level protection |
| MASTG-DEMO-0120 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, manifest_debuggable, sqlcipher_hardcoded_passphrase` | Shares DEMO-0121 sources |
| MASTG-DEMO-0121 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, manifest_debuggable, sqlcipher_hardcoded_passphrase` | Exported provider / SQLCipher passphrase patterns |
| MASTG-DEMO-0122 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, manifest_debuggable, path_traversal, uri_permission_setresult_passthrough` | FileProvider unrestricted paths |
| MASTG-DEMO-0123 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, implicit_intent_sensitive, manifest_debuggable` | FileProvider URI grant oversharing (often surfaces as sensitive implic |
| MASTG-DEMO-0128 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, implicit_intent_launch, implicit_intent_sensitive, manifest_debuggable, ui_password_cache` | Sensitive data via unprotected activity |
| MASTG-DEMO-0129 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, implicit_intent_sensitive, manifest_debuggable, prefs_plaintext_secret` | Sensitive action via unprotected service |
| MASTG-DEMO-0130 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, implicit_intent_sensitive, logging_pii, manifest_debuggable, prefs_plaintext_secret` | Unprotected manifest broadcast receiver |
| MASTG-DEMO-0147 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, manifest_debuggable, pending_intent` | Mutable / implicit PendingIntent |
| MASTG-DEMO-0151 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, deeplink_query_unvalidated, implicit_intent_launch, manifest_debuggable` | App link without autoVerify; deep-link query/intent surface |
| MASTG-DEMO-0152 | MASVS-PLATFORM | `pass` |  |  | `allow_backup, deeplink_query_unvalidated, implicit_intent_launch, manifest_debuggable` | Custom scheme handler uses getQueryParameter without validation |
| MASTG-DEMO-0009 | MASVS-PRIVACY | `pass` |  |  | `allow_backup, manifest_debuggable, network_pii` | PII posted via HttpURLConnection |
| MASTG-DEMO-0033 | MASVS-PRIVACY | `pass` |  |  | `allow_backup, dangerous_permission, manifest_debuggable` | Dangerous permissions in manifest (contacts/storage) |
| MASTG-DEMO-0081 | MASVS-PRIVACY | `pass` | yes | partial | `allow_backup, manifest_debuggable, tracker_fingerprint_api` | Firebase Analytics; Frida for event payloads |
| MASTG-DEMO-0027 | MASVS-RESILIENCE | `pass` | yes | hit | `allow_backup, device_lock_api_check, manifest_debuggable, sdk_int_check` | Frida observes isDeviceSecure/canAuthenticate; statically inventoried |
| MASTG-DEMO-0028 | MASVS-RESILIENCE | `pass` |  |  | `allow_backup, device_lock_api_check, manifest_debuggable, sdk_int_check` | KeyguardManager.isDeviceSecure / BiometricManager.canAuthenticate (sem |
| MASTG-DEMO-0037 | MASVS-RESILIENCE | `pass` |  |  | `allow_backup, manifest_debuggable, sqlcipher_hardcoded_passphrase, strict_mode_policy` | StrictMode + leaked SQLite cursor sample |
| MASTG-DEMO-0038 | MASVS-RESILIENCE | `pass` | yes | hit | `allow_backup, manifest_debuggable, sqlcipher_hardcoded_passphrase, strict_mode_policy` | Frida StrictMode demo; shares DEMO-0037 sources |
| MASTG-DEMO-0039 | MASVS-RESILIENCE | `pass` |  |  | `allow_backup, manifest_debuggable, sqlcipher_hardcoded_passphrase, strict_mode_policy` | StrictMode PenaltyLog via DEMO-0037 sources |
| MASTG-DEMO-0087 | MASVS-RESILIENCE | `pass` |  |  | `allow_backup, manifest_debuggable, rce_dynamic_loading, root_detection` | Root detection via Runtime.exec / which su / package checks |
| MASTG-DEMO-0088 | MASVS-RESILIENCE | `pass` | yes | partial | `allow_backup, manifest_debuggable, rce_dynamic_loading, root_detection` | Root detection runtime; static sees exec-style checks from 0087 |
| MASTG-DEMO-0101 | MASVS-RESILIENCE | `pass` |  |  | `allow_backup, hardcoded_crypto_secret, manifest_debuggable, storage_integrity_hmac, weak_crypto` | HMAC prefs integrity with hardcoded Mac key |
| MASTG-DEMO-0106 | MASVS-RESILIENCE | `pass` | yes | hit | `allow_backup, hardcoded_crypto_secret, keystore_no_user_auth, manifest_debuggable` | Frida hooks Cipher.doFinal; static sees hardcoded API key + Cipher |
| MASTG-DEMO-0107 | MASVS-RESILIENCE | `pass` | yes | hit | `allow_backup, anti_frida_maps, hardcoded_crypto_secret, keystore_no_user_auth, manifest_debuggable` | Anti-Frida /proc/self/maps + frida/gadget checks |
| MASTG-DEMO-0108 | MASVS-RESILIENCE | `pass` | yes | hit | `allow_backup, anti_frida_maps, hardcoded_crypto_secret, keystore_no_user_auth, manifest_debuggable` | Bypass demo; static still sees anti-Frida maps from 0107 sources |
| MASTG-DEMO-0114 | MASVS-RESILIENCE | `pass` | yes | hit | `allow_backup, dangerous_permission, emulator_detection, manifest_debuggable, root_detection, sdk_int_check` | Frida traces emulator checks; Build.* + emulator markers static |
| MASTG-DEMO-0115 | MASVS-RESILIENCE | `pass` |  |  | `allow_backup, debugger_check, manifest_debuggable` | Debug.isDebuggerConnected JDWP check |
| MASTG-DEMO-0116 | MASVS-RESILIENCE | `pass` |  |  | `allow_backup, manifest_debuggable, tracerpid_check` | TracerPid /proc/self/status anti-debug |
| MASTG-DEMO-0132 | MASVS-RESILIENCE | `pass` |  |  | `allow_backup, root_detection, sdk_int_check` | Root manager package name checks (magisk/supersu) |
| MASTG-DEMO-0133 | MASVS-RESILIENCE | `pass` |  |  | `allow_backup, manifest_debuggable, native_root_detection` | Native librootcheck.so embeds su path strings |
| MASTG-DEMO-0001 | MASVS-STORAGE | `pass` |  |  | `allow_backup, external_storage_write, hardcoded_secrets_review, logging_pii, manifest_debuggable` | Writes secrets via getExternalFilesDir / MediaStore |
| MASTG-DEMO-0002 | MASVS-STORAGE | `pass` | yes | hit | `allow_backup, external_storage_write, hardcoded_secrets_review, logging_pii, manifest_debuggable` | Frida traces external storage; static incidental logging/secrets (part |
| MASTG-DEMO-0003 | MASVS-STORAGE | `pass` |  |  | `allow_backup, dangerous_permission, external_storage_write, hardcoded_secrets_review, manifest_debuggable` | getExternalStorageDirectory + MANAGE_EXTERNAL_STORAGE |
| MASTG-DEMO-0004 | MASVS-STORAGE | `pass` |  |  | `allow_backup, external_storage_write, hardcoded_secrets_review, manifest_debuggable` | getExternalFilesDir scoped external write |
| MASTG-DEMO-0005 | MASVS-STORAGE | `pass` |  |  | `allow_backup, external_storage_write, logging_pii, manifest_debuggable` | MediaStore EXTERNAL insert of secret file |
| MASTG-DEMO-0006 | MASVS-STORAGE | `pass` |  |  | `allow_backup, logging_pii, manifest_debuggable` | Logging secrets/PII via Log.* |
| MASTG-DEMO-0010 | MASVS-STORAGE | `pass` |  |  | `allow_backup, hardcoded_secrets_review, manifest_debuggable` | Secret written to internal filesDir |
| MASTG-DEMO-0020 | MASVS-STORAGE | `pass` |  |  | `allow_backup, hardcoded_secrets_review, manifest_debuggable` | allowBackup + secrets in filesDir; backup_rules exclude only some file |
| MASTG-DEMO-0034 | MASVS-STORAGE | `pass` |  |  | `allow_backup, hardcoded_secrets_review, manifest_debuggable` | Backup/restore via DEMO-0020 sources (allowBackup + fullBackupContent) |
| MASTG-DEMO-0035 | MASVS-STORAGE | `pass` |  |  | `allow_backup, hardcoded_secrets_review, manifest_debuggable` | backup_rules + adb backup via DEMO-0020 sources |
| MASTG-DEMO-0059 | MASVS-STORAGE | `pass` | yes | hit | `allow_backup, hardcoded_crypto_secret, keystore_no_user_auth, manifest_debuggable, prefs_plaintext_secret` | Plaintext secrets in SharedPreferences (Frida traces putString) |
| MASTG-DEMO-0060 | MASVS-STORAGE | `pass` | yes | n/a | `allow_backup, manifest_debuggable` | Negative/secure EncryptedSharedPreferences counterpart |
| MASTG-DEMO-0064 | MASVS-STORAGE | `pass` |  |  | `allow_backup, manifest_debuggable, ui_password_cache` | Password/PIN EditText without proper inputType |
| MASTG-DEMO-0068 | MASVS-STORAGE | `skip` |  |  | `—` | GAP: docs demo with no injectable sources (Sensitive Data in Unencrypt |
| MASTG-DEMO-0069 | MASVS-STORAGE | `skip` |  |  | `—` | GAP: docs demo with no injectable sources (Sensitive Data Stored Unenc |
| MASTG-DEMO-0070 | MASVS-STORAGE | `skip` |  |  | `—` | GAP: docs demo with no injectable sources (Sensitive Data Stored Unenc |

## Per-demo detail

### MASTG-DEMO-0001 — `pass`

- **Title:** File System Snapshots from External Storage
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['external_storage_write', 'hardcoded_secrets_review', 'logging_pii']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'external_storage_write', 'hardcoded_secrets_review', 'logging_pii', 'manifest_debuggable']`
- **Message:** matched ['external_storage_write', 'hardcoded_secrets_review', 'logging_pii']
- **Notes:** Writes secrets via getExternalFilesDir / MediaStore
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0001.apk`

### MASTG-DEMO-0002 — `pass`

- **Title:** External Storage APIs Tracing with Frida
- **MASVS:** `MASVS-STORAGE`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — external_storage_write (+ logging/secrets) — Frida traces the same storage APIs.
- **Sources:** `local+sibling`
- **expect_any:** `['logging_pii', 'hardcoded_secrets_review']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'external_storage_write', 'hardcoded_secrets_review', 'logging_pii', 'manifest_debuggable']`
- **Message:** matched ['logging_pii', 'hardcoded_secrets_review']
- **Notes:** Frida traces external storage; static incidental logging/secrets (partial lesson)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0002.apk`

### MASTG-DEMO-0003 — `pass`

- **Title:** App Writing to External Storage without Scoped Storage Restrictions
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['external_storage_write', 'dangerous_permission']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'dangerous_permission', 'external_storage_write', 'hardcoded_secrets_review', 'manifest_debuggable']`
- **Message:** matched ['external_storage_write', 'dangerous_permission']
- **Notes:** getExternalStorageDirectory + MANAGE_EXTERNAL_STORAGE
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0003.apk`

### MASTG-DEMO-0004 — `pass`

- **Title:** App Writing to External Storage with Scoped Storage Restrictions
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['external_storage_write']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'external_storage_write', 'hardcoded_secrets_review', 'manifest_debuggable']`
- **Message:** matched ['external_storage_write']
- **Notes:** getExternalFilesDir scoped external write
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0004.apk`

### MASTG-DEMO-0005 — `pass`

- **Title:** App Writing to External Storage via the MediaStore API
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['external_storage_write', 'logging_pii']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'external_storage_write', 'logging_pii', 'manifest_debuggable']`
- **Message:** matched ['external_storage_write', 'logging_pii']
- **Notes:** MediaStore EXTERNAL insert of secret file
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0005.apk`

### MASTG-DEMO-0006 — `pass`

- **Title:** Tracing Common Logging APIs Looking for Secrets
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['logging_pii', 'insecure_logging']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'logging_pii', 'manifest_debuggable']`
- **Message:** matched ['logging_pii']
- **Notes:** Logging secrets/PII via Log.*
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0006.apk`

### MASTG-DEMO-0007 — `pass`

- **Title:** Common Uses of Insecure Random APIs
- **MASVS:** `MASVS-CRYPTO`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['insecure_random']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'insecure_random', 'manifest_debuggable']`
- **Message:** matched ['insecure_random']
- **Notes:** java.util.Random / Math.random for tokens/passwords
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0007.apk`

### MASTG-DEMO-0008 — `pass`

- **Title:** Uses of Non-random Sources
- **MASVS:** `MASVS-CRYPTO`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['non_random_source']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'non_random_source']`
- **Message:** matched ['non_random_source']
- **Notes:** Date/Calendar used as token entropy
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0008.apk`

### MASTG-DEMO-0009 — `pass`

- **Title:** Detecting Undeclared PII in Network Traffic
- **MASVS:** `MASVS-PRIVACY`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['network_pii']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'network_pii']`
- **Message:** matched ['network_pii']
- **Notes:** PII posted via HttpURLConnection
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0009.apk`

### MASTG-DEMO-0010 — `pass`

- **Title:** File System Snapshots from Internal Storage
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['hardcoded_secrets_review']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'hardcoded_secrets_review', 'manifest_debuggable']`
- **Message:** matched ['hardcoded_secrets_review']
- **Notes:** Secret written to internal filesDir
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0010.apk`

### MASTG-DEMO-0012 — `pass`

- **Title:** Cryptographic Key Generation With Insufficient Key Length
- **MASVS:** `MASVS-CRYPTO`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['insufficient_key_length', 'weak_crypto']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'insufficient_key_length', 'manifest_debuggable']`
- **Message:** matched ['insufficient_key_length']
- **Notes:** RSA 1024 + AES 128 key generation (insufficient_key_length)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0012.apk`

### MASTG-DEMO-0017 — `pass`

- **Title:** Use of Hardcoded AES Key in SecretKeySpec with semgrep
- **MASVS:** `MASVS-CRYPTO`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['hardcoded_secrets_review', 'weak_crypto']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'hardcoded_crypto_secret', 'manifest_debuggable', 'weak_crypto']`
- **Message:** matched ['weak_crypto']
- **Notes:** Hardcoded AES key in SecretKeySpec
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0017.apk`

### MASTG-DEMO-0020 — `pass`

- **Title:** Data Exclusion using backup_rules.xml with Backup Manager
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['allow_backup', 'hardcoded_secrets_review']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'hardcoded_secrets_review', 'manifest_debuggable']`
- **Message:** matched ['allow_backup', 'hardcoded_secrets_review']
- **Notes:** allowBackup + secrets in filesDir; backup_rules exclude only some files
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0020.apk`

### MASTG-DEMO-0022 — `pass`

- **Title:** Uses of Broken Symmetric Encryption Algorithms in Cipher with semgrep
- **MASVS:** `MASVS-CRYPTO`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['weak_crypto']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'hardcoded_crypto_secret', 'insecure_random', 'manifest_debuggable', 'weak_crypto']`
- **Message:** matched ['weak_crypto']
- **Notes:** Broken symmetric algorithms (DES/3DES/RC4)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0022.apk`

### MASTG-DEMO-0023 — `pass`

- **Title:** Uses of Broken Encryption Modes in Cipher with semgrep
- **MASVS:** `MASVS-CRYPTO`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['weak_crypto']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'hardcoded_crypto_secret', 'manifest_debuggable', 'weak_crypto']`
- **Message:** matched ['weak_crypto']
- **Notes:** Broken encryption modes (AES/ECB)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0023.apk`

### MASTG-DEMO-0025 — `pass`

- **Title:** Uses of Build.VERSION.SDK_INT with semgrep
- **MASVS:** `MASVS-CODE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['sdk_int_check']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'sdk_int_check']`
- **Message:** matched ['sdk_int_check']
- **Notes:** Build.VERSION.SDK_INT inventory
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0025.apk`

### MASTG-DEMO-0027 — `pass`

- **Title:** Runtime Use of KeyguardManager.isDeviceSecure and BiometricManager.canAuthenticate APIs with Frida
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — device_lock_api_check — isDeviceSecure / canAuthenticate inventoried statically.
- **Sources:** `local+sibling`
- **expect_any:** `['device_lock_api_check']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'device_lock_api_check', 'manifest_debuggable', 'sdk_int_check']`
- **Message:** matched ['device_lock_api_check']
- **Notes:** Frida observes isDeviceSecure/canAuthenticate; statically inventoried
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0027.apk`

### MASTG-DEMO-0028 — `pass`

- **Title:** Uses of KeyguardManager.isDeviceSecure and BiometricManager.canAuthenticate with semgrep
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['device_lock_api_check']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'device_lock_api_check', 'manifest_debuggable', 'sdk_int_check']`
- **Message:** matched ['device_lock_api_check']
- **Notes:** KeyguardManager.isDeviceSecure / BiometricManager.canAuthenticate (semgrep sibling of 0027)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0028.apk`

### MASTG-DEMO-0029 — `pass`

- **Title:** Uses of WebViews Allowing Content Access with semgrep
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['webview_file_access', 'webview_unsafe']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'webview_file_access']`
- **Message:** matched ['webview_file_access']
- **Notes:** WebView content access (semgrep sibling of 0030)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0029.apk`

### MASTG-DEMO-0030 — `pass`

- **Title:** Uses of WebViews Allowing Content Access with Frida
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — webview_file_access — insecure WebView content/file settings.
- **Sources:** `local+sibling`
- **expect_any:** `['webview_file_access', 'webview_unsafe', 'webview_file_access']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'webview_file_access']`
- **Message:** matched ['webview_file_access', 'webview_file_access']
- **Notes:** WebView content/file access — Frida exploit path
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0030.apk`

### MASTG-DEMO-0031 — `pass`

- **Title:** Uses of WebViews Allowing Local File Access with Frida
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — webview_file_access — local file access flags.
- **Sources:** `local+sibling`
- **expect_any:** `['webview_file_access', 'webview_unsafe']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'webview_file_access']`
- **Message:** matched ['webview_file_access']
- **Notes:** WebView local file access — Frida exploit path
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0031.apk`

### MASTG-DEMO-0032 — `pass`

- **Title:** Uses of WebViews Allowing Local File Access with semgrep
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['webview_file_access', 'webview_unsafe']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'webview_file_access']`
- **Message:** matched ['webview_file_access']
- **Notes:** WebView local file access (semgrep sibling of 0031)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0032.apk`

### MASTG-DEMO-0033 — `pass`

- **Title:** Dangerous Permissions in the AndroidManifest with semgrep
- **MASVS:** `MASVS-PRIVACY`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['dangerous_permission']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'dangerous_permission', 'manifest_debuggable']`
- **Message:** matched ['dangerous_permission']
- **Notes:** Dangerous permissions in manifest (contacts/storage)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0033.apk`

### MASTG-DEMO-0034 — `pass`

- **Title:** Backup and Restore App Data with semgrep
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `sibling` ← MASTG-DEMO-0020
- **expect_any:** `['allow_backup']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'hardcoded_secrets_review', 'manifest_debuggable']`
- **Message:** matched ['allow_backup']
- **Notes:** Backup/restore via DEMO-0020 sources (allowBackup + fullBackupContent)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0034.apk`

### MASTG-DEMO-0035 — `pass`

- **Title:** Data Exclusion using backup_rules.xml with adb backup
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `sibling` ← MASTG-DEMO-0020
- **expect_any:** `['allow_backup']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'hardcoded_secrets_review', 'manifest_debuggable']`
- **Message:** matched ['allow_backup']
- **Notes:** backup_rules + adb backup via DEMO-0020 sources
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0035.apk`

### MASTG-DEMO-0037 — `pass`

- **Title:** App Leaking Information about Unclosed SQL Cursor via StrictMode
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['strict_mode_policy']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'sqlcipher_hardcoded_passphrase', 'strict_mode_policy']`
- **Message:** matched ['strict_mode_policy']
- **Notes:** StrictMode + leaked SQLite cursor sample
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0037.apk`

### MASTG-DEMO-0038 — `pass`

- **Title:** Detecting StrictMode Uses with Frida
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — strict_mode_policy via DEMO-0037 sources.
- **Sources:** `sibling` ← MASTG-DEMO-0037
- **expect_any:** `['strict_mode_policy']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'sqlcipher_hardcoded_passphrase', 'strict_mode_policy']`
- **Message:** matched ['strict_mode_policy']
- **Notes:** Frida StrictMode demo; shares DEMO-0037 sources
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0038.apk`

### MASTG-DEMO-0039 — `pass`

- **Title:** Detecting StrictMode PenaltyLog Usage with Semgrep
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** no
- **Sources:** `sibling` ← MASTG-DEMO-0037
- **expect_any:** `['strict_mode_policy']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'sqlcipher_hardcoded_passphrase', 'strict_mode_policy']`
- **Message:** matched ['strict_mode_policy']
- **Notes:** StrictMode PenaltyLog via DEMO-0037 sources
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0039.apk`

### MASTG-DEMO-0040 — `pass`

- **Title:** Debuggable Flag Enabled in the AndroidManifest with semgrep
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['manifest_debuggable']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable']`
- **Message:** matched ['manifest_debuggable']
- **Notes:** android:debuggable=true
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0040.apk`

### MASTG-DEMO-0048 — `pass`

- **Title:** SSLSocket Connection to Wrong Host Server Allowed by Lack of HostnameVerifier
- **MASVS:** `MASVS-NETWORK`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['ssl_socket_no_hostname']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'ssl_socket_no_hostname']`
- **Message:** matched ['ssl_socket_no_hostname']
- **Notes:** SSLSocket to wrong host without HostnameVerifier
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0048.apk`

### MASTG-DEMO-0049 — `pass`

- **Title:** SSLSocket Connection to Wrong Host Server Blocked by HostnameVerifier
- **MASVS:** `MASVS-NETWORK`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `[]`
- **forbid:** `['ssl_trust_all']`
- **Found:** `['allow_backup', 'manifest_debuggable']`
- **Message:** negative demo clean
- **Notes:** Negative: HostnameVerifier blocks wrong host
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0049.apk`

### MASTG-DEMO-0050 — `skip`

- **Title:** Identifying Insecure Dependencies in Android Studio
- **MASVS:** `MASVS-CODE`
- **Frida:** no
- **Sources:** `none`
- **expect_any:** `[]`
- **forbid:** `[]`
- **Found:** `[]`
- **Message:** no APK to scan
- **Notes:** GAP: other demo with no injectable sources (Identifying Insecure Dependencies in Android Studio)
- **APK:** `—`

### MASTG-DEMO-0051 — `skip`

- **Title:** Identifying Insecure Dependencies through SBOM Creation
- **MASVS:** `MASVS-CODE`
- **Frida:** no
- **Sources:** `none`
- **expect_any:** `[]`
- **forbid:** `[]`
- **Found:** `[]`
- **Message:** no APK to scan
- **Notes:** GAP: other demo with no injectable sources (Identifying Insecure Dependencies through SBOM Creation)
- **APK:** `—`

### MASTG-DEMO-0054 — `pass`

- **Title:** Use of a TrustManager that Does Not Validate Certificate Chains
- **MASVS:** `MASVS-NETWORK`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['ssl_trust_all']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'ssl_trust_all']`
- **Message:** matched ['ssl_trust_all']
- **Notes:** TrustManager that does not validate chains
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0054.apk`

### MASTG-DEMO-0055 — `pass`

- **Title:** Use of the HostnameVerifier that Allows Any Hostname
- **MASVS:** `MASVS-NETWORK`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['ssl_trust_all']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'ssl_trust_all']`
- **Message:** matched ['ssl_trust_all']
- **Notes:** HostnameVerifier that allows any hostname
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0055.apk`

### MASTG-DEMO-0056 — `pass`

- **Title:** WebView Ignoring TLS Errors in onReceivedSslError
- **MASVS:** `MASVS-NETWORK`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['ssl_trust_all']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'ssl_trust_all']`
- **Message:** matched ['ssl_trust_all']
- **Notes:** WebView onReceivedSslError → SslErrorHandler.proceed
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0056.apk`

### MASTG-DEMO-0057 — `pass`

- **Title:** Network Security Configuration Allows User-Added Certificates
- **MASVS:** `MASVS-NETWORK`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['network_security_config_user_ca']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'network_security_config_user_ca']`
- **Message:** matched ['network_security_config_user_ca']
- **Notes:** networkSecurityConfig trusts user CAs
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0057.apk`

### MASTG-DEMO-0058 — `pass`

- **Title:** Using KeyGenParameterSpec with a Broken ECB Block Mode
- **MASVS:** `MASVS-CRYPTO`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — weak_crypto (AES/ECB) — Frida only observes.
- **Sources:** `local+sibling`
- **expect_any:** `['weak_crypto']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'hardcoded_crypto_secret', 'keystore_no_user_auth', 'manifest_debuggable', 'weak_crypto']`
- **Message:** matched ['weak_crypto']
- **Notes:** AES/ECB KeyGenParameterSpec; Frida for observation
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0058.apk`

### MASTG-DEMO-0059 — `pass`

- **Title:** Using SharedPreferences to Write Sensitive Data Unencrypted to the App Sandbox
- **MASVS:** `MASVS-STORAGE`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — prefs_plaintext_secret — plaintext tokens in SharedPreferences.
- **Sources:** `local+sibling`
- **expect_any:** `['prefs_plaintext_secret']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'hardcoded_crypto_secret', 'keystore_no_user_auth', 'manifest_debuggable', 'prefs_plaintext_secret']`
- **Message:** matched ['prefs_plaintext_secret']
- **Notes:** Plaintext secrets in SharedPreferences (Frida traces putString)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0059.apk`

### MASTG-DEMO-0060 — `pass`

- **Title:** App Writing Sensitive Data to Sandbox using EncryptedSharedPreferences
- **MASVS:** `MASVS-STORAGE`
- **Frida:** yes
- **Static (Frida lesson):** `n/a` — EncryptedSharedPreferences secure counterpart; prefs_plaintext_secret suppressed.
- **Sources:** `local+sibling`
- **expect_any:** `[]`
- **forbid:** `['prefs_plaintext_secret']`
- **Found:** `['allow_backup', 'manifest_debuggable']`
- **Message:** negative demo clean
- **Notes:** Negative/secure EncryptedSharedPreferences counterpart
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0060.apk`

### MASTG-DEMO-0061 — `pass`

- **Title:** Uses of FLAG_SECURE with semgrep
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['flag_secure']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'flag_secure', 'manifest_debuggable']`
- **Message:** matched ['flag_secure']
- **Notes:** Window FLAG_SECURE inventory
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0061.apk`

### MASTG-DEMO-0062 — `skip`

- **Title:** Enabling Screenshots in Recents via setRecentsScreenshotEnabled with semgrep
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `none`
- **expect_any:** `[]`
- **forbid:** `[]`
- **Found:** `[]`
- **Message:** no APK to scan
- **Notes:** GAP: docs demo with no injectable sources (Enabling Screenshots in Recents via setRecentsScreenshotEnabled with semgrep)
- **APK:** `—`

### MASTG-DEMO-0063 — `skip`

- **Title:** Incorrectly Preventing Screenshots with SecureFlagPolicy in Compose Dialogs with semgrep
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `none`
- **expect_any:** `[]`
- **forbid:** `[]`
- **Found:** `[]`
- **Message:** no APK to scan
- **Notes:** GAP: docs demo with no injectable sources (Incorrectly Preventing Screenshots with SecureFlagPolicy in Compose Dialogs with semgrep)
- **APK:** `—`

### MASTG-DEMO-0064 — `pass`

- **Title:** Uses of Caching UI Elements with semgrep
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['ui_password_cache']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'ui_password_cache']`
- **Message:** matched ['ui_password_cache']
- **Notes:** Password/PIN EditText without proper inputType
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0064.apk`

### MASTG-DEMO-0068 — `skip`

- **Title:** Sensitive Data in Unencrypted SQLite
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `none`
- **expect_any:** `[]`
- **forbid:** `[]`
- **Found:** `[]`
- **Message:** no APK to scan
- **Notes:** GAP: docs demo with no injectable sources (Sensitive Data in Unencrypted SQLite)
- **APK:** `—`

### MASTG-DEMO-0069 — `skip`

- **Title:** Sensitive Data Stored Unencrypted via DataStore
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `none`
- **expect_any:** `[]`
- **forbid:** `[]`
- **Found:** `[]`
- **Message:** no APK to scan
- **Notes:** GAP: docs demo with no injectable sources (Sensitive Data Stored Unencrypted via DataStore)
- **APK:** `—`

### MASTG-DEMO-0070 — `skip`

- **Title:** Sensitive Data Stored Unencrypted via Room Database
- **MASVS:** `MASVS-STORAGE`
- **Frida:** no
- **Sources:** `none`
- **expect_any:** `[]`
- **forbid:** `[]`
- **Found:** `[]`
- **Message:** no APK to scan
- **Notes:** GAP: docs demo with no injectable sources (Sensitive Data Stored Unencrypted via Room Database)
- **APK:** `—`

### MASTG-DEMO-0071 — `pass`

- **Title:** References to Asymmetric Key Pairs Used For Multiple Purposes with Semgrep
- **MASVS:** `MASVS-CRYPTO`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['keystore_multipurpose']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'keystore_multipurpose', 'keystore_no_user_auth', 'manifest_debuggable', 'non_random_source']`
- **Message:** matched ['keystore_multipurpose']
- **Notes:** RSA key PURPOSE_SIGN|VERIFY|ENCRYPT|DECRYPT
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0071.apk`

### MASTG-DEMO-0072 — `pass`

- **Title:** Runtime Use of Asymmetric Key Pairs Used For Multiple Purposes With Frida
- **MASVS:** `MASVS-CRYPTO`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — keystore_multipurpose via DEMO-0071 (sign+encrypt paddings).
- **Sources:** `sibling` ← MASTG-DEMO-0071
- **expect_any:** `['keystore_multipurpose']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'keystore_multipurpose', 'keystore_no_user_auth', 'manifest_debuggable', 'non_random_source']`
- **Message:** matched ['keystore_multipurpose']
- **Notes:** Frida runtime of DEMO-0071 multipurpose key
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0072.apk`

### MASTG-DEMO-0075 — `pass`

- **Title:** Uses of Explicit Security Providers in Cryptographic APIs with semgrep
- **MASVS:** `MASVS-CRYPTO`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['explicit_security_provider']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'explicit_security_provider', 'hardcoded_crypto_secret', 'insecure_random', 'manifest_debuggable', 'weak_crypto']`
- **Message:** matched ['explicit_security_provider']
- **Notes:** Security.addProvider(CustomProvider)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0075.apk`

### MASTG-DEMO-0078 — `pass`

- **Title:** App Leaking Sensitive Data via Notifications
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['notification_sensitive']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'notification_sensitive']`
- **Message:** matched ['notification_sensitive']
- **Notes:** PII in Notification content
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0078.apk`

### MASTG-DEMO-0079 — `pass`

- **Title:** App Exposing Access and Verification Codes in Text Input Fields
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['compose_password_visible']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'compose_password_visible', 'manifest_debuggable']`
- **Message:** matched ['compose_password_visible']
- **Notes:** SecureTextField with TextObfuscationMode.Visible
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0079.apk`

### MASTG-DEMO-0081 — `pass`

- **Title:** Sensitive User Data Sent to Firebase Analytics with Frida
- **MASVS:** `MASVS-PRIVACY`
- **Frida:** yes
- **Static (Frida lesson):** `partial` — tracker_fingerprint_api inventories analytics; not event PII payloads.
- **Sources:** `local+sibling`
- **expect_any:** `['tracker_fingerprint_api']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'tracker_fingerprint_api']`
- **Message:** matched ['tracker_fingerprint_api']
- **Notes:** Firebase Analytics; Frida for event payloads
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0081.apk`

### MASTG-DEMO-0082 — `pass`

- **Title:** WebView WebStorage Cleanup
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** yes
- **Static (Frida lesson):** `partial` — webview_javascript_interface related; not WebStorage cleanup.
- **Sources:** `local+sibling`
- **expect_any:** `['webview_javascript_interface']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'webview_javascript_interface']`
- **Message:** matched ['webview_javascript_interface']
- **Notes:** WebStorage demo; JS bridge is related static surface
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0082.apk`

### MASTG-DEMO-0087 — `pass`

- **Title:** Uses of Root Detection Techniques with Semgrep
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['rce_dynamic_loading', 'rce_process_exec']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'rce_dynamic_loading', 'root_detection']`
- **Message:** matched ['rce_dynamic_loading']
- **Notes:** Root detection via Runtime.exec / which su / package checks
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0087.apk`

### MASTG-DEMO-0088 — `pass`

- **Title:** Runtime Detection of Root Detection Mechanisms
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** yes
- **Static (Frida lesson):** `partial` — rce_dynamic_loading from root-check exec surfaces in 0087.
- **Sources:** `sibling` ← MASTG-DEMO-0087
- **expect_any:** `['rce_dynamic_loading', 'rce_process_exec']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'rce_dynamic_loading', 'root_detection']`
- **Message:** matched ['rce_dynamic_loading']
- **Notes:** Root detection runtime; static sees exec-style checks from 0087
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0088.apk`

### MASTG-DEMO-0089 — `pass`

- **Title:** Uses of BiometricPrompt with Device Credential Fallback with semgrep
- **MASVS:** `MASVS-AUTH`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['biometric_without_crypto', 'keystore_no_user_auth']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'biometric_without_crypto', 'logging_pii', 'manifest_debuggable']`
- **Message:** matched ['biometric_without_crypto']
- **Notes:** BiometricPrompt with device credential fallback
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0089.apk`

### MASTG-DEMO-0090 — `pass`

- **Title:** Uses of BiometricPrompt with Event-Bound Authentication with semgrep
- **MASVS:** `MASVS-AUTH`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['biometric_without_crypto']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'biometric_without_crypto', 'hardcoded_crypto_secret', 'manifest_debuggable']`
- **Message:** matched ['biometric_without_crypto']
- **Notes:** BiometricPrompt event-bound auth
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0090.apk`

### MASTG-DEMO-0091 — `pass`

- **Title:** Uses of setInvalidatedByBiometricEnrollment with semgrep
- **MASVS:** `MASVS-AUTH`
- **Frida:** no
- **Sources:** `sibling` ← MASTG-DEMO-0090
- **expect_any:** `['biometric_without_crypto', 'keystore_no_user_auth']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'biometric_without_crypto', 'hardcoded_crypto_secret', 'manifest_debuggable']`
- **Message:** matched ['biometric_without_crypto']
- **Notes:** Shares DEMO-0090 sources (setInvalidatedByBiometricEnrollment)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0091.apk`

### MASTG-DEMO-0092 — `pass`

- **Title:** Uses of BiometricPrompt without Explicit User Confirmation with semgrep
- **MASVS:** `MASVS-AUTH`
- **Frida:** no
- **Sources:** `sibling` ← MASTG-DEMO-0090
- **expect_any:** `['biometric_without_crypto']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'biometric_without_crypto', 'hardcoded_crypto_secret', 'manifest_debuggable']`
- **Message:** matched ['biometric_without_crypto']
- **Notes:** Shares DEMO-0090 sources
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0092.apk`

### MASTG-DEMO-0093 — `pass`

- **Title:** Uses of Extended Validity Duration in setUserAuthenticationParameters with semgrep
- **MASVS:** `MASVS-AUTH`
- **Frida:** no
- **Sources:** `sibling` ← MASTG-DEMO-0090
- **expect_any:** `['biometric_without_crypto', 'keystore_no_user_auth']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'biometric_without_crypto', 'hardcoded_crypto_secret', 'manifest_debuggable']`
- **Message:** matched ['biometric_without_crypto']
- **Notes:** Shares DEMO-0090 sources
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0093.apk`

### MASTG-DEMO-0097 — `pass`

- **Title:** Sensitive Data and Functionality Exposed Through WebView JavaScript Bridges
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['webview_javascript_interface']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'webview_javascript_interface']`
- **Message:** matched ['webview_javascript_interface']
- **Notes:** WebView addJavascriptInterface bridge exposure
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0097.apk`

### MASTG-DEMO-0100 — `pass`

- **Title:** Object Deserialization Using Serializable with semgrep
- **MASVS:** `MASVS-CODE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['unsafe_deserialization']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'unsafe_deserialization']`
- **Message:** matched ['unsafe_deserialization']
- **Notes:** Java Serializable deserialization
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0100.apk`

### MASTG-DEMO-0101 — `pass`

- **Title:** References to Storage Integrity Check APIs with semgrep
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['storage_integrity_hmac', 'hardcoded_crypto_secret']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'hardcoded_crypto_secret', 'manifest_debuggable', 'storage_integrity_hmac', 'weak_crypto']`
- **Message:** matched ['storage_integrity_hmac', 'hardcoded_crypto_secret']
- **Notes:** HMAC prefs integrity with hardcoded Mac key
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0101.apk`

### MASTG-DEMO-0102 — `pass`

- **Title:** SQL Injection via URI Path and Selection in Android Content Providers
- **MASVS:** `MASVS-CODE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['provider_sql_injection', 'sql_injection', 'room_sql_injection']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'sql_injection']`
- **Message:** matched ['sql_injection']
- **Notes:** SQL injection via ContentProvider
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0102.apk`

### MASTG-DEMO-0103 — `pass`

- **Title:** Missing Overlay Protection on a Sensitive View
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['overlay_protection_api']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'overlay_protection_api']`
- **Message:** matched ['overlay_protection_api']
- **Notes:** setFilterTouchesWhenObscured inventory (mixed protected/unprotected views)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0103.apk`

### MASTG-DEMO-0104 — `pass`

- **Title:** App Requesting SYSTEM_ALERT_WINDOW Permission
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['system_alert_window']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'implicit_intent_launch', 'manifest_debuggable', 'system_alert_window']`
- **Message:** matched ['system_alert_window']
- **Notes:** SYSTEM_ALERT_WINDOW permission
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0104.apk`

### MASTG-DEMO-0105 — `pass`

- **Title:** Activity-Level Overlay Protection Using setHideOverlayWindows
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['overlay_protection_api']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'overlay_protection_api', 'sdk_int_check']`
- **Message:** matched ['overlay_protection_api']
- **Notes:** setHideOverlayWindows activity-level protection
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0105.apk`

### MASTG-DEMO-0106 — `pass`

- **Title:** Extracting Sensitive Data from Cipher.doFinal via Frida Hooking
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — hardcoded_crypto_secret — API key + Cipher.doFinal (hookable statically).
- **Sources:** `local+sibling`
- **expect_any:** `['hardcoded_crypto_secret']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'hardcoded_crypto_secret', 'keystore_no_user_auth', 'manifest_debuggable']`
- **Message:** matched ['hardcoded_crypto_secret']
- **Notes:** Frida hooks Cipher.doFinal; static sees hardcoded API key + Cipher
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0106.apk`

### MASTG-DEMO-0107 — `pass`

- **Title:** Detecting Frida hooks and terminating the application on response
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — anti_frida_maps — /proc/self/maps + frida/gadget.
- **Sources:** `local+sibling`
- **expect_any:** `['anti_frida_maps', 'hardcoded_crypto_secret']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'anti_frida_maps', 'hardcoded_crypto_secret', 'keystore_no_user_auth', 'manifest_debuggable']`
- **Message:** matched ['anti_frida_maps', 'hardcoded_crypto_secret']
- **Notes:** Anti-Frida /proc/self/maps + frida/gadget checks
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0107.apk`

### MASTG-DEMO-0108 — `pass`

- **Title:** Bypassing Frida Detection in /proc/self/maps to Extract Sensitive Data
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — Same anti-Frida surface as 0107 (bypass itself is dynamic).
- **Sources:** `sibling` ← MASTG-DEMO-0107
- **expect_any:** `['anti_frida_maps', 'hardcoded_crypto_secret']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'anti_frida_maps', 'hardcoded_crypto_secret', 'keystore_no_user_auth', 'manifest_debuggable']`
- **Message:** matched ['anti_frida_maps', 'hardcoded_crypto_secret']
- **Notes:** Bypass demo; static still sees anti-Frida maps from 0107 sources
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0108.apk`

### MASTG-DEMO-0114 — `pass`

- **Title:** Detecting Emulator Detection Checks with Frida
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — emulator_detection — Build.* + emulator package/string markers.
- **Sources:** `local+sibling`
- **expect_any:** `['emulator_detection']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'dangerous_permission', 'emulator_detection', 'manifest_debuggable', 'root_detection', 'sdk_int_check']`
- **Message:** matched ['emulator_detection']
- **Notes:** Frida traces emulator checks; Build.* + emulator markers static
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0114.apk`

### MASTG-DEMO-0115 — `pass`

- **Title:** JDWP Debugging Checks in App Code
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['debugger_check']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'debugger_check', 'manifest_debuggable']`
- **Message:** matched ['debugger_check']
- **Notes:** Debug.isDebuggerConnected JDWP check
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0115.apk`

### MASTG-DEMO-0116 — `pass`

- **Title:** Native Anti-Debugging Checks with TracerPid and ptrace
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['tracerpid_check']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'tracerpid_check']`
- **Message:** matched ['tracerpid_check']
- **Notes:** TracerPid /proc/self/status anti-debug
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0116.apk`

### MASTG-DEMO-0120 — `pass`

- **Title:** Uses of Unauthorized Access to Exported Content Providers
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `sibling` ← MASTG-DEMO-0121
- **expect_any:** `['provider_sql_injection', 'sql_injection', 'sqlcipher_hardcoded_passphrase']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'sqlcipher_hardcoded_passphrase']`
- **Message:** matched ['sqlcipher_hardcoded_passphrase']
- **Notes:** Shares DEMO-0121 sources
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0120.apk`

### MASTG-DEMO-0121 — `pass`

- **Title:** Unauthorized Access to Database Records through Exported Content Provider
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['provider_sql_injection', 'sql_injection', 'icc_extra_flow', 'sqlcipher_hardcoded_passphrase']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'sqlcipher_hardcoded_passphrase']`
- **Message:** matched ['sqlcipher_hardcoded_passphrase']
- **Notes:** Exported provider / SQLCipher passphrase patterns
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0121.apk`

### MASTG-DEMO-0122 — `pass`

- **Title:** Oversharing via FileProvider with Unrestricted Path Configuration
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['path_traversal', 'provider_path_traversal', 'uri_permission_grant_flow']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'path_traversal', 'uri_permission_setresult_passthrough']`
- **Message:** matched ['path_traversal']
- **Notes:** FileProvider unrestricted paths
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0122.apk`

### MASTG-DEMO-0123 — `pass`

- **Title:** Exfiltration of Private Files via FileProvider URI Grant Oversharing
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['uri_permission_grant_flow', 'path_traversal', 'provider_path_traversal', 'implicit_intent_sensitive', 'implicit_intent_launch']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'implicit_intent_sensitive', 'manifest_debuggable']`
- **Message:** matched ['implicit_intent_sensitive']
- **Notes:** FileProvider URI grant oversharing (often surfaces as sensitive implicit Intent)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0123.apk`

### MASTG-DEMO-0128 — `pass`

- **Title:** Sensitive Data Exposed Through an Unprotected Activity
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['implicit_intent_launch', 'implicit_intent_sensitive', 'intent_spoofing', 'icc_extra_flow']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'implicit_intent_launch', 'implicit_intent_sensitive', 'manifest_debuggable', 'ui_password_cache']`
- **Message:** matched ['implicit_intent_launch', 'implicit_intent_sensitive']
- **Notes:** Sensitive data via unprotected activity
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0128.apk`

### MASTG-DEMO-0129 — `pass`

- **Title:** Sensitive Action Exposed Through an Unprotected Service
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['implicit_intent_launch', 'implicit_intent_sensitive', 'command_receiver', 'icc_extra_flow']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'implicit_intent_sensitive', 'manifest_debuggable', 'prefs_plaintext_secret']`
- **Message:** matched ['implicit_intent_sensitive']
- **Notes:** Sensitive action via unprotected service
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0129.apk`

### MASTG-DEMO-0130 — `pass`

- **Title:** Sensitive Action Exposed Through an Unprotected Manifest-Declared Broadcast Receiver
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['sensitive_broadcast', 'credential_broadcast', 'command_receiver', 'sticky_ordered_broadcast', 'implicit_intent_sensitive', 'logging_pii']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'implicit_intent_sensitive', 'logging_pii', 'manifest_debuggable', 'prefs_plaintext_secret']`
- **Message:** matched ['implicit_intent_sensitive', 'logging_pii']
- **Notes:** Unprotected manifest broadcast receiver
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0130.apk`

### MASTG-DEMO-0132 — `pass`

- **Title:** Root Detection Logic in Java/Kotlin Layer Only Protected by Identifier Renaming
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['root_detection']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'root_detection', 'sdk_int_check']`
- **Message:** matched ['root_detection']
- **Notes:** Root manager package name checks (magisk/supersu)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0132.apk`

### MASTG-DEMO-0133 — `pass`

- **Title:** Root Detection Logic in Native Layer with Insufficient Obfuscation
- **MASVS:** `MASVS-RESILIENCE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['native_root_detection', 'root_detection']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'native_root_detection']`
- **Message:** matched ['native_root_detection']
- **Notes:** Native librootcheck.so embeds su path strings
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0133.apk`

### MASTG-DEMO-0136 — `pass`

- **Title:** Internal Activity Communication via Implicit Intent
- **MASVS:** `MASVS-CODE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['implicit_intent_launch', 'implicit_intent_sensitive', 'intent_spoofing']`
- **forbid:** `[]`
- **Found:** `['exported_custom_action', 'icc_extra_flow', 'implicit_intent_sensitive', 'manifest_debuggable']`
- **Message:** matched ['implicit_intent_sensitive']
- **Notes:** Internal activity via implicit Intent
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0136.apk`

### MASTG-DEMO-0138 — `pass`

- **Title:** Leaking Sensitive Information via Implicit Intents
- **MASVS:** `MASVS-CODE`
- **Frida:** no
- **Sources:** `sibling` ← MASTG-DEMO-0136
- **expect_any:** `['implicit_intent_launch', 'implicit_intent_sensitive', 'icc_extra_flow']`
- **forbid:** `[]`
- **Found:** `['exported_custom_action', 'icc_extra_flow', 'implicit_intent_sensitive', 'manifest_debuggable']`
- **Message:** matched ['implicit_intent_sensitive', 'icc_extra_flow']
- **Notes:** Shares DEMO-0136 sources (implicit intent leak)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0138.apk`

### MASTG-DEMO-0139 — `pass`

- **Title:** Path Traversal via Malicious ContentProvider Filename
- **MASVS:** `MASVS-CODE`
- **Frida:** yes
- **Static (Frida lesson):** `partial` — implicit_intent_* on provider flow; path_traversal still weak.
- **Sources:** `local+sibling`
- **expect_any:** `['path_traversal', 'provider_path_traversal', 'implicit_intent_launch', 'implicit_intent_sensitive']`
- **forbid:** `[]`
- **Found:** `['hardcoded_secrets_review', 'implicit_intent_launch', 'implicit_intent_sensitive', 'manifest_debuggable']`
- **Message:** matched ['implicit_intent_launch', 'implicit_intent_sensitive']
- **Notes:** Path traversal + Frida hooks; intent surface static
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0139.apk`

### MASTG-DEMO-0140 — `pass`

- **Title:** Attacker App Registering for Internal Implicit Intent
- **MASVS:** `MASVS-CODE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['exported_custom_action']`
- **forbid:** `[]`
- **Found:** `['exported_custom_action', 'manifest_debuggable']`
- **Message:** matched ['exported_custom_action']
- **Notes:** Attacker activity exported for INTERNAL_ACTION
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0140.apk`

### MASTG-DEMO-0141 — `pass`

- **Title:** Attacker App Returning Malicious ContentProvider Filename
- **MASVS:** `MASVS-CODE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['uri_permission_setresult_passthrough']`
- **forbid:** `[]`
- **Found:** `['exported_custom_action', 'manifest_debuggable', 'uri_permission_setresult_passthrough']`
- **Message:** matched ['uri_permission_setresult_passthrough']
- **Notes:** AttackerActivity setResult(getIntent()) URI grant passthrough for path-traversal provider
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0141.apk`

### MASTG-DEMO-0147 — `pass`

- **Title:** Uses of Insecure PendingIntent
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['pending_intent']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'pending_intent']`
- **Message:** matched ['pending_intent']
- **Notes:** Mutable / implicit PendingIntent
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0147.apk`

### MASTG-DEMO-0151 — `pass`

- **Title:** Deep Link Intent Filter Missing android:autoVerify with semgrep
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['deeplink_query_unvalidated', 'implicit_intent_launch']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'deeplink_query_unvalidated', 'implicit_intent_launch', 'manifest_debuggable']`
- **Message:** matched ['deeplink_query_unvalidated', 'implicit_intent_launch']
- **Notes:** App link without autoVerify; deep-link query/intent surface
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0151.apk`

### MASTG-DEMO-0152 — `pass`

- **Title:** Custom URL Scheme Handler Without Input Validation with semgrep
- **MASVS:** `MASVS-PLATFORM`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['deeplink_query_unvalidated', 'implicit_intent_launch']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'deeplink_query_unvalidated', 'implicit_intent_launch', 'manifest_debuggable']`
- **Message:** matched ['deeplink_query_unvalidated', 'implicit_intent_launch']
- **Notes:** Custom scheme handler uses getQueryParameter without validation
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0152.apk`

### MASTG-DEMO-0156 — `pass`

- **Title:** SafeBrowsing Disabled Detection with semgrep
- **MASVS:** `MASVS-CODE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['safebrowsing_disabled']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'safebrowsing_disabled']`
- **Message:** matched ['safebrowsing_disabled']
- **Notes:** WebSettings.setSafeBrowsingEnabled(false)
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0156.apk`

### MASTG-DEMO-0157 — `pass`

- **Title:** Uses of WebViewClient URL Loading Handlers with semgrep
- **MASVS:** `MASVS-CODE`
- **Frida:** no
- **Sources:** `local+sibling`
- **expect_any:** `['webview_url_override', 'webview_unsafe', 'webview_unsafe_url', 'webview_weak_host_check']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'webview_url_override']`
- **Message:** matched ['webview_url_override']
- **Notes:** WebViewClient URL loading handlers without host validation
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0157.apk`

### MASTG-DEMO-0158 — `pass`

- **Title:** Runtime Use of WebViewClient URL Loading Handlers with Frida
- **MASVS:** `MASVS-CODE`
- **Frida:** yes
- **Static (Frida lesson):** `hit` — webview_url_override from DEMO-0157 sources.
- **Sources:** `sibling` ← MASTG-DEMO-0157
- **expect_any:** `['webview_url_override', 'webview_unsafe', 'webview_unsafe_url', 'webview_weak_host_check']`
- **forbid:** `[]`
- **Found:** `['allow_backup', 'manifest_debuggable', 'webview_url_override']`
- **Message:** matched ['webview_url_override']
- **Notes:** Frida WebViewClient handlers; sources from 0157
- **APK:** `/Users/toto/Code/androguard/androguard/workspace/mastg-validation/apks/MASTG-DEMO-0158.apk`

## Reproduce

```bash
python scripts/mastg_validate.py --setup
python scripts/mastg_validate.py
python scripts/mastg_validate.py --scan-only
python scripts/mastg_coverage_doc.py
```

