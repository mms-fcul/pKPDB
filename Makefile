.PHONY: check-space help
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

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

