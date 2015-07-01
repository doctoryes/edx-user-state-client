from setuptools import setup

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
    ]
)
