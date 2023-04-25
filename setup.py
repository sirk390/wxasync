from setuptools import setup

setup(name='wxasync',
      version='0.49',
      description='asyncio for wxpython',
      long_description='wxasync it a library for using python 3 asyncio (async/await) with wxpython.',
      url='http://github.com/sirk390/wxasync',
      author='C.Bodt',
      author_email='sirk390@gmail.com',
      license='MIT',
      package_dir={'': 'src'},
      install_requires=[
          'wxpython',
      ],
      python_requires=">=3.7",
      py_modules=['wxasync'],
      zip_safe=True,
)
