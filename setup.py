from setuptools import setup

setup(
    name="edx_user_state_client",
    version="1.0.4",
    packages=[
        "edx_user_state_client",
    ],
    install_requires=[
        "PyContracts>=1.7.1,<2.0.0",
        "edx-opaque-keys>=0.2.0,<1.0.0",
        "xblock>=0.4,<2.0.0",
    ]
)
