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

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	pip install -q -r requirements/pip_tools.txt
	pip-compile --upgrade --allow-unsafe --rebuild -o requirements/pip.txt requirements/pip.in
	pip-compile --upgrade -o requirements/pip_tools.txt requirements/pip_tools.in
	pip install -qr requirements/pip.txt
	pip install -qr requirements/pip-tools.txt
	pip-compile --upgrade -o requirements/base.txt requirements/base.in
	pip-compile --upgrade -o requirements/doc.txt requirements/doc.in
	pip-compile --upgrade -o requirements/test.txt requirements/test.in
	pip-compile --upgrade -o requirements/ci.txt requirements/ci.in
