COPY (
    select idcode, rcsb_id, isoelectric_point, isoelectric_point_limit
    from protein, pk_sim, sequence_align
    where protein.pid = pk_sim.pid and 
          protein.pid = sequence_align.pid and
          pk_sim.isoelectric_point is not null
) TO '/tmp/isoelectric.csv' DELIMITER ';' csv header;

\! echo "EXPORTED /tmp/isoelectric.csv";