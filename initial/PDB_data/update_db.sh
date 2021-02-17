
# Download latest files from the Protein Data Bank
curl ftp://ftp.wwpdb.org/pub/pdb/derived_data/pdb_entry_type.txt > pdb_entry_type.txt
curl ftp://ftp.wwpdb.org/pub/pdb/derived_data/index/entries.idx > entries.idx

# Insert new proteins into PKPDB
python3 read_entry_type.py
python3 read_entries.py
