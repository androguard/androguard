from __future__ import division
from __future__ import print_function

from future import standard_library
standard_library.install_aliases()
from builtins import chr
from builtins import str
from builtins import range
from builtins import object
from androguard.core import bytecode
from androguard.core import androconf
from androguard.core.bytecodes.dvm_permissions import DVM_PERMISSIONS
from androguard.util import read

from androguard.core.resources import public

import io
from struct import pack, unpack
from xml.sax.saxutils import escape
from zlib import crc32
import re
import collections
import sys
import binascii

from xml.dom import minidom

# Used for reading Certificates
from pyasn1.codec.der.decoder import decode
from pyasn1.codec.der.encoder import encode
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

NS_ANDROID_URI = 'http://schemas.android.com/apk/res/android'

# 0: chilkat
# 1: default python zipfile module
# 2: patch zipfile module
ZIPMODULE = 1

if sys.hexversion < 0x2070000:
    try:
        import chilkat
        ZIPMODULE = 0
        # UNLOCK : change it with your valid key !
        try:
            CHILKAT_KEY = read("key.txt")
        except Exception:
            CHILKAT_KEY = "testme"

    except ImportError:
        ZIPMODULE = 1
else:
    ZIPMODULE = 1


################################################### CHILKAT ZIP FORMAT #####################################################
class ChilkatZip(object):

    def __init__(self, raw):
        self.files = []
        self.zip = chilkat.CkZip()

        self.zip.UnlockComponent(CHILKAT_KEY)

        self.zip.OpenFromMemory(raw, len(raw))

        filename = chilkat.CkString()
        e = self.zip.FirstEntry()
        while e is not None:
            e.get_FileName(filename)
            self.files.append(filename.getString())
            e = e.NextEntry()

    def delete(self, patterns):
        el = []

        filename = chilkat.CkString()
        e = self.zip.FirstEntry()
        while e is not None:
            e.get_FileName(filename)

            if re.match(patterns, filename.getString()) != None:
                el.append(e)
            e = e.NextEntry()

        for i in el:
            self.zip.DeleteEntry(i)

    def remplace_file(self, filename, buff):
        entry = self.zip.GetEntryByName(filename)
        if entry is not None:
            obj = chilkat.CkByteData()
            obj.append2(buff, len(buff))
            return entry.ReplaceData(obj)
        return False

    def write(self):
        obj = chilkat.CkByteData()
        self.zip.WriteToMemory(obj)
        return obj.getBytes()

    def namelist(self):
        return self.files

    def read(self, elem):
        e = self.zip.GetEntryByName(elem)
        s = chilkat.CkByteData()

        e.Inflate(s)
        return s.getBytes()


def sign_apk(filename, keystore, storepass):
    from subprocess import Popen, PIPE, STDOUT
    compile = Popen([androconf.CONF["PATH_JARSIGNER"], "-sigalg", "MD5withRSA",
                     "-digestalg", "SHA1", "-storepass", storepass, "-keystore",
                     keystore, filename, "alias_name"],
                    stdout=PIPE,
                    stderr=STDOUT)
    stdout, stderr = compile.communicate()


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class FileNotPresent(Error):
    pass


