from setuptools import setup
setup(
  name='opportunistikapacity',         # How you named your package folder (MyLib)
  packages=['opportunistikapacity'],   # Chose the same as "name"
  version='0.0.1',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description='A simple library to compute the contact capacity in mobility/contact traces',   # Give a short description about your library
  author='Clement Bertier',                   # Type in your name
  author_email='clement.bertier@lip6.fr',      # Type in your E-Mail
  url='https://github.com/user/reponame',   # Provide either the link to your github or to your website
  download_url='https://github.com/user/reponame/archive/v_01.tar.gz',    # I explain this later on
  keywords=['SOME', 'MEANINGFULL', 'KEYWORDS'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'numpy',
          'scipy',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Scientists',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',

    'License :: OSI Approved :: MIT License',   # Again, pick a license

    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.5',
  ],
)
