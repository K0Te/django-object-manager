from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='django-object-manager',
    version='0.0.7',
    description='Django object manager for tests',
    license='BSD',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/K0Te/django-object-manager',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='django tests',
    install_requires=['django'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov', 'pytest-django'],
    packages=find_packages(exclude=['tests']),
    project_urls={
        'Bug Reports': 'https://github.com/K0Te/django-object-manager/issues',
        'Source': 'https://github.com/K0Te/django-object-manager',
    },
)