######################################################## APK FORMAT ########################################################
class APK(object):
    """
        This class can access to all elements in an APK file

        :param filename: specify the path of the file, or raw data
        :param raw: specify if the filename is a path or raw data (optional)
        :param mode: specify the mode to open the file (optional)
        :param magic_file: specify the magic file (optional)
        :param zipmodule: specify the type of zip module to use (0:chilkat, 1:zipfile, 2:patch zipfile)

        :type filename: string
        :type raw: boolean
        :type mode: string
        :type magic_file: string
        :type zipmodule: int

        :Example:
          APK("myfile.apk")
          APK(read("myfile.apk"), raw=True)
    """

    def __init__(self,
                 filename,
                 raw=False,
                 mode="r",
                 magic_file=None,
                 zipmodule=ZIPMODULE,
                 skip_analysis=False):
        self.filename = filename

        self.xml = {}
        self.axml = {}
        self.arsc = {}

        self.package = ""
        self.androidversion = {}
        self.permissions = []
        self.declared_permissions = {}
        self.valid_apk = False

        self.files = {}
        self.files_crc32 = {}

        self.magic_file = magic_file

        if raw is True:
            self.__raw = bytearray(filename)
        else:
            self.__raw = bytearray(read(filename))

        self.zipmodule = zipmodule

        if zipmodule == 0:
            self.zip = ChilkatZip(self.__raw)
        elif zipmodule == 2:
            from androguard.patch import zipfile
            self.zip = zipfile.ZipFile(io.BytesIO(self.__raw), mode=mode)
        else:
            import zipfile
            self.zip = zipfile.ZipFile(io.BytesIO(self.__raw), mode=mode)

        if not skip_analysis:
            for i in self.zip.namelist():
                if i == "AndroidManifest.xml":
                    self.axml[i] = AXMLPrinter(self.zip.read(i))
                    try:
                        self.xml[i] = minidom.parseString(self.axml[i].get_buff())
                    except:
                        self.xml[i] = None

                    if self.xml[i] != None:
                        self.package = self.xml[i].documentElement.getAttribute(
                            "package")
                        self.androidversion[
                            "Code"
                        ] = self.xml[i].documentElement.getAttributeNS(
                            NS_ANDROID_URI, "versionCode")
                        self.androidversion[
                            "Name"
                        ] = self.xml[i].documentElement.getAttributeNS(
                            NS_ANDROID_URI, "versionName")

                        for item in self.xml[i].getElementsByTagName('uses-permission'):
                            self.permissions.append(str(item.getAttributeNS(
                                NS_ANDROID_URI, "name")))

                        # getting details of the declared permissions
                        for d_perm_item in self.xml[i].getElementsByTagName('permission'):
                            d_perm_name = self._get_res_string_value(str(
                                d_perm_item.getAttributeNS(NS_ANDROID_URI, "name")))
                            d_perm_label = self._get_res_string_value(str(
                                d_perm_item.getAttributeNS(NS_ANDROID_URI,
                                                           "label")))
                            d_perm_description = self._get_res_string_value(str(
                                d_perm_item.getAttributeNS(NS_ANDROID_URI,
                                                           "description")))
                            d_perm_permissionGroup = self._get_res_string_value(str(
                                d_perm_item.getAttributeNS(NS_ANDROID_URI,
                                                           "permissionGroup")))
                            d_perm_protectionLevel = self._get_res_string_value(str(
                                d_perm_item.getAttributeNS(NS_ANDROID_URI,
                                                           "protectionLevel")))

                            d_perm_details = {
                                "label": d_perm_label,
                                "description": d_perm_description,
                                "permissionGroup": d_perm_permissionGroup,
                                "protectionLevel": d_perm_protectionLevel,
                            }
                            self.declared_permissions[d_perm_name] = d_perm_details

                        self.valid_apk = True

            self.get_files_types()
            self.permission_module = androconf.load_api_specific_resource_module(
                "aosp_permissions", self.get_target_sdk_version())

    def _get_res_string_value(self, string):
        if not string.startswith('@string/'):
            return string
        string_key = string[9:]

        res_parser = self.get_android_resources()
        string_value = ''
        for package_name in res_parser.get_packages_names():
            extracted_values = res_parser.get_string(package_name, string_key)
            if extracted_values:
                string_value = extracted_values[1]
                break
        return string_value

    def get_AndroidManifest(self):
        """
            Return the Android Manifest XML file

            :rtype: xml object
        """
        return self.xml["AndroidManifest.xml"]

    def is_valid_APK(self):
        """
            Return true if the APK is valid, false otherwise

            :rtype: boolean
        """
        return self.valid_apk

    def get_filename(self):
        """
            Return the filename of the APK

            :rtype: string
        """
        return self.filename

    def get_app_name(self):
        """
            Return the appname of the APK

            :rtype: string
        """
        main_activity_name = self.get_main_activity()

        app_name = self.get_element('activity', 'label', name=main_activity_name)
        if not app_name:
            app_name = self.get_element('application', 'label')

        if app_name.startswith("@"):
            res_id = int(app_name[1:], 16)
            res_parser = self.get_android_resources()

            try:
                app_name = res_parser.get_resolved_res_configs(
                    res_id,
                    ARSCResTableConfig.default_config())[0][1]
            except Exception as e:
                androconf.warning("Exception selecting app name: %s" % e)
                app_name = ""
        return app_name

    def get_app_icon(self, max_dpi=65536):
        """
            Return the first non-greater density than max_dpi icon file name,
            unless exact icon resolution is set in the manifest, in which case
            return the exact file

            :rtype: string
        """
        main_activity_name = self.get_main_activity()

        app_icon = self.get_element('activity', 'icon', name=main_activity_name)

        if not app_icon:
            app_icon = self.get_element('application', 'icon')

        if not app_icon:
            res_id = self.get_android_resources().get_res_id_by_key(self.package, 'mipmap', 'ic_launcher')
            if res_id:
                app_icon = "@%x" % res_id

        if not app_icon:
            res_id = self.get_android_resources().get_res_id_by_key(self.package, 'drawable', 'ic_launcher')
            if res_id:
                app_icon = "@%x" % res_id

        if not app_icon:
            # If the icon can not be found, return now
            return None

        if app_icon.startswith("@"):
            res_id = int(app_icon[1:], 16)
            res_parser = self.get_android_resources()
            candidates = res_parser.get_resolved_res_configs(res_id)

            app_icon = None
            current_dpi = -1

            try:
                for config, file_name in candidates:
                    dpi = config.get_density()
                    if current_dpi < dpi <= max_dpi:
                        app_icon = file_name
                        current_dpi = dpi
            except Exception as e:
                androconf.warning("Exception selecting app icon: %s" % e)

        return app_icon

    def get_package(self):
        """
            Return the name of the package

            :rtype: string
        """
        return self.package

    def get_androidversion_code(self):
        """
            Return the android version code

            :rtype: string
        """
        return self.androidversion["Code"]

    def get_androidversion_name(self):
        """
            Return the android version name

            :rtype: string
        """
        return self.androidversion["Name"]

    def get_files(self):
        """
            Return the files inside the APK

            :rtype: a list of strings
        """
        return self.zip.namelist()

    def get_files_types(self):
        """
            Return the files inside the APK with their associated types (by using python-magic)

            :rtype: a dictionnary
        """
        try:
            import magic
        except ImportError:
            # no lib magic !
            for i in self.get_files():
                buffer = self.zip.read(i)
                self.files_crc32[i] = crc32(buffer)
                self.files[i] = "Unknown"
            return self.files

        if self.files != {}:
            return self.files

        builtin_magic = 0
        filemagic = 0
        try:
            getattr(magic, "MagicException")
        except AttributeError:
            try:
                getattr(magic.Magic, "id_buffer")
                filemagic = 1
            except AttributeError:
                builtin_magic = 1

        if builtin_magic:
            ms = magic.open(magic.MAGIC_NONE)
            ms.load()

            for i in self.get_files():
                buffer = self.zip.read(i)
                self.files[i] = ms.buffer(buffer)
                if self.files[i] is None:
                    self.files[i] = "Unknown"
                else:
                    self.files[i] = self._patch_magic(buffer, self.files[i])
                self.files_crc32[i] = crc32(buffer)
        elif filemagic:
            if self.magic_file is not None:
                m = magic.Magic(paths=[self.magic_file])
            else:
                m = magic.Magic()
            for i in self.get_files():
                buffer = self.zip.read(i)
                self.files[i] = m.id_buffer(buffer)
                if self.files[i] is None:
                    self.files[i] = "Unknown"
                else:
                    self.files[i] = self._patch_magic(buffer, self.files[i])
                self.files_crc32[i] = crc32(buffer)
        else:
            m = magic.Magic(magic_file=self.magic_file)
            for i in self.get_files():
                buffer = self.zip.read(i)
                self.files[i] = m.from_buffer(buffer)
                if self.files[i] is None:
                    self.files[i] = "Unknown"
                else:
                    self.files[i] = self._patch_magic(buffer, self.files[i])
                self.files_crc32[i] = crc32(buffer)

        return self.files

    def _patch_magic(self, buffer, orig):
        if ("Zip" in orig) or ("DBase" in orig):
            val = androconf.is_android_raw(buffer)
            if val == "APK":
                return "Android application package file"
            elif val == "AXML":
                return "Android's binary XML"

        return orig

    def get_files_crc32(self):
        if self.files_crc32 == {}:
            self.get_files_types()

        return self.files_crc32

    def get_files_information(self):
        """
            Return the files inside the APK with their associated types and crc32

            :rtype: string, string, int
        """
        if self.files == {}:
            self.get_files_types()

        for i in self.get_files():
            try:
                yield i, self.files[i], self.files_crc32[i]
            except KeyError:
                yield i, "", ""

    def get_raw(self):
        """
            Return raw bytes of the APK

            :rtype: string
        """
        return self.__raw

    def get_file(self, filename):
        """
            Return the raw data of the specified filename

            :rtype: string
        """
        try:
            return self.zip.read(filename)
        except KeyError:
            raise FileNotPresent(filename)

    def get_dex(self):
        """
            Return the raw data of the classes dex file

            :rtype: a string
        """
        try:
            return self.get_file("classes.dex")
        except FileNotPresent:
            return ""

    def get_all_dex(self):
        """
            Return the raw data of all classes dex files

            :rtype: a generator
        """
        try:
            yield self.get_file("classes.dex")

            # Multidex support
            basename = "classes%d.dex"
            for i in range(2, sys.maxsize):
                yield self.get_file(basename % i)
        except FileNotPresent:
            pass

    def get_elements(self, tag_name, attribute):
        """
            Return elements in xml files which match with the tag name and the specific attribute

            :param tag_name: a string which specify the tag name
            :param attribute: a string which specify the attribute
        """
        l = []
        for i in self.xml:
            for item in self.xml[i].getElementsByTagName(tag_name):
                value = item.getAttributeNS(NS_ANDROID_URI, attribute)
                value = self.format_value(value)

                l.append(str(value))
        return l

    def format_value(self, value):
        if len(value) > 0:
            if value[0] == ".":
                value = self.package + value
            else:
                v_dot = value.find(".")
                if v_dot == 0:
                    value = self.package + "." + value
                elif v_dot == -1:
                    value = self.package + "." + value
        return value

    def get_element(self, tag_name, attribute, **attribute_filter):
        """
            Return element in xml files which match with the tag name and the specific attribute

            :param tag_name: specify the tag name
            :type tag_name: string
            :param attribute: specify the attribute
            :type attribute: string

            :rtype: string
        """
        for i in self.xml:
            if self.xml[i] is None :
                continue
            tag = self.xml[i].getElementsByTagName(tag_name)
            if tag is None:
                return None
            for item in tag:
                skip_this_item = False
                for attr, val in list(attribute_filter.items()):
                    attr_val = item.getAttributeNS(NS_ANDROID_URI, attr)
                    if attr_val != val:
                        skip_this_item = True
                        break

                if skip_this_item:
                    continue

                value = item.getAttributeNS(NS_ANDROID_URI, attribute)

                if len(value) > 0:
                    return value
        return None

    def get_main_activity(self):
        """
            Return the name of the main activity

            :rtype: string
        """
        x = set()
        y = set()

        for i in self.xml:
            activities_and_aliases = self.xml[i].getElementsByTagName("activity") + \
                                     self.xml[i].getElementsByTagName("activity-alias")

            for item in activities_and_aliases:
                # Some applications have more than one MAIN activity.
                # For example: paid and free content
                activityEnabled = item.getAttributeNS(NS_ANDROID_URI, "enabled")
                if activityEnabled is not None and activityEnabled != "" and activityEnabled == "false":
                    continue

                for sitem in item.getElementsByTagName("action"):
                    val = sitem.getAttributeNS(NS_ANDROID_URI, "name")
                    if val == "android.intent.action.MAIN":
                        x.add(item.getAttributeNS(NS_ANDROID_URI, "name"))

                for sitem in item.getElementsByTagName("category"):
                    val = sitem.getAttributeNS(NS_ANDROID_URI, "name")
                    if val == "android.intent.category.LAUNCHER":
                        y.add(item.getAttributeNS(NS_ANDROID_URI, "name"))

        z = x.intersection(y)
        if len(z) > 0:
            return self.format_value(z.pop())
        return None

    def get_activities(self):
        """
            Return the android:name attribute of all activities

            :rtype: a list of string
        """
        return self.get_elements("activity", "name")

    def get_services(self):
        """
            Return the android:name attribute of all services

            :rtype: a list of string
        """
        return self.get_elements("service", "name")

    def get_receivers(self):
        """
            Return the android:name attribute of all receivers

            :rtype: a list of string
        """
        return self.get_elements("receiver", "name")

    def get_providers(self):
        """
            Return the android:name attribute of all providers

            :rtype: a list of string
        """
        return self.get_elements("provider", "name")

    def get_intent_filters(self, category, name):
        d = {}

        d["action"] = []
        d["category"] = []

        for i in self.xml:
            for item in self.xml[i].getElementsByTagName(category):
                if self.format_value(
                        item.getAttributeNS(NS_ANDROID_URI, "name")
                        ) == name:
                    for sitem in item.getElementsByTagName("intent-filter"):
                        for ssitem in sitem.getElementsByTagName("action"):
                            if ssitem.getAttributeNS(NS_ANDROID_URI, "name") \
                                    not in d["action"]:
                                d["action"].append(ssitem.getAttributeNS(
                                    NS_ANDROID_URI, "name"))
                        for ssitem in sitem.getElementsByTagName("category"):
                            if ssitem.getAttributeNS(NS_ANDROID_URI, "name") \
                                    not in d["category"]:
                                d["category"].append(ssitem.getAttributeNS(
                                    NS_ANDROID_URI, "name"))

        if not d["action"]:
            del d["action"]

        if not d["category"]:
            del d["category"]

        return d

    def get_permissions(self):
        """
            Return permissions

            :rtype: list of string
        """
        return self.permissions

    def get_details_permissions(self):
        """
            Return permissions with details

            :rtype: list of string
        """
        l = {}

        for i in self.permissions:
            perm = i
            pos = i.rfind(".")

            if pos != -1:
                perm = i[pos + 1:]

            try:
                l[i] = DVM_PERMISSIONS["MANIFEST_PERMISSION"][perm]
            except KeyError:
                l[i] = ["normal", "Unknown permission from android reference",
                        "Unknown permission from android reference"]

        return l

    def get_requested_permissions(self):
        """
            Returns all requested permissions.

            :rtype: list of strings
        """
        return self.permissions

    def get_requested_aosp_permissions(self):
        '''
            Returns requested permissions declared within AOSP project.

            :rtype: list of strings
        '''
        aosp_permissions = []
        all_permissions = self.get_requested_permissions()
        for perm in all_permissions:
            if perm in list(self.permission_module["AOSP_PERMISSIONS"].keys()):
                aosp_permissions.append(perm)
        return aosp_permissions

    def get_requested_aosp_permissions_details(self):
        """
            Returns requested aosp permissions with details.

            :rtype: dictionary
        """
        l = {}
        for i in self.permissions:
            try:
                l[i] = self.permission_module["AOSP_PERMISSIONS"][i]
            except KeyError:
                # if we have not found permission do nothing
                continue
        return l

    def get_requested_third_party_permissions(self):
        '''
            Returns list of requested permissions not declared within AOSP project.

            :rtype: list of strings
        '''
        third_party_permissions = []
        all_permissions = self.get_requested_permissions()
        for perm in all_permissions:
            if perm not in list(self.permission_module["AOSP_PERMISSIONS"].keys()):
                third_party_permissions.append(perm)
        return third_party_permissions

    def get_declared_permissions(self):
        '''
            Returns list of the declared permissions.

            :rtype: list of strings
        '''
        return list(self.declared_permissions.keys())

    def get_declared_permissions_details(self):
        '''
            Returns declared permissions with the details.

            :rtype: dict
        '''
        return self.declared_permissions

    def get_max_sdk_version(self):
        """
            Return the android:maxSdkVersion attribute

            :rtype: string
        """
        return self.get_element("uses-sdk", "maxSdkVersion")

    def get_min_sdk_version(self):
        """
            Return the android:minSdkVersion attribute

            :rtype: string
        """
        return self.get_element("uses-sdk", "minSdkVersion")

    def get_target_sdk_version(self):
        """
            Return the android:targetSdkVersion attribute

            :rtype: string
        """
        return self.get_element("uses-sdk", "targetSdkVersion")

    def get_libraries(self):
        """
            Return the android:name attributes for libraries

            :rtype: list
        """
        return self.get_elements("uses-library", "name")

    def get_certificate(self, filename):
        """
            Return a certificate object by giving the name in the apk file
        """
        pkcs7message = self.get_file(filename)

        message, _ = decode(pkcs7message)
        cert = encode(message[1][3])
        # Remove the first identifier
        # byte 0 == identifier, skip
        # byte 1 == length. If byte1 & 0x80 > 1, we have long format
        #                   The length of to read bytes is then coded
        #                   in byte1 & 0x7F
        cert = cert[2 + (cert[1] & 0x7F) if cert[1] & 0x80 > 1 else 2:]
    
        certificate = x509.load_der_x509_certificate(cert, default_backend())
    
        return certificate

    def new_zip(self, filename, deleted_files=None, new_files={}):
        """
            Create a new zip file

            :param filename: the output filename of the zip
            :param deleted_files: a regex pattern to remove specific file
            :param new_files: a dictionnary of new files

            :type filename: string
            :type deleted_files: None or a string
            :type new_files: a dictionnary (key:filename, value:content of the file)
        """
        if self.zipmodule == 2:
            from androguard.patch import zipfile
            zout = zipfile.ZipFile(filename, 'w')
        else:
            import zipfile
            zout = zipfile.ZipFile(filename, 'w')

        for item in self.zip.infolist():
            if deleted_files is not None:
                if re.match(deleted_files, item.filename) == None:
                    if item.filename in new_files:
                        zout.writestr(item, new_files[item.filename])
                    else:
                        buffer = self.zip.read(item.filename)
                        zout.writestr(item, buffer)
        zout.close()

    def get_android_manifest_axml(self):
        """
            Return the :class:`AXMLPrinter` object which corresponds to the AndroidManifest.xml file

            :rtype: :class:`AXMLPrinter`
        """
        try:
            return self.axml["AndroidManifest.xml"]
        except KeyError:
            return None

    def get_android_manifest_xml(self):
        """
            Return the xml object which corresponds to the AndroidManifest.xml file

            :rtype: object
        """
        try:
            return self.xml["AndroidManifest.xml"]
        except KeyError:
            return None

    def get_android_resources(self):
        """
            Return the :class:`ARSCParser` object which corresponds to the resources.arsc file

            :rtype: :class:`ARSCParser`
        """
        try:
            return self.arsc["resources.arsc"]
        except KeyError:
            self.arsc["resources.arsc"] = ARSCParser(self.zip.read(
                "resources.arsc"))
            return self.arsc["resources.arsc"]

    def get_signature_name(self):
        """
            Return the name of the first signature file found.
        """
        return self.get_signature_names()[0]

    def get_signature_names(self):
        """
             Return a list of the signature file names.
        """
        signature_expr = re.compile("^(META-INF/)(.*)(\.RSA|\.EC|\.DSA)$")
        signatures = []

        for i in self.get_files():
            if signature_expr.search(i):
                signatures.append(i)

        if len(signatures) > 0:
            return signatures

        return None

    def get_signature(self):
        """
            Return the data of the first signature file found.
        """
        return self.get_signatures()[0]

    def get_signatures(self):
        """
            Return a list of the data of the signature files.
        """
        signature_expr = re.compile("^(META-INF/)(.*)(\.RSA|\.EC|\.DSA)$")
        signature_datas = []

        for i in self.get_files():
            if signature_expr.search(i):
                signature_datas.append(self.get_file(i))

        if len(signature_datas) > 0:
            return signature_datas

        return None

    def show(self):
        self.get_files_types()

        print("FILES: ")
        for i in self.get_files():
            try:
                print("\t", i, self.files[i], "%x" % self.files_crc32[i])
            except KeyError:
                print("\t", i, "%x" % self.files_crc32[i])

        print("DECLARED PERMISSIONS:")
        declared_permissions = self.get_declared_permissions()
        for i in declared_permissions:
            print("\t", i)

        print("REQUESTED PERMISSIONS:")
        requested_permissions = self.get_requested_permissions()
        for i in requested_permissions:
            print("\t", i)

        print("MAIN ACTIVITY: ", self.get_main_activity())

        print("ACTIVITIES: ")
        activities = self.get_activities()
        for i in activities:
            filters = self.get_intent_filters("activity", i)
            print("\t", i, filters or "")

        print("SERVICES: ")
        services = self.get_services()
        for i in services:
            filters = self.get_intent_filters("service", i)
            print("\t", i, filters or "")

        print("RECEIVERS: ")
        receivers = self.get_receivers()
        for i in receivers:
            filters = self.get_intent_filters("receiver", i)
            print("\t", i, filters or "")

        print("PROVIDERS: ", self.get_providers())

        print("CERTIFICATES:")
        for c in self.get_signature_names():
            show_Certificate(self.get_certificate(c))


