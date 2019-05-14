from struct import pack, unpack
import sys
from binascii import hexlify

# This is a very simple DEX parser, to get the bytecodes for each method
# Output format will be:
# <class name> <method name> <bytecode as hex string>

from androguard.core.bytecodes.dvm import readuleb128, readsleb128, DalvikPacker


def read_null_terminated(f):
    x = bytearray()
    while True:
        z = f.read(1)
        if ord(z) == 0:
            return x
        else:
            x.append(ord(z))

class MockClassManager():
    @property
    def packer(self):
        return DalvikPacker(0x12345678)

cm = MockClassManager()

class read_dex:

    def __init__(self, fname):
        methods = []  # Stores method_idx, code_off

        with open(fname, "rb") as f:
            magic, checksum, signature, file_size, header_size, endian_tag, link_size, \
            link_off, map_off, self.string_ids_size, string_ids_off, type_ids_size, \
            type_ids_off, proto_ids_size, proto_ids_off, field_ids_size, field_ids_off, \
            method_ids_size, method_ids_off, class_defs_size, class_defs_off, data_size, \
            data_off = unpack("<8sI20s20I", f.read(112))

            # print("class_defs_size", class_defs_size, "class_defs_off", class_defs_off)
            for i in range(class_defs_size):
                # class_def_item
                f.seek(class_defs_off + i * 8 * 4)
                class_idx, access_flags, superclass_idx, interfaces_off, source_file_idx, \
                annotations_off, class_data_off, static_values_off = unpack("<8I", f.read(8 * 4))

                # Now parse the class_data_item
                if class_data_off == 0:
                    continue
                f.seek(class_data_off)
                static_fields_size = readuleb128(cm, f)
                instance_fields_size = readuleb128(cm, f)
                direct_methods_size = readuleb128(cm, f)
                virtual_methods_size = readuleb128(cm, f)
                #print("class_data_item:", static_fields_size, instance_fields_size, direct_methods_size, virtual_methods_size)

                # We do not need the fields...
                for _ in range(static_fields_size + instance_fields_size):
                    readuleb128(cm, f)
                    readuleb128(cm, f)

                # Now parse methods
                method_idx = 0
                for _ in range(direct_methods_size):
                    method_idx_diff = readuleb128(cm, f)
                    access_flags = readuleb128(cm, f)
                    code_off = readuleb128(cm, f)

                    # print("direct_methods", method_idx_diff, access_flags, code_off)

                    method_idx += method_idx_diff
                    methods.append([method_idx, code_off])

                method_idx = 0
                for _ in range(virtual_methods_size):
                    method_idx_diff = readuleb128(cm, f)
                    access_flags = readuleb128(cm, f)
                    code_off = readuleb128(cm, f)

                    # print("virtual_methods", method_idx_diff, access_flags, code_off)

                    method_idx += method_idx_diff
                    methods.append([method_idx, code_off])


            # Read the string section
            strings = dict()
            self.str_raw = dict()
            for i in range(self.string_ids_size):
                f.seek(string_ids_off + i * 4)
                string_data_off, = unpack("<I", f.read(4))

                f.seek(string_data_off)
                utf16_size = readuleb128(cm, f)
                s = read_null_terminated(f)
                # FIXME this is wrong...
                self.str_raw[i] = s
                strings[i] = s.decode("UTF-8")

            # Read the type section
            self.types = dict()
            for i in range(type_ids_size):
                f.seek(type_ids_off + i * 4)
                descriptor_idx, = unpack("<I", f.read(4))
                self.types[i] = descriptor_idx

            method_ids = {}
            # Next, we need to parse the method_id section
            for i in range(method_ids_size):
                f.seek(method_ids_off + i * 8)
                class_idx, proto_idx, name_idx = unpack("<HHI", f.read(8))
                method_ids[i] = [strings[self.types[class_idx]], strings[name_idx]]



            # Now parse the found methods and print to stdout
            mres = dict()
            for method_idx, code_off in methods:
                if code_off == 0:
                    continue
                # We just parse everything manually to get the length, then we save the
                # complete code block
                f.seek(code_off)
                registers_size, ins_size, outs_size, tries_size, debug_info_off, insns_size \
                    = unpack("<4HII", f.read(4 * 2 + 2 * 4))

                insns = unpack("<{}H".format(insns_size), f.read(2 * insns_size))

                if tries_size > 0 and insns_size % 2 == 1:
                    padding = unpack("<H", f.read(2))

                if tries_size > 0:

                    # try_item[tries_size]
                    tries = unpack("<{}".format("".join(["IHH"] * tries_size)), f.read(8 * tries_size))

                    # encoded_catch_handler_list
                    size = readuleb128(cm, f)
                    for _ in range(size):
                        # encoded_catch_handler
                        s = readsleb128(cm, f)
                        for _ in range(abs(s)):
                            # encoded_type_addr_pair
                            _ = readuleb128(cm, f)
                            _ = readuleb128(cm, f)
                        if s <= 0:
                            catch_all_addr = readuleb128(cm, f)

                l = f.tell() - code_off
                f.seek(code_off)
                buff = f.read(l)
                mres[method_idx] = hexlify(buff)

            self.methods = mres


if __name__ == "__main__":
    for midx, buff in read_dex(sys.argv[1]).methods.items():
        pass
        #print(midx, buff)


