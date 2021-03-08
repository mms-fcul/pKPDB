select 
    downloaded.a as downloaded, 
    simed.a as started_sim, 
    simed.a - (inserted.a+failed.a) as running, 
    inserted.a as finished, failed.a * 100 / simed.a  as failed_perc,
    dpks.a as total_dpks
from 
    (select count(nres) as a from protein where nres is not null) as downloaded,
    (select count(settid) as a from pk_sim) as inserted,
    (select count(error_description) as a from pk_sim) as failed,
    (select count(*) as a from protein where nres <500) as simed,
    (select count(dpk) as a from pk where dpk is not null) as dpks
;