def get_Name(name, short=False):
    """
        Return the distinguished name of an X509 Certificate
        
        :param name: Name object to return the DN from
        :param short: Use short form (Default: False)

        :type name: :class:`cryptography.x509.Name`
        :type short: Boolean

        :rtype: str
    """
    
    # For the shortform, we have a lookup table
    # See RFC4514 for more details
    sf = {
          "countryName": "C",
          "stateOrProvinceName": "ST",
          "localityName": "L",
          "organizationalUnitName": "OU",
          "organizationName": "O",
          "commonName": "CN",
          "emailAddress": "E",
         }
    return ", ".join(["{}={}".format(attr.oid._name if not short or attr.oid._name not in sf else sf[attr.oid._name], attr.value) for attr in name])
    
    
def show_Certificate(cert, short=False):
    """
        Print Fingerprints, Issuer and Subject of an X509 Certificate.

        :param cert: X509 Certificate to print
        :param short: Print in shortform for DN (Default: False)

        :type cert: :class:`cryptography.x509.Certificate`
        :type short: Boolean
    """
    
    for h in [hashes.MD5, hashes.SHA1, hashes.SHA256, hashes.SHA512]:
        print("{}: {}".format(h.name, binascii.hexlify(cert.fingerprint(h())).decode("ascii")))
    print("Issuer: {}".format(get_Name(cert.issuer, short=short)))
    print("Subject: {}".format(get_Name(cert.subject, short=short)))

