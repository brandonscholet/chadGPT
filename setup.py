from setuptools import setup, find_packages

setup(
    name='chadgpt',
    version='0.1.0',
    description='Your description of chadgpt here',
    author='Brandon',
    author_email='brandon@scholet.net',
    url='https://github.com/brandonscholet/chadgpt',
    packages=find_packages(),
    install_requires=[
        'openai',
        'speechrecognition',
        'gtts',
    ],
	entry_points={
        'console_scripts': [
            'chadgpt = chadgpt.main:do_the_thing',
        ],
    },
)
