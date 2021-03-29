COPY (
    select idcode, array_to_string(cluster, ',', '') as cluster
    from protein, similarity
    where protein.pid = similarity.pid and 
          similarity.cluster is not null
) TO '/tmp/similarity090.csv' DELIMITER ';' csv header;

\! echo "EXPORTED /tmp/similarity.csv";