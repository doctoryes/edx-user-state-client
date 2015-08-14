from setuptools import setup

extras_require = dict(
    django=[
        'django>=1.4,<=1.5',
        'dogapi'
    ],
)

extras_require['all'] = set().union(*extras_require.values())

setup(
    name="edx_user_state_client",
    version="1.0.0",
    packages=[
        "edx_user_state_client",
        "edx_user_state_client.backends",
        "edx_user_state_client.backends.django",
        "edx_user_state_client.backends.django.user_state_client",
    ],
    install_requires=[
        "PyContracts",
        "opaque-keys",
        "xblock",
    ],
    extras_require=extras_require
)
