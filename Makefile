.PHONY: check-space help csv-exports
.DEFAULT_GOAL := help
SHELL := /bin/bash

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

help:  ## get help
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

disk-space: ## check disk space used by the database
	psql -d pkpdb -f queries/check_db_size.sql

large-tables: ## check disk space used by the largest tables
	psql -d pkpdb -f queries/check_table_sizes.sql
	
status: ## check the insertion progress
	psql -d pkpdb -f queries/check_insertion_status.sql

connections: ## check the number of active connections
	psql -d pkpdb -f queries/check_connections.sql

csv-exports: ## export csv files of similarity, pIs and pKas
	psql -d pkpdb -f queries/export_similarity.sql
	psql -d pkpdb -f queries/export_pis.sql
	psql -d pkpdb -f queries/export_pks.sql
	
	rm -f ${static_folder}/{similarity090,isoelectric,pkas}.csv*	
	cp /tmp/similarity090.csv ${static_folder}
	cp /tmp/isoelectric.csv ${static_folder}
	cp /tmp/pkas.csv ${static_folder}

	gzip -9 ${static_folder}/similarity090.csv
	gzip -9 ${static_folder}/isoelectric.csv
	gzip -9 ${static_folder}/pkas.csv


