SHELL := /bin/bash
RUN ?= runs/1iep-smoke
THREADS ?= 2
SEED ?= 202601
STEP ?= 12

.PHONY: help env docs check-docs fixtures dock smoke quickstart skeleton check report
help:
	@printf '%s\n' 'make env        Create the example environment' 'make dock       Run stages 01–05 (no GROMACS required)' 'make smoke      Run stages 01–12 with 2 ps of production' 'make quickstart Run stages 01–12 with 1 ns of production' 'make check STEP=04 RUN=runs/1iep-dock' 'make skeleton RUN=runs/my-project' 'make report RESULTS=results.csv'
env:
	conda env create -f environment.yml
docs:
	python scripts/build_docs.py
check-docs:
	python scripts/build_docs.py --check
	python scripts/check_docs.py
fixtures:
	cd examples/1iep && sha256sum -c SHA256SUMS
	cd examples/regression && sha256sum -c SHA256SUMS
	cd examples/expected && sha256sum -c SHA256SUMS
	cd environment && sha256sum -c SHA256SUMS
dock:
	THREADS="$(THREADS)" SEED="$(SEED)" bash scripts/run_example.sh dock "$(if $(filter undefined file,$(origin RUN)),runs/1iep-dock,$(RUN))"
smoke:
	THREADS="$(THREADS)" SEED="$(SEED)" bash scripts/run_example.sh smoke "$(RUN)"
quickstart:
	THREADS="$(THREADS)" SEED="$(SEED)" bash scripts/run_example.sh quickstart "$(if $(filter undefined file,$(origin RUN)),runs/1iep-1ns,$(RUN))"
skeleton:
	bash scripts/init_project.sh "$(RUN)"
check:
	bash "scripts/check_$(STEP).sh" "$(RUN)"
report:
	python scripts/results_table.py "$(or $(RESULTS),examples/results-template.csv)"

.PHONY: site
site: docs
	python scripts/build_site.py
