default: test quality docs

test:
	tox

docs:
	cd doc && make html

quality:
	pycodestyle --config=pycodestyle
	pylint edx_user_state_client

package:
	python setup.py register sdist upload
