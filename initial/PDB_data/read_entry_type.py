import sys

sys.path.insert(1, "../../src/")
from db import PKPDB

DB = PKPDB()

with open("pdb_entry_type.txt") as f:
    for line in f:
        cols = line.strip().split("\t")
        pdbcode, p_type, exp = cols
        if DB.check_pdbcode_exists(pdbcode):
            sql_query = f"""
UPDATE Protein
SET PROTEIN_TYPE = '{p_type}'
WHERE IDCODE = '{pdbcode}'"""
            DB.exec_statement(sql_query)
        else:
            sql_query = f"""
INSERT INTO Protein(IDCODE, PROTEIN_TYPE)
VALUES ('{pdbcode}', '{p_type}') """
            DB.exec_statement(sql_query)

DB.commit()
print("Successfully updated PROTEIN: PROTEIN_TYPE")
