import json
import os
_resources = None

if _resources is None:
    root = os.path.dirname(os.path.realpath(__file__))
    resfile = os.path.join(root, "public.json")

    if os.path.isfile(resfile):
        with open(resfile, "r") as fp:
            _resources = json.load(fp)
    else:
        # TODO raise error instead?
        _resources = {}

SYSTEM_RESOURCES = {
    "attributes": {
        "forward": {k: v for k, v in _resources['attr'].items()},
        "inverse": {v: k for k, v in _resources['attr'].items()}
    },
    "styles": {
        "forward": {k: v for k, v in _resources['style'].items()},
        "inverse": {v: k for k, v in _resources['style'].items()}
    }
}
