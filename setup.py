from setuptools import setup

setup(name="switchprint",
      version="zero",
      description="",
      url="https://github.com/Aeva/switchprint",
      author="Aeva Palecek"
      author_email="aeva.ntsc@gmail.com",
      license="GPLv3",
      packages=["switchprint"],
      zip_safe=False,

      entry_points = {
        "console_scripts" : [
            "switchprint=switchprint.switch:daemon",
            ],
        }

      install_requires = [
        "daemon",
        "pyserial",
        ])
      
