from setuptools import setup
import os


def main():
    setup(
        name='SBMLparser',
        version='0.1',
        description='Dose response curve and drug induced proliferation '
                    '(DIP) rate fits and visualisation',
        author='Jose Juan Tapia',
        author_email='jjtapia@gmail.com',
        url='https://ruleworld.github.io/atomizer/',
        packages=['SBMLparser', 'SBMLparser.writer', 'SBMLparser.utils', 'SBMLparser.atomizer', 'SBMLparser.rulifier'],
        install_requires=['numpy', 'pylru', 'lxml', 'pyyaml'],
        entry_points = {
            'console_scripts': ['sbmlTranslator=SBMLparser.sbmlTranslator:main']
        },
        classifiers=[
            'Intended Audience :: Science/Research',
            'Programming Language :: Python',
            'Topic :: Scientific/Engineering :: Bio-Informatics',
            'Topic :: Scientific/Engineering :: Chemistry',
            'Topic :: Scientific/Engineering :: Medical Science Apps.',
        ]
    )


if __name__ == '__main__':
    main()
