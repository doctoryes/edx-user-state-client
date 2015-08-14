from setuptools import setup

extras_require = dict(
    django = ['django>=1.4,<=1.5'],
)

extras_require['all'] = set().union(*extras_require.values())

setup(
    name="edx_user_state_client",
    version="1.0.0",
    packages=[
        "edx_user_state_client",
    ],
    install_requires=[
        "PyContracts",
        "opaque-keys",
        "xblock",
    ],
    extras_require = extras_require
)
