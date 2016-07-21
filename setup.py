"""Installation script for NEXT."""

from setuptools import setup, find_packages

base_url = 'https://github.com/nextml/NEXT'
__version__ = "0.1.0"

setup(
    name='NEXT',
    version=__version__,
    description='Cloud-based active learning.',
    url=base_url,
    download_url="{}/tarball/{}".format(base_url, __version__),
    author='nextml',
    author_email='contact@nextml.org',
    license='Apache',
    packages=find_packages(),
    package_data={'': ['README.md']},
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'next = ec2.next_ec2:main',
        ],
    },
    install_requires=[]
)
