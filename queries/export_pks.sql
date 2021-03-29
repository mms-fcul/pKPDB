COPY (
    select idcode, chain, residue_type as residue_name, residue_number, pk
    from protein, residue, pk
    where protein.pid = residue.pid and 
          residue.resid = pk.resid and 
          pk.pk is not null
) TO '/tmp/pkas.csv' DELIMITER ';' csv header;

\! echo "EXPORTED /tmp/pkas.csv";