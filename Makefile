default: test quality docs

test:
	tox

docs:
	cd doc && make html

quality:
	pep8
	pylint edx_user_state_client

package:
	python setup.py register sdist upload