################################## AXML FORMAT ########################################
# Translated from
# http://code.google.com/p/android4me/source/browse/src/android/content/res/AXmlResourceParser.java

UTF8_FLAG = 0x00000100
CHUNK_STRINGPOOL_TYPE = 0x001C0001
CHUNK_NULL_TYPE = 0x00000000


class StringBlock(object):

    def __init__(self, buff):
        self.start = buff.get_idx()
        self._cache = {}
        self.header_size, self.header = self.skipNullPadding(buff)

        self.chunkSize = unpack('<i', buff.read(4))[0]
        self.stringCount = unpack('<i', buff.read(4))[0]
        self.styleOffsetCount = unpack('<i', buff.read(4))[0]

        self.flags = unpack('<i', buff.read(4))[0]
        self.m_isUTF8 = ((self.flags & UTF8_FLAG) != 0)

        self.stringsOffset = unpack('<i', buff.read(4))[0]
        self.stylesOffset = unpack('<i', buff.read(4))[0]

        self.m_stringOffsets = []
        self.m_styleOffsets = []
        self.m_charbuff = ""
        self.m_styles = []

        for i in range(0, self.stringCount):
            self.m_stringOffsets.append(unpack('<i', buff.read(4))[0])

        for i in range(0, self.styleOffsetCount):
            self.m_styleOffsets.append(unpack('<i', buff.read(4))[0])

        size = self.chunkSize - self.stringsOffset
        if self.stylesOffset != 0:
            size = self.stylesOffset - self.stringsOffset

        # FIXME
        if (size % 4) != 0:
            androconf.warning("ooo")

        self.m_charbuff = buff.read(size)

        if self.stylesOffset != 0:
            size = self.chunkSize - self.stylesOffset

            # FIXME
            if (size % 4) != 0:
                androconf.warning("ooo")

            for i in range(0, size // 4):
                self.m_styles.append(unpack('<i', buff.read(4))[0])

    def skipNullPadding(self, buff):

        def readNext(buff, first_run=True):
            header = unpack('<i', buff.read(4))[0]

            if header == CHUNK_NULL_TYPE and first_run:
                androconf.info("Skipping null padding in StringBlock header")
                header = readNext(buff, first_run=False)
            elif header != CHUNK_STRINGPOOL_TYPE:
                androconf.warning("Invalid StringBlock header")

            return header

        header = readNext(buff)
        return header >> 8, header & 0xFF

    def getString(self, idx):
        if idx in self._cache:
            return self._cache[idx]

        if idx < 0 or not self.m_stringOffsets or idx >= len(
                self.m_stringOffsets):
            return ""

        offset = self.m_stringOffsets[idx]

        if self.m_isUTF8:
            self._cache[idx] = self.decode8(offset)
        else:
            self._cache[idx] = self.decode16(offset)

        return self._cache[idx]

    def getStyle(self, idx):
        # FIXME
        return self.m_styles[idx]

    def decode8(self, offset):
        str_len, skip = self.decodeLength(offset, 1)
        offset += skip

        encoded_bytes, skip = self.decodeLength(offset, 1)
        offset += skip

        data = self.m_charbuff[offset: offset + encoded_bytes]

        return self.decode_bytes(data, 'utf-8', str_len)

    def decode16(self, offset):
        str_len, skip = self.decodeLength(offset, 2)
        offset += skip

        encoded_bytes = str_len * 2

        data = self.m_charbuff[offset: offset + encoded_bytes]

        return self.decode_bytes(data, 'utf-16', str_len)

    def decode_bytes(self, data, encoding, str_len):
        string = data.decode(encoding, 'replace')
        if len(string) != str_len:
            androconf.warning("invalid decoded string length")
        return string

    def decodeLength(self, offset, sizeof_char):
        length = self.m_charbuff[offset]

        sizeof_2chars = sizeof_char << 1
        fmt_chr = 'B' if sizeof_char == 1 else 'H'
        fmt = "<2" + fmt_chr

        length1, length2 = unpack(fmt, self.m_charbuff[offset:(offset + sizeof_2chars)])

        highbit = 0x80 << (8 * (sizeof_char - 1))

        if (length & highbit) != 0:
            return ((length1 & ~highbit) << (8 * sizeof_char)) | length2, sizeof_2chars
        else:
            return length1, sizeof_char

    def show(self):
        print("StringBlock(%x, %x, %x, %x, %x, %x" % (
            self.start,
            self.header,
            self.header_size,
            self.chunkSize,
            self.stringsOffset,
            self.flags))
        for i in range(0, len(self.m_stringOffsets)):
            print(i, repr(self.getString(i)))


ATTRIBUTE_IX_NAMESPACE_URI = 0
ATTRIBUTE_IX_NAME = 1
ATTRIBUTE_IX_VALUE_STRING = 2
ATTRIBUTE_IX_VALUE_TYPE = 3
ATTRIBUTE_IX_VALUE_DATA = 4
ATTRIBUTE_LENGHT = 5

CHUNK_AXML_FILE = 0x00080003
CHUNK_RESOURCEIDS = 0x00080180
CHUNK_XML_FIRST = 0x00100100
CHUNK_XML_START_NAMESPACE = 0x00100100
CHUNK_XML_END_NAMESPACE = 0x00100101
CHUNK_XML_START_TAG = 0x00100102
CHUNK_XML_END_TAG = 0x00100103
CHUNK_XML_TEXT = 0x00100104
CHUNK_XML_LAST = 0x00100104

START_DOCUMENT = 0
END_DOCUMENT = 1
START_TAG = 2
END_TAG = 3
TEXT = 4


class AXMLParser(object):

    def __init__(self, raw_buff):
        self.reset()

        self.valid_axml = True
        self.buff = bytecode.BuffHandle(raw_buff)

        axml_file = unpack('<L', self.buff.read(4))[0]

        if axml_file == CHUNK_AXML_FILE:
            self.buff.read(4)

            self.sb = StringBlock(self.buff)

            self.m_resourceIDs = []
            self.m_prefixuri = {}
            self.m_uriprefix = {}
            self.m_prefixuriL = []

            self.visited_ns = []
        else:
            self.valid_axml = False
            androconf.warning("Not a valid xml file")

    def is_valid(self):
        return self.valid_axml

    def reset(self):
        self.m_event = -1
        self.m_lineNumber = -1
        self.m_name = -1
        self.m_namespaceUri = -1
        self.m_attributes = []
        self.m_idAttribute = -1
        self.m_classAttribute = -1
        self.m_styleAttribute = -1

    def __next__(self):
        self.doNext()
        return self.m_event

    def doNext(self):
        if self.m_event == END_DOCUMENT:
            return

        event = self.m_event

        self.reset()
        while True:
            chunkType = -1

            # Fake END_DOCUMENT event.
            if event == END_TAG:
                pass

            # START_DOCUMENT
            if event == START_DOCUMENT:
                chunkType = CHUNK_XML_START_TAG
            else:
                if self.buff.end():
                    self.m_event = END_DOCUMENT
                    break
                chunkType = unpack('<L', self.buff.read(4))[0]

            if chunkType == CHUNK_RESOURCEIDS:
                chunkSize = unpack('<L', self.buff.read(4))[0]
                # FIXME
                if chunkSize < 8 or chunkSize % 4 != 0:
                    androconf.warning("Invalid chunk size")

                for i in range(0, (chunkSize // 4) - 2):
                    self.m_resourceIDs.append(
                        unpack('<L', self.buff.read(4))[0])

                continue

            # FIXME
            if chunkType < CHUNK_XML_FIRST or chunkType > CHUNK_XML_LAST:
                androconf.warning("invalid chunk type")

            # Fake START_DOCUMENT event.
            if chunkType == CHUNK_XML_START_TAG and event == -1:
                self.m_event = START_DOCUMENT
                break

            self.buff.read(4)  # /*chunkSize*/
            lineNumber = unpack('<L', self.buff.read(4))[0]
            self.buff.read(4)  # 0xFFFFFFFF

            if chunkType == CHUNK_XML_START_NAMESPACE or chunkType == CHUNK_XML_END_NAMESPACE:
                if chunkType == CHUNK_XML_START_NAMESPACE:
                    prefix = unpack('<L', self.buff.read(4))[0]
                    uri = unpack('<L', self.buff.read(4))[0]

                    self.m_prefixuri[prefix] = uri
                    self.m_uriprefix[uri] = prefix
                    self.m_prefixuriL.append((prefix, uri))
                    self.ns = uri
                else:
                    self.ns = -1
                    self.buff.read(4)
                    self.buff.read(4)
                    (prefix, uri) = self.m_prefixuriL.pop()

                continue

            self.m_lineNumber = lineNumber

            if chunkType == CHUNK_XML_START_TAG:
                self.m_namespaceUri = unpack('<L', self.buff.read(4))[0]
                self.m_name = unpack('<L', self.buff.read(4))[0]

                # FIXME
                self.buff.read(4)  # flags

                attributeCount = unpack('<L', self.buff.read(4))[0]
                self.m_idAttribute = (attributeCount >> 16) - 1
                attributeCount = attributeCount & 0xFFFF
                self.m_classAttribute = unpack('<L', self.buff.read(4))[0]
                self.m_styleAttribute = (self.m_classAttribute >> 16) - 1

                self.m_classAttribute = (self.m_classAttribute & 0xFFFF) - 1

                for i in range(0, attributeCount * ATTRIBUTE_LENGHT):
                    self.m_attributes.append(unpack('<L', self.buff.read(4))[0])

                for i in range(ATTRIBUTE_IX_VALUE_TYPE, len(self.m_attributes),
                               ATTRIBUTE_LENGHT):
                    self.m_attributes[i] = self.m_attributes[i] >> 24

                self.m_event = START_TAG
                break

            if chunkType == CHUNK_XML_END_TAG:
                self.m_namespaceUri = unpack('<L', self.buff.read(4))[0]
                self.m_name = unpack('<L', self.buff.read(4))[0]
                self.m_event = END_TAG
                break

            if chunkType == CHUNK_XML_TEXT:
                self.m_name = unpack('<L', self.buff.read(4))[0]

                # FIXME
                self.buff.read(4)
                self.buff.read(4)

                self.m_event = TEXT
                break

    def getPrefixByUri(self, uri):
        try:
            return self.m_uriprefix[uri]
        except KeyError:
            return -1

    def getPrefix(self):
        try:
            return self.sb.getString(self.m_uriprefix[self.m_namespaceUri])
        except KeyError:
            return u''

    def getName(self):
        if self.m_name == -1 or (self.m_event != START_TAG and
                                     self.m_event != END_TAG):
            return u''

        return self.sb.getString(self.m_name)

    def getText(self):
        if self.m_name == -1 or self.m_event != TEXT:
            return u''

        return self.sb.getString(self.m_name)

    def getNamespacePrefix(self, pos):
        prefix = self.m_prefixuriL[pos][0]
        return self.sb.getString(prefix)

    def getNamespaceUri(self, pos):
        uri = self.m_prefixuriL[pos][1]
        return self.sb.getString(uri)

    def getXMLNS(self):
        buff = ""
        for i in self.m_uriprefix:
            if i not in self.visited_ns:
                buff += "xmlns:%s=\"%s\"\n" % (
                    self.sb.getString(self.m_uriprefix[i]),
                    self.sb.getString(self.m_prefixuri[self.m_uriprefix[i]]))
                self.visited_ns.append(i)
        return buff

    def getNamespaceCount(self, pos):
        pass

    def getAttributeOffset(self, index):
        # FIXME
        if self.m_event != START_TAG:
            androconf.warning("Current event is not START_TAG.")

        offset = index * 5
        # FIXME
        if offset >= len(self.m_attributes):
            androconf.warning("Invalid attribute index")

        return offset

    def getAttributeCount(self):
        if self.m_event != START_TAG:
            return -1

        return len(self.m_attributes) // ATTRIBUTE_LENGHT

    def getAttributePrefix(self, index):
        offset = self.getAttributeOffset(index)
        uri = self.m_attributes[offset + ATTRIBUTE_IX_NAMESPACE_URI]

        prefix = self.getPrefixByUri(uri)

        if prefix == -1:
            return ""

        return self.sb.getString(prefix)

    def getAttributeName(self, index):
        offset = self.getAttributeOffset(index)
        name = self.m_attributes[offset + ATTRIBUTE_IX_NAME]

        if name == -1:
            return ""

        res = self.sb.getString(name)
        if not res:
            attr = self.m_resourceIDs[name]
            if attr in public.SYSTEM_RESOURCES['attributes']['inverse']:
                res = 'android:' + public.SYSTEM_RESOURCES['attributes']['inverse'][
                    attr
                ]

        return res

    def getAttributeValueType(self, index):
        offset = self.getAttributeOffset(index)
        return self.m_attributes[offset + ATTRIBUTE_IX_VALUE_TYPE]

    def getAttributeValueData(self, index):
        offset = self.getAttributeOffset(index)
        return self.m_attributes[offset + ATTRIBUTE_IX_VALUE_DATA]

    def getAttributeValue(self, index):
        offset = self.getAttributeOffset(index)
        valueType = self.m_attributes[offset + ATTRIBUTE_IX_VALUE_TYPE]
        if valueType == TYPE_STRING:
            valueString = self.m_attributes[offset + ATTRIBUTE_IX_VALUE_STRING]
            return self.sb.getString(valueString)
        # WIP
        return ""


TYPE_ATTRIBUTE = 2
TYPE_DIMENSION = 5
TYPE_FIRST_COLOR_INT = 28
TYPE_FIRST_INT = 16
TYPE_FLOAT = 4
TYPE_FRACTION = 6
TYPE_INT_BOOLEAN = 18
TYPE_INT_COLOR_ARGB4 = 30
TYPE_INT_COLOR_ARGB8 = 28
TYPE_INT_COLOR_RGB4 = 31
TYPE_INT_COLOR_RGB8 = 29
TYPE_INT_DEC = 16
TYPE_INT_HEX = 17
TYPE_LAST_COLOR_INT = 31
TYPE_LAST_INT = 31
TYPE_NULL = 0
TYPE_REFERENCE = 1
TYPE_STRING = 3

TYPE_TABLE = {
    TYPE_ATTRIBUTE: "attribute",
    TYPE_DIMENSION: "dimension",
    TYPE_FLOAT: "float",
    TYPE_FRACTION: "fraction",
    TYPE_INT_BOOLEAN: "int_boolean",
    TYPE_INT_COLOR_ARGB4: "int_color_argb4",
    TYPE_INT_COLOR_ARGB8: "int_color_argb8",
    TYPE_INT_COLOR_RGB4: "int_color_rgb4",
    TYPE_INT_COLOR_RGB8: "int_color_rgb8",
    TYPE_INT_DEC: "int_dec",
    TYPE_INT_HEX: "int_hex",
    TYPE_NULL: "null",
    TYPE_REFERENCE: "reference",
    TYPE_STRING: "string",
}

RADIX_MULTS = [0.00390625, 3.051758E-005, 1.192093E-007, 4.656613E-010]
DIMENSION_UNITS = ["px", "dip", "sp", "pt", "in", "mm"]
FRACTION_UNITS = ["%", "%p"]

COMPLEX_UNIT_MASK = 15


def complexToFloat(xcomplex):
    return (float)(xcomplex & 0xFFFFFF00) * RADIX_MULTS[(xcomplex >> 4) & 3]


def getPackage(id):
    if id >> 24 == 1:
        return "android:"
    return ""


def format_value(_type, _data, lookup_string=lambda ix: "<string>"):
    if _type == TYPE_STRING:
        return lookup_string(_data)

    elif _type == TYPE_ATTRIBUTE:
        return "?%s%08X" % (getPackage(_data), _data)

    elif _type == TYPE_REFERENCE:
        return "@%s%08X" % (getPackage(_data), _data)

    elif _type == TYPE_FLOAT:
        return "%f" % unpack("=f", pack("=L", _data))[0]

    elif _type == TYPE_INT_HEX:
        return "0x%08X" % _data

    elif _type == TYPE_INT_BOOLEAN:
        if _data == 0:
            return "false"
        return "true"

    elif _type == TYPE_DIMENSION:
        return "%f%s" % (complexToFloat(_data), DIMENSION_UNITS[_data & COMPLEX_UNIT_MASK])

    elif _type == TYPE_FRACTION:
        return "%f%s" % (complexToFloat(_data) * 100, FRACTION_UNITS[_data & COMPLEX_UNIT_MASK])

    elif _type >= TYPE_FIRST_COLOR_INT and _type <= TYPE_LAST_COLOR_INT:
        return "#%08X" % _data

    elif _type >= TYPE_FIRST_INT and _type <= TYPE_LAST_INT:
        return "%d" % androconf.long2int(_data)

    return "<0x%X, type 0x%02X>" % (_data, _type)


class AXMLPrinter(object):

    def __init__(self, raw_buff):
        self.axml = AXMLParser(raw_buff)
        self.xmlns = False

        self.buff = u''

        while True and self.axml.is_valid():
            _type = next(self.axml)

            if _type == START_DOCUMENT:
                self.buff += u'<?xml version="1.0" encoding="utf-8"?>\n'
            elif _type == START_TAG:
                self.buff += u'<' + self.getPrefix(self.axml.getPrefix(
                )) + self.axml.getName() + u'\n'
                self.buff += self.axml.getXMLNS()

                for i in range(0, self.axml.getAttributeCount()):
                    self.buff += "%s%s=\"%s\"\n" % (
                        self.getPrefix(
                            self.axml.getAttributePrefix(i)),
                        self.axml.getAttributeName(i),
                        self._escape(self.getAttributeValue(i)))

                self.buff += u'>\n'

            elif _type == END_TAG:
                self.buff += "</%s%s>\n" % (
                    self.getPrefix(self.axml.getPrefix()), self.axml.getName())

            elif _type == TEXT:
                self.buff += "%s\n" % self.axml.getText()

            elif _type == END_DOCUMENT:
                break

    # pleed patch
    def _escape(self, s):
        s = s.replace("&", "&amp;")
        s = s.replace('"', "&quot;")
        s = s.replace("'", "&apos;")
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        return escape(s)

    def get_buff(self):
        return self.buff.encode('utf-8')

    def get_xml(self):
        return minidom.parseString(self.get_buff()).toprettyxml(
            encoding="utf-8")

    def get_xml_obj(self):
        return minidom.parseString(self.get_buff())

    def getPrefix(self, prefix):
        if prefix is None or len(prefix) == 0:
            return u''

        return prefix + u':'

    def getAttributeValue(self, index):
        _type = self.axml.getAttributeValueType(index)
        _data = self.axml.getAttributeValueData(index)

        return format_value(_type, _data, lambda _: self.axml.getAttributeValue(index))


RES_NULL_TYPE = 0x0000
RES_STRING_POOL_TYPE = 0x0001
RES_TABLE_TYPE = 0x0002
RES_XML_TYPE = 0x0003

# Chunk types in RES_XML_TYPE
RES_XML_FIRST_CHUNK_TYPE = 0x0100
RES_XML_START_NAMESPACE_TYPE = 0x0100
RES_XML_END_NAMESPACE_TYPE = 0x0101
RES_XML_START_ELEMENT_TYPE = 0x0102
RES_XML_END_ELEMENT_TYPE = 0x0103
RES_XML_CDATA_TYPE = 0x0104
RES_XML_LAST_CHUNK_TYPE = 0x017f

# This contains a uint32_t array mapping strings in the string
# pool back to resource identifiers.  It is optional.
RES_XML_RESOURCE_MAP_TYPE = 0x0180

# Chunk types in RES_TABLE_TYPE
RES_TABLE_PACKAGE_TYPE = 0x0200
RES_TABLE_TYPE_TYPE = 0x0201
RES_TABLE_TYPE_SPEC_TYPE = 0x0202

ACONFIGURATION_MCC = 0x0001
ACONFIGURATION_MNC = 0x0002
ACONFIGURATION_LOCALE = 0x0004
ACONFIGURATION_TOUCHSCREEN = 0x0008
ACONFIGURATION_KEYBOARD = 0x0010
ACONFIGURATION_KEYBOARD_HIDDEN = 0x0020
ACONFIGURATION_NAVIGATION = 0x0040
ACONFIGURATION_ORIENTATION = 0x0080
ACONFIGURATION_DENSITY = 0x0100
ACONFIGURATION_SCREEN_SIZE = 0x0200
ACONFIGURATION_VERSION = 0x0400
ACONFIGURATION_SCREEN_LAYOUT = 0x0800
ACONFIGURATION_UI_MODE = 0x1000


class ARSCParser(object):

    def __init__(self, raw_buff):
        self.analyzed = False
        self._resolved_strings = None
        self.buff = bytecode.BuffHandle(raw_buff)

        self.header = ARSCHeader(self.buff)
        self.packageCount = unpack('<i', self.buff.read(4))[0]

        self.stringpool_main = StringBlock(self.buff)

        self.next_header = ARSCHeader(self.buff)
        self.packages = {}
        self.values = {}
        self.resource_values = collections.defaultdict(collections.defaultdict)
        self.resource_configs = collections.defaultdict(lambda: collections.defaultdict(set))
        self.resource_keys = collections.defaultdict(
            lambda: collections.defaultdict(collections.defaultdict))

        for i in range(0, self.packageCount):
            current_package = ARSCResTablePackage(self.buff)
            package_name = current_package.get_name()

            self.packages[package_name] = []

            mTableStrings = StringBlock(self.buff)
            mKeyStrings = StringBlock(self.buff)

            self.packages[package_name].append(current_package)
            self.packages[package_name].append(mTableStrings)
            self.packages[package_name].append(mKeyStrings)

            pc = PackageContext(current_package, self.stringpool_main,
                                mTableStrings, mKeyStrings)

            current = self.buff.get_idx()
            while not self.buff.end():
                header = ARSCHeader(self.buff)
                self.packages[package_name].append(header)

                if header.type == RES_TABLE_TYPE_SPEC_TYPE:
                    self.packages[package_name].append(ARSCResTypeSpec(
                        self.buff, pc))

                elif header.type == RES_TABLE_TYPE_TYPE:
                    a_res_type = ARSCResType(self.buff, pc)
                    self.packages[package_name].append(a_res_type)
                    self.resource_configs[package_name][a_res_type].add(
                       a_res_type.config)

                    entries = []
                    for i in range(0, a_res_type.entryCount):
                        current_package.mResId = current_package.mResId & 0xffff0000 | i
                        entries.append((unpack('<i', self.buff.read(4))[0],
                                        current_package.mResId))

                    self.packages[package_name].append(entries)

                    for entry, res_id in entries:
                        if self.buff.end():
                            break

                        if entry != -1:
                            ate = ARSCResTableEntry(self.buff, res_id, pc)
                            self.packages[package_name].append(ate)

                elif header.type == RES_TABLE_PACKAGE_TYPE:
                    break
                else:
                    androconf.warning("unknown type")
                    break

                current += header.size
                self.buff.set_idx(current)

    def _analyse(self):
        if self.analyzed:
            return

        self.analyzed = True

        for package_name in self.packages:
            self.values[package_name] = {}

            nb = 3
            while nb < len(self.packages[package_name]):
                header = self.packages[package_name][nb]
                if isinstance(header, ARSCHeader):
                    if header.type == RES_TABLE_TYPE_TYPE:
                        a_res_type = self.packages[package_name][nb + 1]

                        if a_res_type.config.get_language(
                        ) not in self.values[package_name]:
                            self.values[package_name][
                                a_res_type.config.get_language()
                            ] = {}
                            self.values[package_name][a_res_type.config.get_language(
                            )]["public"] = []

                        c_value = self.values[package_name][
                            a_res_type.config.get_language()
                        ]

                        entries = self.packages[package_name][nb + 2]
                        nb_i = 0
                        for entry, res_id in entries:
                            if entry != -1:
                                ate = self.packages[package_name][nb + 3 + nb_i]

                                self.resource_values[ate.mResId][a_res_type.config] = ate
                                self.resource_keys[package_name][a_res_type.get_type()][ate.get_value()] = ate.mResId

                                if ate.get_index() != -1:
                                    c_value["public"].append(
                                        (a_res_type.get_type(), ate.get_value(),
                                         ate.mResId))

                                if a_res_type.get_type() not in c_value:
                                    c_value[a_res_type.get_type()] = []

                                if a_res_type.get_type() == "string":
                                    c_value["string"].append(
                                        self.get_resource_string(ate))

                                elif a_res_type.get_type() == "id":
                                    if not ate.is_complex():
                                        c_value["id"].append(
                                            self.get_resource_id(ate))

                                elif a_res_type.get_type() == "bool":
                                    if not ate.is_complex():
                                        c_value["bool"].append(
                                            self.get_resource_bool(ate))

                                elif a_res_type.get_type() == "integer":
                                    c_value["integer"].append(
                                        self.get_resource_integer(ate))

                                elif a_res_type.get_type() == "color":
                                    c_value["color"].append(
                                        self.get_resource_color(ate))

                                elif a_res_type.get_type() == "dimen":
                                    c_value["dimen"].append(
                                        self.get_resource_dimen(ate))

                                nb_i += 1
                        nb += 3 + nb_i - 1  # -1 to account for the nb+=1 on the next line
                nb += 1

    def get_resource_string(self, ate):
        return [ate.get_value(), ate.get_key_data()]

    def get_resource_id(self, ate):
        x = [ate.get_value()]
        if ate.key.get_data() == 0:
            x.append("false")
        elif ate.key.get_data() == 1:
            x.append("true")
        return x

    def get_resource_bool(self, ate):
        x = [ate.get_value()]
        if ate.key.get_data() == 0:
            x.append("false")
        elif ate.key.get_data() == -1:
            x.append("true")
        return x

    def get_resource_integer(self, ate):
        return [ate.get_value(), ate.key.get_data()]

    def get_resource_color(self, ate):
        entry_data = ate.key.get_data()
        return [
            ate.get_value(),
            "#%02x%02x%02x%02x" % (
                ((entry_data >> 24) & 0xFF),
                ((entry_data >> 16) & 0xFF),
                ((entry_data >> 8) & 0xFF),
                (entry_data & 0xFF))
        ]

    def get_resource_dimen(self, ate):
        try:
            return [
                ate.get_value(), "%s%s" % (
                    complexToFloat(ate.key.get_data()),
                    DIMENSION_UNITS[ate.key.get_data() & COMPLEX_UNIT_MASK])
                ]
        except IndexError:
            androconf.debug("Out of range dimension unit index for %s: %s" % (
                complexToFloat(ate.key.get_data()),
                ate.key.get_data() & COMPLEX_UNIT_MASK))
            return [ate.get_value(), ate.key.get_data()]

    # FIXME
    def get_resource_style(self, ate):
        return ["", ""]

    def get_packages_names(self):
        return list(self.packages.keys())

    def get_locales(self, package_name):
        self._analyse()
        return list(self.values[package_name].keys())

    def get_types(self, package_name, locale):
        self._analyse()
        return list(self.values[package_name][locale].keys())

    def get_public_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["public"]:
                buff += '<public type="%s" name="%s" id="0x%08x" />\n' % (
                    i[0], i[1], i[2])
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_string_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["string"]:
                buff += '<string name="%s">%s</string>\n' % (i[0], escape(i[1]))
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_strings_resources(self):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'

        buff += "<packages>\n"
        for package_name in self.get_packages_names():
            buff += "<package name=\"%s\">\n" % package_name

            for locale in self.get_locales(package_name):
                buff += "<locale value=%s>\n" % repr(locale)

                buff += '<resources>\n'
                try:
                    for i in self.values[package_name][locale]["string"]:
                        buff += '<string name="%s">%s</string>\n' % (i[0], escape(i[1]))
                except KeyError:
                    pass

                buff += '</resources>\n'
                buff += '</locale>\n'

            buff += "</package>\n"

        buff += "</packages>\n"

        return buff.encode('utf-8')

    def get_id_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["id"]:
                if len(i) == 1:
                    buff += '<item type="id" name="%s"/>\n' % (i[0])
                else:
                    buff += '<item type="id" name="%s">%s</item>\n' % (i[0],
                                                                       escape(i[1]))
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_bool_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["bool"]:
                buff += '<bool name="%s">%s</bool>\n' % (i[0], i[1])
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_integer_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["integer"]:
                buff += '<integer name="%s">%s</integer>\n' % (i[0], i[1])
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_color_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["color"]:
                buff += '<color name="%s">%s</color>\n' % (i[0], i[1])
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_dimen_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["dimen"]:
                buff += '<dimen name="%s">%s</dimen>\n' % (i[0], i[1])
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_id(self, package_name, rid, locale='\x00\x00'):
        self._analyse()

        try:
            for i in self.values[package_name][locale]["public"]:
                if i[2] == rid:
                    return i
        except KeyError:
            return None

    class ResourceResolver(object):
        def __init__(self, android_resources, config=None):
            self.resources = android_resources
            self.wanted_config = config

        def resolve(self, res_id):
            result = []
            self._resolve_into_result(result, res_id, self.wanted_config)
            return result

        def _resolve_into_result(self, result, res_id, config):
            configs = self.resources.get_res_configs(res_id, config)
            if configs:
                for config, ate in configs:
                    self.put_ate_value(result, ate, config)

        def put_ate_value(self, result, ate, config):
            if ate.is_complex():
                complex_array = []
                result.append((config, complex_array))
                for _, item in ate.item.items:
                    self.put_item_value(complex_array, item, config, complex_=True)
            else:
                self.put_item_value(result, ate.key, config, complex_=False)

        def put_item_value(self, result, item, config, complex_):
            if item.is_reference():
                res_id = item.get_data()
                if res_id:
                    self._resolve_into_result(
                        result,
                        item.get_data(),
                        self.wanted_config)
            else:
                if complex_:
                    result.append(item.format_value())
                else:
                    result.append((config, item.format_value()))

    def get_resolved_res_configs(self, rid, config=None):
        resolver = ARSCParser.ResourceResolver(self, config)
        return resolver.resolve(rid)

    def get_resolved_strings(self):
        self._analyse()
        if self._resolved_strings:
            return self._resolved_strings

        r = {}
        for package_name in self.get_packages_names():
            r[package_name] = {}
            k = {}

            for locale in self.values[package_name]:
                v_locale = locale
                if v_locale == '\x00\x00':
                    v_locale = 'DEFAULT'

                r[package_name][v_locale] = {}

                try:
                    for i in self.values[package_name][locale]["public"]:
                        if i[0] == 'string':
                            r[package_name][v_locale][i[2]] = None
                            k[i[1]] = i[2]
                except KeyError:
                    pass

                try:
                    for i in self.values[package_name][locale]["string"]:
                        if i[0] in k:
                            r[package_name][v_locale][k[i[0]]] = i[1]
                except KeyError:
                    pass

        self._resolved_strings = r
        return r

    def get_res_configs(self, rid, config=None):
        self._analyse()

        if not rid:
            raise ValueError("'rid' should be set")

        try:
            res_options = self.resource_values[rid]
            if len(res_options) > 1 and config:
                return [(
                    config,
                    res_options[config])]
            else:
                return list(res_options.items())

        except KeyError:
            return []

    def get_string(self, package_name, name, locale='\x00\x00'):
        self._analyse()

        try:
            for i in self.values[package_name][locale]["string"]:
                if i[0] == name:
                    return i
        except KeyError:
            return None

    def get_res_id_by_key(self, package_name, resource_type, key):
        try:
            return self.resource_keys[package_name][resource_type][key]
        except KeyError:
            return None

    def get_items(self, package_name):
        self._analyse()
        return self.packages[package_name]

    def get_type_configs(self, package_name, type_name=None):
        if package_name is None:
            package_name = self.get_packages_names()[0]
        result = collections.defaultdict(list)

        for res_type, configs in list(self.resource_configs[package_name].items()):
            if res_type.get_package_name() == package_name and (
                    type_name is None or res_type.get_type() == type_name):
                result[res_type.get_type()].extend(configs)

        return result


class PackageContext(object):

    def __init__(self, current_package, stringpool_main, mTableStrings,
                 mKeyStrings):
        self.stringpool_main = stringpool_main
        self.mTableStrings = mTableStrings
        self.mKeyStrings = mKeyStrings
        self.current_package = current_package

    def get_mResId(self):
        return self.current_package.mResId

    def set_mResId(self, mResId):
        self.current_package.mResId = mResId

    def get_package_name(self):
        return self.current_package.get_name()


class ARSCHeader(object):

    def __init__(self, buff):
        self.start = buff.get_idx()
        self.type = unpack('<h', buff.read(2))[0]
        self.header_size = unpack('<h', buff.read(2))[0]
        self.size = unpack('<I', buff.read(4))[0]


class ARSCResTablePackage(object):

    def __init__(self, buff):
        self.start = buff.get_idx()
        self.id = unpack('<I', buff.read(4))[0]
        self.name = buff.readNullString(256)
        self.typeStrings = unpack('<I', buff.read(4))[0]
        self.lastPublicType = unpack('<I', buff.read(4))[0]
        self.keyStrings = unpack('<I', buff.read(4))[0]
        self.lastPublicKey = unpack('<I', buff.read(4))[0]
        self.mResId = self.id << 24

    def get_name(self):
        name = self.name.decode("utf-16", 'replace')
        name = name[:name.find("\x00")]
        return name


class ARSCResTypeSpec(object):

    def __init__(self, buff, parent=None):
        self.start = buff.get_idx()
        self.parent = parent
        self.id = unpack('<b', buff.read(1))[0]
        self.res0 = unpack('<b', buff.read(1))[0]
        self.res1 = unpack('<h', buff.read(2))[0]
        self.entryCount = unpack('<I', buff.read(4))[0]

        self.typespec_entries = []
        for i in range(0, self.entryCount):
            self.typespec_entries.append(unpack('<I', buff.read(4))[0])


class ARSCResType(object):

    def __init__(self, buff, parent=None):
        self.start = buff.get_idx()
        self.parent = parent
        self.id = unpack('<b', buff.read(1))[0]
        self.res0 = unpack('<b', buff.read(1))[0]
        self.res1 = unpack('<h', buff.read(2))[0]
        self.entryCount = unpack('<i', buff.read(4))[0]
        self.entriesStart = unpack('<i', buff.read(4))[0]
        self.mResId = (0xff000000 & self.parent.get_mResId()) | self.id << 16
        self.parent.set_mResId(self.mResId)

        self.config = ARSCResTableConfig(buff)

    def get_type(self):
        return self.parent.mTableStrings.getString(self.id - 1)

    def get_package_name(self):
        return self.parent.get_package_name()

    def __repr__(self):
        return "ARSCResType(%x, %x, %x, %x, %x, %x, %x, %s)" % (
            self.start,
            self.id,
            self.res0,
            self.res1,
            self.entryCount,
            self.entriesStart,
            self.mResId,
            "table:" + self.parent.mTableStrings.getString(self.id - 1)
        )


class ARSCResTableConfig(object):
    @classmethod
    def default_config(cls):
        if not hasattr(cls, 'DEFAULT'):
            cls.DEFAULT = ARSCResTableConfig(None)
        return cls.DEFAULT

    def __init__(self, buff=None, **kwargs):
        if buff is not None:
            self.start = buff.get_idx()
            self.size = unpack('<I', buff.read(4))[0]
            self.imsi = unpack('<I', buff.read(4))[0]
            self.locale = unpack('<I', buff.read(4))[0]
            self.screenType = unpack('<I', buff.read(4))[0]
            self.input = unpack('<I', buff.read(4))[0]
            self.screenSize = unpack('<I', buff.read(4))[0]
            self.version = unpack('<I', buff.read(4))[0]

            self.screenConfig = 0
            self.screenSizeDp = 0

            if self.size >= 32:
                self.screenConfig = unpack('<I', buff.read(4))[0]

                if self.size >= 36:
                    self.screenSizeDp = unpack('<I', buff.read(4))[0]

            self.exceedingSize = self.size - 36
            if self.exceedingSize > 0:
                androconf.info("Skipping padding bytes!")
                self.padding = buff.read(self.exceedingSize)
        else:
            self.start = 0
            self.size = 0
            self.imsi = \
                ((kwargs.pop('mcc', 0) & 0xffff) << 0) + \
                ((kwargs.pop('mnc', 0) & 0xffff) << 16)

            self.locale = 0
            for char_ix, char in kwargs.pop('locale', "")[0:4]:
                self.locale += (ord(char) << (char_ix * 8))

            self.screenType = \
                ((kwargs.pop('orientation', 0) & 0xff) << 0) + \
                ((kwargs.pop('touchscreen', 0) & 0xff) << 8) + \
                ((kwargs.pop('density', 0) & 0xffff) << 16)

            self.input = \
                ((kwargs.pop('keyboard', 0) & 0xff) << 0) + \
                ((kwargs.pop('navigation', 0) & 0xff) << 8) + \
                ((kwargs.pop('inputFlags', 0) & 0xff) << 16) + \
                ((kwargs.pop('inputPad0', 0) & 0xff) << 24)

            self.screenSize = \
                ((kwargs.pop('screenWidth', 0) & 0xffff) << 0) + \
                ((kwargs.pop('screenHeight', 0) & 0xffff) << 16)

            self.version = \
                ((kwargs.pop('sdkVersion', 0) & 0xffff) << 0) + \
                ((kwargs.pop('minorVersion', 0) & 0xffff) << 16)

            self.screenConfig = \
                ((kwargs.pop('screenLayout', 0) & 0xff) << 0) + \
                ((kwargs.pop('uiMode', 0) & 0xff) << 8) + \
                ((kwargs.pop('smallestScreenWidthDp', 0) & 0xffff) << 16)

            self.screenSizeDp = \
                ((kwargs.pop('screenWidthDp', 0) & 0xffff) << 0) + \
                ((kwargs.pop('screenHeightDp', 0) & 0xffff) << 16)

            self.exceedingSize = 0

    def get_language(self):
        x = self.locale & 0x0000ffff
        return chr(x & 0x00ff) + chr((x & 0xff00) >> 8)

    def get_country(self):
        x = (self.locale & 0xffff0000) >> 16
        return chr(x & 0x00ff) + chr((x & 0xff00) >> 8)

    def get_density(self):
        x = ((self.screenType >> 16) & 0xffff)
        return x

    def _get_tuple(self):
        return (
            self.imsi,
            self.locale,
            self.screenType,
            self.input,
            self.screenSize,
            self.version,
            self.screenConfig,
            self.screenSizeDp,
        )

    def __hash__(self):
        return hash(self._get_tuple())

    def __eq__(self, other):
        return self._get_tuple() == other._get_tuple()

    def __repr__(self):
        return repr(self._get_tuple())


class ARSCResTableEntry(object):

    def __init__(self, buff, mResId, parent=None):
        self.start = buff.get_idx()
        self.mResId = mResId
        self.parent = parent
        self.size = unpack('<H', buff.read(2))[0]
        self.flags = unpack('<H', buff.read(2))[0]
        self.index = unpack('<I', buff.read(4))[0]

        if self.flags & 1:
            self.item = ARSCComplex(buff, parent)
        else:
            self.key = ARSCResStringPoolRef(buff, self.parent)

    def get_index(self):
        return self.index

    def get_value(self):
        return self.parent.mKeyStrings.getString(self.index)

    def get_key_data(self):
        return self.key.get_data_value()

    def is_public(self):
        return self.flags == 0 or self.flags == 2

    def is_complex(self):
        return (self.flags & 1) == 1

    def __repr__(self):
        return "ARSCResTableEntry(%x, %x, %x, %x, %x, %r)" % (
            self.start,
            self.mResId,
            self.size,
            self.flags,
            self.index,
            self.item if self.is_complex() else self.key)


class ARSCComplex(object):

    def __init__(self, buff, parent=None):
        self.start = buff.get_idx()
        self.parent = parent

        self.id_parent = unpack('<I', buff.read(4))[0]
        self.count = unpack('<I', buff.read(4))[0]

        self.items = []
        for i in range(0, self.count):
            self.items.append((unpack('<I', buff.read(4))[0],
                               ARSCResStringPoolRef(buff, self.parent)))

    def __repr__(self):
        return "ARSCComplex(%x, %d, %d)" % (self.start, self.id_parent, self.count)


class ARSCResStringPoolRef(object):

    def __init__(self, buff, parent=None):
        self.start = buff.get_idx()
        self.parent = parent

        self.skip_bytes = buff.read(3)
        self.data_type = unpack('<B', buff.read(1))[0]
        self.data = unpack('<I', buff.read(4))[0]

    def get_data_value(self):
        return self.parent.stringpool_main.getString(self.data)

    def get_data(self):
        return self.data

    def get_data_type(self):
        return self.data_type

    def get_data_type_string(self):
        return TYPE_TABLE[self.data_type]

    def format_value(self):
        return format_value(
            self.data_type,
            self.data,
            self.parent.stringpool_main.getString
        )

    def is_reference(self):
        return self.data_type == TYPE_REFERENCE

    def __repr__(self):
        return "ARSCResStringPoolRef(%x, %s, %x)" % (
            self.start,
            TYPE_TABLE.get(self.data_type, "0x%x" % self.data_type),
            self.data)


def get_arsc_info(arscobj):
    buff = ""
    for package in arscobj.get_packages_names():
        buff += package + ":\n"
        for locale in arscobj.get_locales(package):
            buff += "\t" + repr(locale) + ":\n"
            for ttype in arscobj.get_types(package, locale):
                buff += "\t\t" + ttype + ":\n"
                try:
                    tmp_buff = getattr(arscobj, "get_" + ttype + "_resources")(
                        package, locale).decode("utf-8", 'replace').split("\n")
                    for i in tmp_buff:
                        buff += "\t\t\t" + i + "\n"
                except AttributeError:
                    pass
    return buff
