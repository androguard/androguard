from __future__ import division
from __future__ import print_function

from future import standard_library

standard_library.install_aliases()
from builtins import str
from builtins import range
from builtins import object
from androguard.core import androconf
from androguard.core.bytecodes.dvm_permissions import DVM_PERMISSIONS
from androguard.util import read

from androguard.core.bytecodes.axml import ARSCParser, AXMLPrinter, ARSCResTableConfig

import io
from zlib import crc32
import re
import sys
import binascii
import zipfile
import logging

import lxml.sax
from xml.dom.pulldom import SAX2DOM
from lxml import etree

# Used for reading Certificates
from pyasn1.codec.der.decoder import decode
from pyasn1.codec.der.encoder import encode
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

NS_ANDROID_URI = 'http://schemas.android.com/apk/res/android'

log = logging.getLogger("androguard.apk")


def parse_lxml_dom(tree):
    handler = SAX2DOM()
    lxml.sax.saxify(tree, handler)
    return handler.document


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class FileNotPresent(Error):
    pass


class BrokenAPKError(Error):
    pass


######################################################## APK FORMAT ########################################################
class APK(object):
    def __init__(self,
                 filename,
                 raw=False,
                 magic_file=None,
                 skip_analysis=False,
                 testzip=False):
        """
            This class can access to all elements in an APK file

            :param filename: specify the path of the file, or raw data
            :param raw: specify if the filename is a path or raw data (optional)
            :param magic_file: specify the magic file (optional)
            :param skip_analysis: Skip the analysis, e.g. no manifest files are read. (default: False)
            :param testzip: Test the APK for integrity, e.g. if the ZIP file is broken. Throw an exception on failure (default False)

            :type filename: string
            :type raw: boolean
            :type magic_file: string
            :type skip_analysis: boolean
            :type testzip: boolean

            :Example:
              APK("myfile.apk")
              APK(read("myfile.apk"), raw=True)
        """
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

        self.zip = zipfile.ZipFile(io.BytesIO(self.__raw), mode="r")

        if testzip:
            # Test the zipfile for integrity before continuing.
            # This process might be slow, as the whole file is read.
            # Therefore it is possible to enable it as a separate feature.
            #
            # A short benchmark showed, that testing the zip takes about 10 times longer!
            # e.g. normal zip loading (skip_analysis=True) takes about 0.01s, where
            # testzip takes 0.1s!
            ret = self.zip.testzip()
            if ret is not None:
                # we could print the filename here, but there are zip which are so broken
                # That the filename is either very very long or does not make any sense.
                # Thus we do not do it, the user might find out by using other tools.
                raise BrokenAPKError("The APK is probably broken: testzip returned an error.")

        if not skip_analysis:
            self._apk_analysis()

    def _apk_analysis(self):
        """
        Run analysis on the APK file.

        This method is usually called by __init__ except if skip_analysis is False.
        It will then parse the AndroidManifest.xml and set all fields in the APK class which can be
        extracted from the Manifest.
        """
        for i in self.zip.namelist():
            if i == "AndroidManifest.xml":
                self.axml[i] = AXMLPrinter(self.zip.read(i))
                self.xml[i] = None
                raw_xml = self.axml[i].get_buff()
                if len(raw_xml) == 0:
                    log.warning("AXML parsing failed, file is empty")
                else:
                    try:
                        if self.axml[i].is_packed():
                            log.warning("XML Seems to be packed, parsing is very likely to fail.")
                        parser = etree.XMLParser(recover=True)
                        tree = etree.fromstring(raw_xml, parser=parser)
                        self.xml[i] = parse_lxml_dom(tree)
                    except Exception as e:
                        log.warning("reading AXML as XML failed: " + str(e))

                if self.xml[i] is not None:
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

        self.permission_module = androconf.load_api_specific_resource_module(
            "aosp_permissions", self.get_target_sdk_version())

    def __getstate__(self):
        """
        Function for pickling APK Objects.

        We remove the zip from the Object, as it is not pickable
        And it does not make any sense to pickle it anyways.

        :return: the picklable APK Object without zip.
        """
        # Upon pickling, we need to remove the ZipFile
        x = self.__dict__
        del x['zip']

        return x

    def __setstate__(self, state):
        """
        Load a pickled APK Object and restore the state

        We load the zip file back by reading __raw from the Object.

        :param state: pickled state
        """
        self.__dict__ = state

        self.zip = zipfile.ZipFile(io.BytesIO(self.__raw), mode="r")

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

        if app_name is None:
            # No App name set
            # TODO return packagename instead?
            return ""
        if app_name.startswith("@"):
            res_id = int(app_name[1:], 16)
            res_parser = self.get_android_resources()

            try:
                app_name = res_parser.get_resolved_res_configs(
                    res_id,
                    ARSCResTableConfig.default_config())[0][1]
            except Exception as e:
                log.warning("Exception selecting app name: %s" % e)
                app_name = ""
        return app_name

    def get_app_icon(self, max_dpi=65536):
        """
            Return the first non-greater density than max_dpi icon file name,
            unless exact icon resolution is set in the manifest, in which case
            return the exact file

            From https://developer.android.com/guide/practices/screens_support.html
            ldpi (low) ~120dpi
            mdpi (medium) ~160dpi
            hdpi (high) ~240dpi
            xhdpi (extra-high) ~320dpi
            xxhdpi (extra-extra-high) ~480dpi
            xxxhdpi (extra-extra-extra-high) ~640dpi

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
                log.warning("Exception selecting app icon: %s" % e)

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

    def _get_file_magic_name(self, buffer):
        """
        Return the filetype guessed for a buffer
        :param buffer: bytes
        :return: str of filetype
        """
        # TODO this functions should be better in another package
        default = "Unknown"
        ftype = None

        # There are several implementations of magic,
        # unfortunately all called magic
        try:
            import magic
        except ImportError:
            # no lib magic at all, return unknown
            return default

        try:
            # We test for the python-magic package here
            getattr(magic, "MagicException")
        except AttributeError:
            try:
                # Check for filemagic package
                getattr(magic.Magic, "id_buffer")
            except AttributeError:
                # Here, we load the file-magic package
                ms = magic.open(magic.MAGIC_NONE)
                ms.load()
                ftype = ms.buffer(buffer)
            else:
                # This is now the filemagic package
                if self.magic_file is not None:
                    m = magic.Magic(paths=[self.magic_file])
                else:
                    m = magic.Magic()
                ftype = m.id_buffer(buffer)
        else:
            # This is the code for python-magic
            if self.magic_file is not None:
                m = magic.Magic(magic_file=self.magic_file)
            else:
                m = magic.Magic()
            ftype = m.from_buffer(buffer)

        if ftype is None:
            return default
        else:
            return self._patch_magic(buffer, ftype)

    def get_files_types(self):
        """
            Return the files inside the APK with their associated types (by using python-magic)

            :rtype: a dictionnary
        """
        if self.files == {}:
            # Generate File Types / CRC List
            for i in self.get_files():
                buffer = self.zip.read(i)
                self.files_crc32[i] = crc32(buffer)
                self.files[i] = self._get_file_magic_name(buffer)

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
        """
        Calculates and returns a dictionary of filenames and CRC32

        :return: dict of filename: CRC32
        """
        if self.files_crc32 == {}:
            for i in self.get_files():
                buffer = self.zip.read(i)
                self.files_crc32[i] = crc32(buffer)

        return self.files_crc32

    def get_files_information(self):
        """
            Return the files inside the APK with their associated types and crc32

            :rtype: string, string, int
        """
        for k in self.get_files():
            yield k, self.get_files_types()[k], self.get_files_crc32()[k]

    def get_raw(self):
        """
            Return raw bytes of the APK

            :rtype: string
        """
        return self.__raw

    def get_file(self, filename):
        """
            Return the raw data of the specified filename
            inside the APK

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

    def is_multidex(self):
        """
        Test if the APK has multiple DEX files

        :return: True if multiple dex found, otherwise False
        """
        return "classes1.dex" in self.get_files()

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

                l.append(value)
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
            if self.xml[i] is None:
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
        d = {"action": [], "category": []}

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

    @DeprecationWarning
    def get_requested_permissions(self):
        """
            Returns all requested permissions.

            :rtype: list of strings
        """
        return self.get_permissions()

    def get_requested_aosp_permissions(self):
        """
            Returns requested permissions declared within AOSP project.

            :rtype: list of strings
        """
        aosp_permissions = []
        all_permissions = self.get_permissions()
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
        """
            Returns list of requested permissions not declared within AOSP project.

            :rtype: list of strings
        """
        third_party_permissions = []
        all_permissions = self.get_permissions()
        for perm in all_permissions:
            if perm not in list(self.permission_module["AOSP_PERMISSIONS"].keys()):
                third_party_permissions.append(perm)
        return third_party_permissions

    def get_declared_permissions(self):
        """
            Returns list of the declared permissions.

            :rtype: list of strings
        """
        return list(self.declared_permissions.keys())

    def get_declared_permissions_details(self):
        """
            Returns declared permissions with the details.

            :rtype: dict
        """
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


    def get_certificate_der(self, filename):
        """
        Return the DER coded X.509 certificate from the signature file.

        :param filename: Signature filename in APK
        :return: DER coded X.509 certificate as binary
        """
        pkcs7message = self.get_file(filename)

        # TODO for correct parsing, we would need to write our own ASN1Spec for the SignatureBlock format
        message, _ = decode(pkcs7message)
        cert = encode(message[1][3])
        # Remove the first identifier
        # byte 0 == identifier, skip
        # byte 1 == length. If byte1 & 0x80 > 1, we have long format
        #                   The length of to read bytes is then coded
        #                   in byte1 & 0x7F
        # Check if the first byte is 0xA0 (Sequence Tag)
        tag = cert[0]
        l = cert[1]
        # Python2 compliance
        if not isinstance(l, int):
            l = ord(l)
            tag = ord(tag)
        if tag == 0xA0:
            cert = cert[2 + (l & 0x7F) if l & 0x80 > 1 else 2:]

        return cert

    def get_certificate(self, filename):
        """
        Return a X.509 certificate object by giving the name in the apk file

        :param filename: filename of the signature file in the APK
        :return: a `x509` certificate
        """
        cert = self.get_certificate_der(filename)
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
        zout = zipfile.ZipFile(filename, 'w')

        for item in self.zip.infolist():
            if deleted_files is not None:
                if re.match(deleted_files, item.filename) is None:
                    buffer = self.zip.read(item.filename)
                    zout.writestr(item, buffer)
            if new_files is not False:
                if item.filename in new_files:
                    zout.writestr(item, new_files[item.filename])
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
            if "resources.arsc" not in self.zip.namelist():
                # There is a rare case, that no resource file is supplied.
                # Maybe it was added manually, thus we check here
                return None
            self.arsc["resources.arsc"] = ARSCParser(self.zip.read(
                "resources.arsc"))
            return self.arsc["resources.arsc"]

    def get_signature_name(self):
        """
            Return the name of the first signature file found.
        """
        if self.get_signature_names():
            return self.get_signature_names()[0]
        else:
            # Unsigned APK
            return None

    def get_signature_names(self):
        """
             Return a list of the signature file names.
        """
        signature_expr = re.compile("^(META-INF/)(.*)(\.RSA|\.EC|\.DSA)$")
        signatures = []

        for i in self.get_files():
            if signature_expr.search(i):
                signatures.append(i)

        return signatures

    def get_signature(self):
        """
            Return the data of the first signature file found.
        """
        if self.get_signatures():
            return self.get_signatures()[0]
        else:
            return None

    def get_signatures(self):
        """
            Return a list of the data of the signature files.
        """
        signature_expr = re.compile("^(META-INF/)(.*)(\.RSA|\.EC|\.DSA)$")
        signature_datas = []

        for i in self.get_files():
            if signature_expr.search(i):
                signature_datas.append(self.get_file(i))

        return signature_datas

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
        requested_permissions = self.get_permissions()
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
    return ", ".join(
        ["{}={}".format(attr.oid._name if not short or attr.oid._name not in sf else sf[attr.oid._name], attr.value) for
         attr in name])


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


