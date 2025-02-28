from setuptools import setup

setup(
    name='backlink-organizer',
    version='1.0',
    packages=[''],
    install_requires=[
        'flask',
        'pyinstaller',
    ],
    entry_points={
        'console_scripts': [
            'backlink-organizer=app:app.run',
        ],
    },
)