"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
Modified by Madoshakalaka@Github (dependency links added)
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path

# io.open is needed for projects that support Python 2.7
# It ensures open() defaults to text mode with universal newlines,
# and accepts an argument to specify the text encoding
# Python 3 only projects can skip this import
from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    # This is the name of your project. The first time you publish this
    # package, this name will be registered for you. It will determine how
    # users can install this project, e.g.:
    #
    # $ pip install sampleproject
    #
    # And where it will live on PyPI: https://pypi.org/project/sampleproject/
    #
    # There are some restrictions on what makes a valid project name
    # specification here:
    # https://packaging.python.org/specifications/core-metadata/#name
    name="qiskit-aws-braket-provider",  # Required
    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    #
    # For a discussion on single-sourcing the version across setup.py and the
    # project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version="0.0.1",  # Required
    # This is a one-line description or tagline of what your project does. This
    # corresponds to the "Summary" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#summary
    description="A provider for qiskit to access quantum devices through AWS Braket",  # Optional
    # This is an optional longer description of your project that represents
    # the body of text which users will see when they visit PyPI.
    #
    # Often, this is the same as your README, so you can just read it in from
    # that file directly (as we have already done above)
    #
    # This field corresponds to the "Description" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-optional
    long_description=long_description,  # Optional
    # Denotes that our long_description is in Markdown; valid values are
    # text/plain, text/x-rst, and text/markdown
    #
    # Optional if long_description is written in reStructuredText (rst) but
    # required for plain-text or Markdown; if unspecified, "applications should
    # attempt to render [the long_description] as text/x-rst; charset=UTF-8 and
    # fall back to text/plain if it is not valid rst" (see link below)
    #
    # This field corresponds to the "Description-Content-Type" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-content-type-optional
    long_description_content_type="text/markdown",  # Optional (see note above)
    # This should be a valid link to your project's main homepage.
    #
    # This field corresponds to the "Home-Page" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#home-page-optional
    url="https://github.com/carstenblank/qiskit-aws-braket-provider",  # Optional
    # This should be your name or the name of the organization which owns the
    # project.
    author="Carsten Blank",  # Optional
    # This should be a valid email address corresponding to the author listed
    # above.
    author_email="blank@data-cybernetics.com",  # Optional
    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Physics",
        # Pick your license as you wish
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # These classifiers are *not* checked by 'pip install'. See instead
        # 'python_requires' below.
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
    ],
    # This field adds keywords for your project which will appear on the
    # project page. What does your project relate to?
    #
    # Note that this is a string of words separated by whitespace, not a list.
    keywords="sample setuptools development",  # Optional
    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    #   py_modules=["my_module"],
    #
    packages=find_packages(where='src', exclude=["contrib", "docs", "tests"]),  # Required
    package_dir={"": "src"},
    # Specify which Python versions you support. In contrast to the
    # 'Programming Language' classifiers above, 'pip install' will check this
    # and refuse to install the project if the version does not match. If you
    # do not support Python 2, you can simplify this to '>=3.5' or similar, see
    # https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4",
    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        "amazon-braket-default-simulator==1.0.0.post2; python_version >= '3.7'",
        "amazon-braket-schemas==1.0.2.post1; python_version >= '3.7'",
        "amazon-braket-sdk==1.1.1.post1",
        "attrs==20.2.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "backoff==1.10.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
        "boltons==20.2.1",
        "boto3==1.15.1",
        "boto3-stubs==1.15.1.0",
        "botocore==1.18.1",
        "certifi==2020.6.20",
        "cffi==1.14.3",
        "chardet==3.0.4",
        "cryptography==3.1; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
        "cython==0.29.21; python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "decorator==4.4.2",
        "dill==0.3.2; python_version >= '2.6' and python_version != '3.0'",
        "dlx==1.0.4",
        "docplex==2.15.194",
        "fastdtw==0.3.4",
        "fastjsonschema==2.14.5",
        "h5py==2.10.0",
        "idna==2.10; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "inflection==0.5.1; python_version >= '3.5'",
        "jmespath==0.10.0; python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "joblib==0.16.0; python_version >= '3.6'",
        "jsonschema==3.2.0",
        "more-itertools==8.5.0; python_version >= '3.5'",
        "mpmath==1.1.0",
        "multitasking==0.0.9",
        "nest-asyncio==1.4.0; python_version >= '3.5'",
        "networkx==2.5; python_version >= '3.6'",
        "ntlm-auth==1.5.0; python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "numpy==1.19.2; python_version >= '3.6'",
        "opt-einsum==3.3.0; python_version >= '3.5'",
        "packaging==20.4; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "pandas==1.1.2; python_full_version >= '3.6.1'",
        "pint==0.16",
        "ply==3.11",
        "psutil==5.7.2; python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "pybind11==2.5.0",
        "pycparser==2.20; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "pydantic==1.6.1; python_version >= '3.6'",
        "pyparsing==2.4.7; python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "pyrsistent==0.17.3; python_version >= '3.5'",
        "python-constraint==1.4.0",
        "python-dateutil==2.8.1; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "pytz==2020.1",
        "qiskit==0.20.0",
        "qiskit-aer==0.6.1",
        "qiskit-aqua==0.7.5; python_version >= '3.5'",
        "qiskit-ibmq-provider==0.8.0; python_version >= '3.5'",
        "qiskit-ignis==0.4.0; python_version >= '3.5'",
        "qiskit-terra==0.15.1; python_version >= '3.5'",
        "quandl==3.5.2; python_version >= '3.5'",
        "requests==2.24.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
        "requests-ntlm==1.1.0",
        "retworkx==0.5.0; python_version >= '3.5'",
        "s3transfer==0.3.3",
        "scikit-learn==0.23.2; python_version >= '3.6'",
        "scipy==1.5.2; python_version >= '3.6'",
        "six==1.15.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
        "sympy==1.6.2; python_version >= '3.5'",
        "threadpoolctl==2.1.0; python_version >= '3.5'",
        "urllib3==1.25.10; python_version != '3.4'",
        "websockets==8.1; python_version >= '3.7'",
        "yfinance==0.1.54",
    ],  # Optional
    # List additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install sampleproject[dev]
    #
    # Similar to `install_requires` above, these must be valid existing
    # projects.
    extras_require={
        "dev": [
            "appdirs==1.4.4",
            "atomicwrites==1.4.0; sys_platform == 'win32'",
            "attrs==20.2.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "black==19.10b0; python_version >= '3.6'",
            "cached-property==1.5.1",
            "cerberus==1.3.2",
            "certifi==2020.6.20",
            "chardet==3.0.4",
            "click==7.1.2; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "colorama==0.4.3; sys_platform == 'win32'",
            "distlib==0.3.1",
            "idna==2.10; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "iniconfig==1.0.1",
            "more-itertools==8.5.0; python_version >= '3.5'",
            "orderedmultidict==1.0.1",
            "packaging==20.4; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "pathspec==0.8.0",
            "pep517==0.8.2",
            "pip-shims==0.5.3; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "pipenv-setup==3.1.1",
            "pipfile==0.0.2",
            "plette[validation]==0.2.3; python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "pluggy==0.13.1; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "py==1.9.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "pyparsing==2.4.7; python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "pytest==6.0.2",
            "python-dateutil==2.8.1; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "regex==2020.7.14",
            "requests==2.24.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "requirementslib==1.5.13; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "six==1.15.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "toml==0.10.1",
            "tomlkit==0.7.0; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "typed-ast==1.4.1",
            "urllib3==1.25.10; python_version != '3.4'",
            "vistir==0.5.2; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "wheel==0.35.1; python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
        ]
    },  # Optional
    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # Sometimes you’ll want to use packages that are properly arranged with
    # setuptools, but are not published to PyPI. In those cases, you can specify
    # a list of one or more dependency_links URLs where the package can
    # be downloaded, along with some additional hints, and setuptools
    # will find and install the package correctly.
    # see https://python-packaging.readthedocs.io/en/latest/dependencies.html#packages-not-on-pypi
    #
    dependency_links=[],
    # If using Python 2.6 or earlier, then these have to be included in
    # MANIFEST.in as well.
    # package_data={"sample": ["package_data.dat"]},  # Optional
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    #
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[("my_data", ["data/data_file"])],  # Optional
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    # For example, the following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:
    # entry_points={"console_scripts": ["sample=sample:main"]},  # Optional
    # List additional URLs that are relevant to your project as a dict.
    #
    # This field corresponds to the "Project-URL" metadata fields:
    # https://packaging.python.org/specifications/core-metadata/#project-url-multiple-use
    #
    # Examples listed include a pattern for specifying where the package tracks
    # issues, where the source is hosted, where to say thanks to the package
    # maintainers, and where to support the project financially. The key is
    # what's used to render the link text on PyPI.
    project_urls={  # Optional
        "Bug Reports": "https://github.com/carstenblank/qiskit-aws-braket-provider/issues",
        "Source": "https://github.com/carstenblank/qiskit-aws-braket-provider",
    },
)
