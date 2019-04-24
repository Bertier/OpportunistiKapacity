from setuptools import setup
setup(
  name='opportunistikapacity',
  packages=['opportunistikapacity'],
  version='0.0.1',
  license='MIT',
  description='A simple library to compute the contact capacity in mobility/contact traces',
  author='Clement Bertier',
  author_email='clement.bertier@lip6.fr',
  url='https://github.com/Bertier/OpportunistiKapacity',
  download_url='https://github.com/user/reponame/archive/v_01.tar.gz',    # I explain this later on
  keywords=['CONTACT', 'OPPORTUNISTIC', 'CAPACITY', 'MOBILITY', 'DATA', 'TRACE', 'VANET', 'MANET'],
  install_requires=[            # I get to this in a second
          'numpy',
          'scipy',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Scientists',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',

    'License :: OSI Approved :: MIT License',   # Again, pick a license

    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
)
