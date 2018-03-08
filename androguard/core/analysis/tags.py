import re


class Enum:
    def __init__(self, names):
        self.names = names
        for value, name in enumerate(self.names):
            setattr(self, name.upper(), value)

    def tuples(self):
        return tuple(enumerate(self.names))


TAG_ANDROID = Enum(
    ['ANDROID', 'TELEPHONY', 'SMS', 'SMSMESSAGE', 'ACCESSIBILITYSERVICE',
     'ACCOUNTS', 'ANIMATION', 'APP', 'BLUETOOTH', 'CONTENT', 'DATABASE',
     'DEBUG', 'DRM', 'GESTURE', 'GRAPHICS', 'HARDWARE', 'INPUTMETHODSERVICE',
     'LOCATION', 'MEDIA', 'MTP', 'NET', 'NFC', 'OPENGL', 'OS', 'PREFERENCE',
     'PROVIDER', 'RENDERSCRIPT', 'SAX', 'SECURITY', 'SERVICE', 'SPEECH',
     'SUPPORT', 'TEST', 'TEXT', 'UTIL', 'VIEW', 'WEBKIT', 'WIDGET',
     'DALVIK_BYTECODE', 'DALVIK_SYSTEM', 'JAVA_REFLECTION'])

TAG_REVERSE_ANDROID = dict((i[0], i[1]) for i in TAG_ANDROID.tuples())

TAGS_ANDROID = {
    TAG_ANDROID.ANDROID: [0, "Landroid"],
    TAG_ANDROID.TELEPHONY: [0, "Landroid/telephony"],
    TAG_ANDROID.SMS: [0, "Landroid/telephony/SmsManager"],
    TAG_ANDROID.SMSMESSAGE: [0, "Landroid/telephony/SmsMessage"],
    TAG_ANDROID.DEBUG: [0, "Landroid/os/Debug"],
    TAG_ANDROID.ACCESSIBILITYSERVICE: [0, "Landroid/accessibilityservice"],
    TAG_ANDROID.ACCOUNTS: [0, "Landroid/accounts"],
    TAG_ANDROID.ANIMATION: [0, "Landroid/animation"],
    TAG_ANDROID.APP: [0, "Landroid/app"],
    TAG_ANDROID.BLUETOOTH: [0, "Landroid/bluetooth"],
    TAG_ANDROID.CONTENT: [0, "Landroid/content"],
    TAG_ANDROID.DATABASE: [0, "Landroid/database"],
    TAG_ANDROID.DRM: [0, "Landroid/drm"],
    TAG_ANDROID.GESTURE: [0, "Landroid/gesture"],
    TAG_ANDROID.GRAPHICS: [0, "Landroid/graphics"],
    TAG_ANDROID.HARDWARE: [0, "Landroid/hardware"],
    TAG_ANDROID.INPUTMETHODSERVICE: [0, "Landroid/inputmethodservice"],
    TAG_ANDROID.LOCATION: [0, "Landroid/location"],
    TAG_ANDROID.MEDIA: [0, "Landroid/media"],
    TAG_ANDROID.MTP: [0, "Landroid/mtp"],
    TAG_ANDROID.NET: [0, "Landroid/net"],
    TAG_ANDROID.NFC: [0, "Landroid/nfc"],
    TAG_ANDROID.OPENGL: [0, "Landroid/opengl"],
    TAG_ANDROID.OS: [0, "Landroid/os"],
    TAG_ANDROID.PREFERENCE: [0, "Landroid/preference"],
    TAG_ANDROID.PROVIDER: [0, "Landroid/provider"],
    TAG_ANDROID.RENDERSCRIPT: [0, "Landroid/renderscript"],
    TAG_ANDROID.SAX: [0, "Landroid/sax"],
    TAG_ANDROID.SECURITY: [0, "Landroid/security"],
    TAG_ANDROID.SERVICE: [0, "Landroid/service"],
    TAG_ANDROID.SPEECH: [0, "Landroid/speech"],
    TAG_ANDROID.SUPPORT: [0, "Landroid/support"],
    TAG_ANDROID.TEST: [0, "Landroid/test"],
    TAG_ANDROID.TEXT: [0, "Landroid/text"],
    TAG_ANDROID.UTIL: [0, "Landroid/util"],
    TAG_ANDROID.VIEW: [0, "Landroid/view"],
    TAG_ANDROID.WEBKIT: [0, "Landroid/webkit"],
    TAG_ANDROID.WIDGET: [0, "Landroid/widget"],
    TAG_ANDROID.DALVIK_BYTECODE: [0, "Ldalvik/bytecode"],
    TAG_ANDROID.DALVIK_SYSTEM: [0, "Ldalvik/system"],
    TAG_ANDROID.JAVA_REFLECTION: [0, "Ljava/lang/reflect"],
}


class Tags:
    """
      Handle specific tags

      :param patterns:
      :params reverse:
  """

    def __init__(self, patterns=TAGS_ANDROID, reverse=TAG_REVERSE_ANDROID):
        self.tags = set()

        self.patterns = patterns
        self.reverse = TAG_REVERSE_ANDROID

        for i in self.patterns:
            self.patterns[i][1] = re.compile(self.patterns[i][1])

    def emit(self, method):
        for i in self.patterns:
            if self.patterns[i][0] == 0:
                if self.patterns[i][1].search(method.get_class()) is not None:
                    self.tags.add(i)

    def emit_by_classname(self, classname):
        for i in self.patterns:
            if self.patterns[i][0] == 0:
                if self.patterns[i][1].search(classname) is not None:
                    self.tags.add(i)

    def get_list(self):
        return [self.reverse[i] for i in self.tags]

    def __contains__(self, key):
        return key in self.tags

    def __str__(self):
        return str([self.reverse[i] for i in self.tags])

    def empty(self):
        return self.tags == set()
