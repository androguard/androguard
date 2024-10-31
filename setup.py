from setuptools import find_packages, setup

from androguard import __version__

with open('requirements.txt', 'r') as fp:
    install_requires = fp.read().splitlines()

setup(
    name='androguard',
    description='Androguard is a full python tool to play with Android files.',
    version=__version__,
    packages=find_packages(),
    license="Apache Licence, Version 2.0",
    url="https://github.com/androguard/androguard",
    install_requires=install_requires,
    package_data={
        "androguard.core.api_specific_resources": [
            "aosp_permissions/*.json",
            "api_permission_mappings/*.json",
        ],
        "androguard.core.resources": ["public.xml"],
    },
    entry_points={
        'console_scripts': ['androguard = androguard.cli.cli:entry_point']
    },
    setup_requires=['setuptools'],
    python_requires='>=3.9',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Security',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
)
