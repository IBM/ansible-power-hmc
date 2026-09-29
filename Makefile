ifndef PYTHON_VERSION
	PYTHON_VERSION := $(shell python -c "import sys; print('%d.%d' % sys.version_info[0:2])")
endif

ifndef MODULE
	MODULE = plugins/modules/*.py
endif


ifndef TEST
	TEST = tests/unit/plugins/modules/*.py
endif

DEPRECATED = plugins/modules/_*.py
TEST_OMIT = $(DEPRECATED),tests/*

######################################################################################
# utility targets
######################################################################################

.PHONY: help
help:
	@echo "usage: make <target>"
	@echo ""
	@echo "target:"
	@echo "install-requirements ANSIBLE_VERSION=<version> 	install all requirements"
	@echo "install-ansible ANSIBLE_VERSION=<version>	install ansible: 2.9, 3, or 4"
	@echo "install-ansible-devel-branch			install ansible development branch"
	@echo "install-sanity-test-requirements		install python modules needed to \
	run sanity testing"
	@echo "install-unit-test-requirements 			install python modules needed \
	run unit testing"
	@echo "install-ansible-lint"
	@echo "module-lint MODULE=<module path> 		lint ansible module"         
	@echo "unit-test TEST=<test path>			run unit test suite for the collection"
	@echo "clean						clean junk files"

.PHONY: clean
clean:
	@rm -rf tests/unit/plugins/modules/__pycache__
	@rm -rf tests/unit/plugins/modules/common/__pycache__
	@rm -rf plugins/modules/__pycache__
	@rm -rf ibm-power_hmc-*

######################################################################################
# installation targets
######################################################################################

.PHONY: install-requirements
install-requirements: install-ansible install-sanity-test-requirements \
		install-unit-test-requirements install-ansible-lint
	python -m pip install --upgrade pip

.PHONY: install-ansible
install-ansible:
	python -m pip install --upgrade pip
ifdef ANSIBLE_VERSION
	python -m pip install ansible==$(ANSIBLE_VERSION).*
else
	python -m pip install ansible
endif

.PHONY: install-ansible-devel-branch
install-ansible-devel-branch:
	python -m pip install --upgrade pip
	python -m pip install https://github.com/ansible/ansible/archive/devel.tar.gz \
	--disable-pip-version-check

.PHONY: install-sanity-test-requirements
install-sanity-test-requirements:
	python -m pip install -r tests/sanity/sanity.requirements

.PHONY: install-unit-test-requirements
install-unit-test-requirements:
	python -m pip install -r tests/unit/unit.requirements

.PHONY: install-ansible-lint
install-ansible-lint:
	python -m pip install ansible-lint

######################################################################################
# testing targets
######################################################################################

.PHONY: lint
lint: module-lint

.PHONY: module-lint
module-lint:
	ansible-test sanity --python $(PYTHON_VERSION) --skip-test shebang --skip-test ignores
	flake8 plugins/modules/* --max-line-length=160 --ignore=E402,W503 
	flake8 plugins/module_utils/* --max-line-length=160 --ignore=E402,W503
	flake8 plugins/inventory/* --max-line-length=160 --ignore=E402,W503 --exclude=plugins/inventory/*.yaml,plugins/inventory/*.yml
	python -m pycodestyle --ignore=E402,W503 --max-line-length=160 $(MODULE)

.PHONY: prep-collection
prep-collection:
	ansible-galaxy collection build
	ansible-galaxy collection install ibm-power_hmc*

.PHONY: unit-test
unit-test: prep-collection
	cd ~/.ansible/collections/; \
	python -m pytest

.PHONY: ansible-lint
ansible-lint: 
	cd playbooks && ansible-lint --exclude=hmc_users_input.yaml,partitions.power_hmc.yml,source.power_hmc.yml .
	python -m ansiblelint --profile production --exclude tests/integration/ --exclude tests/unit/
