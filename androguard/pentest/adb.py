import subprocess

from loguru import logger

def adb(device_id, cmd=None):
    logger.info("ADB: Running on {}:{}".format(device_id, cmd))
    subprocess.run('adb -s {} {}'.format(device_id, cmd), shell=True)
