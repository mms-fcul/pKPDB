# PKPDB

A database of theoretical pK values obtained with pypKa

# Create/Update Protein Data Bank proteins

dbs/init.sql contains the schema of the database

dbs/update_db.sh downloads the latest entries to the Protein Data Banks and inserts them into the database

```
cd initial/
psql -d pkpdb -f init.sql

cd PDB_data/
bash update_db.sh
```

# Add proteins to the database

```
# Add a random protein
python3 fill.py

# Add the protein with the IDCODE <IDCODE>
python3 fill.py --idcode <IDCODE>
```

Extra options:
- ncpus NCPUS
- verbose {DEBUG,INFO,WARNING}
- nres-limit NRES_LIMIT

# Dependencies

```
python3 -m pip install psycopg2-binary sqlalchemy pypka biopython
```

[mmseqs](https://github.com/soedinglab/MMseqs2) and [DSSP](https://github.com/cmbi/dssp) are also required for running extra_properties/solvent_exposure.py