from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat
from androguard.core.analysis.analysis import Analysis
from androguard.decompiler.dad.decompile import DvMethod

import logging
import traceback
import sys
import os

"""
This is a script to call several functions on APK and DEX files
and run the decompiler on all methods inside the DEX files.

You just need some folder where you store APK files.
You can also adjust the function samples() by your needs.

This script will create a logfile in the current directory,
and log all errors regarding those files in there.

The list of functions to call, can be adjusted as well.
Note that you can currently only call functions that do not
take an argument.

This script is not intended to be used on CI platforms,
as it can take ages to run!
A single APK takes already several minutes.
"""

# Adjust those two variables to your own needs:
COLLECTION_PATH = r"G:\testset"
LOG_FILENAME = 'G:\ANDROGUARD_TESTS_BUGS.txt'

logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)


def samples():
    for root, _, files in os.walk(COLLECTION_PATH):
        for f in files:
            yield os.path.join(root, f)


def main():
    for path in samples():
        print(path)
        logging.error("Processing" + path)

        tests_apk = ["is_valid_APK", "get_filename", "get_app_name", "get_app_icon",
                 "get_package", "get_androidversion_code", "get_androidversion_name",
                 "get_files", "get_files_types", "get_files_crc32", "get_files_information",
                 "get_raw", "get_dex", "get_all_dex", "get_main_activity",
                 "get_activities", "get_services", "get_receivers", "get_providers",
                 "get_permissions", "get_details_permissions", "get_requested_aosp_permissions",
                 "get_requested_aosp_permissions_details", "get_requested_third_party_permissions",
                 "get_declared_permissions", "get_declared_permissions_details", "get_max_sdk_version",
                 "get_min_sdk_version", "get_target_sdk_version", "get_libraries", "get_android_manifest_axml",
                 "get_android_manifest_xml", "get_android_resources", "get_signature_name", "get_signature_names",
                 "get_signature", "get_signatures"]

        tests_dex = ["get_api_version", "get_classes_def_item", "get_methods_id_item", "get_fields_id_item",
                     "get_codes_item", "get_string_data_item",
                     "get_debug_info_item", "get_header_item", "get_class_manager", "show",
                     # "save",  # FIXME broken
                     "get_classes_names", "get_classes",
                     "get_all_fields", "get_fields", "get_methods", "get_len_methods",
                     "get_strings", "get_format_type", "create_python_export",
                     "get_BRANCH_DVM_OPCODES", "get_determineNext",
                     "get_determineException", "print_classes_hierarchy",
                     "list_classes_hierarchy", "get_format"]

        try:
            # Testing APK
            a = APK(path)
            for t in tests_apk:
                print(t)
                x = getattr(a, t)
                try:
                    x()
                except Exception as aaa:
                    print(aaa)
                    traceback.print_exc()
                    print(path, aaa, file=sys.stderr)
                    logging.exception("{} .. {}".format(path, t))


            # Testing DEX
            dx = Analysis()
            for dex in a.get_all_dex():
                d = DalvikVMFormat(dex)
                dx.add(d)

                # Test decompilation
                for c in d.get_classes():
                    for m in c.get_methods():
                        mx = dx.get_method(m)
                        ms = DvMethod(mx)
                        try:
                            ms.process(doAST=True)
                        except Exception as aaa:
                            print(aaa)
                            traceback.print_exc()
                            print(path, aaa, file=sys.stderr)
                            logging.exception("{} .. {} .. {}".format(path, c.get_name(), m.get_name()))
                        ms2 = DvMethod(mx)
                        try:
                            ms2.process(doAST=False)
                        except Exception as aaa:
                            print(aaa)
                            traceback.print_exc()
                            print(path, aaa, file=sys.stderr)
                            logging.exception("{} .. {} .. {}".format(path, c.get_name(), m.get_name()))

                # DEX tests
                for t in tests_dex:
                    print(t)
                    x = getattr(d, t)
                    try:
                        x()
                    except Exception as aaa:
                        print(aaa)
                        traceback.print_exc()
                        print(path, aaa, file=sys.stderr)
                        logging.exception("{} .. {}".format(path, t))

            # Analysis Tests
            try:
                dx.create_xref()
            except Exception as aaa:
                print(aaa)
                traceback.print_exc()
                print(path, aaa, file=sys.stderr)
                logging.exception("{} .. {} at Analysis".format(path, t))

            # MethodAnalysis tests
            for m in dx.methods.values():
                for bb in m.get_basic_blocks():
                    try:
                        list(bb.get_instructions())
                    except Exception as aaa:
                        print(aaa)
                        traceback.print_exc()
                        print(path, aaa, file=sys.stderr)
                        logging.exception("{} .. {} at BasicBlock {}".format(path, t, m))

        except KeyboardInterrupt:
            raise
        except FileNotFoundError:
            pass
        except Exception as e:
            print(e)
            traceback.print_exc()
            print(path, e, file=sys.stderr)
            logging.exception(path)

if __name__ == "__main__":
    main()


