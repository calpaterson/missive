from setuptools import setup, find_packages

VERSION = open("VERSION").read().strip()

setup(
    name="missive",
    version=VERSION,
    packages=find_packages(exclude=["tests.*", "tests"]),
    package_data={"missive": ["py.typed"]},
    include_package_data=True,
    zip_safe=True,
    install_requires=["flask~=1.1.1",],
    extras_require={
        "tests": ["pytest~=5.3.1", "pytest-cov~=2.8.1"],
        "dev": [
            "wheel~=0.33.6",
            "black~=19.10b0",
            "mypy~=0.750",
            "bpython~=0.18",
            "flake8==3.7.9",
        ],
    },
)
