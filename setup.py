import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'dropq/_version.py'
versioneer.versionfile_build = 'dropq/_version.py'
versioneer.tag_prefix = '' # tags are like 1.2.0
versioneer.parentdir_prefix = 'dropq-' # dirname like 'dropq-1.2.0'

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.md') as f:
        longdesc = f.read()

config = {
    'description': 'drop-Q algorithm',
    'description':'dropq',
    'long_description':longdesc,
    'version': versioneer.get_version(),
    'cmdclass': versioneer.get_cmdclass(), 
    'packages': ['dropq'],
    'include_package_data': True,
    'name': 'dropq',
    'classifiers': [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    'tests_require': ['pytest']
}

setup(**config)
