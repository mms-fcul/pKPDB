select 
    round(tried.a * 100 / total.total::numeric, 1) as tried,
    round(downloaded.a * 100 / total.total::numeric, 1) as downloaded,    
    running.a as running,
    inserted.a as finished, 
    round(failed.a * 100 / (inserted.a+failed.a)::numeric, 1) as failed_perc
from
    (select count(*) as a from pk_sim) as tried, 
    (select count(*) as a from protein where nres is not null and protein_type = 'prot') as downloaded,
    (select count(*) as total from protein where protein_type = 'prot') as total,
    (select count(settid) as a from pk_sim) as inserted,
    (select count(error_description) as a from pk_sim) as failed,    
    (select sum(numbackends) as a from pg_stat_database) as running
;

select
    round((inserted_small.a)* 100 / small.a::numeric, 1) as small,    
    round((inserted_medium.a)* 100 / medium.a::numeric, 1) as medium,    
    round((inserted_large.a)* 100 / large.a::numeric, 1) as large,    
    round((inserted_small.a + inserted_medium.a + inserted_large.a)* 100 / (small.a + medium.a + large.a::numeric), 1) as small_2_large,
    round((inserted_all.a)* 100 / all_prots.a::numeric, 1) as all
from
    (select count(*) as a from protein where nres < 500 and protein_type = 'prot') as small,
    (select count(*) as a from protein where nres < 750 and nres >= 500 and protein_type = 'prot') as medium,
    (select count(*) as a from protein where nres < 1000 and nres >= 750 and protein_type = 'prot') as large,
    (select count(*) as a from protein where nres is not null and protein_type = 'prot') as all_prots,
    (select count(tit_curve) as a from pk_sim, protein where pk_sim.pid = protein.pid and nres < 500) as inserted_small,
    (select count(tit_curve) as a from pk_sim, protein where pk_sim.pid = protein.pid and nres < 750 and nres >= 500) as inserted_medium,
    (select count(tit_curve) as a from pk_sim, protein where pk_sim.pid = protein.pid and nres < 1000 and nres >= 750) as inserted_large,
    (select count(tit_curve) as a from pk_sim, protein where pk_sim.pid = protein.pid) as inserted_all,
    (select count(error_description) as a from pk_sim) as failed
;

select
    small.a as missing_small,
    medium.a as missing_medium,
    large.a as missing_large
from
    (
        select count(*) as a from protein where nres < 500 and protein_type = 'prot' and pid not in 
        (
            select pid from pk_sim where tit_curve is not null or error_description is not null or sim_date >= '2021-03-13'
        )
    ) as small,
    (
        select count(*) as a from protein where nres >= 500 and nres < 750 and protein_type = 'prot' and pid not in 
        (
            select pid from pk_sim where tit_curve is not null or error_description is not null or sim_date >= '2021-03-13'
        )
    ) as medium,
        (
        select count(*) as a from protein where nres >= 750 and nres < 1000 and protein_type = 'prot' and pid not in 
        (
            select pid from pk_sim where tit_curve is not null or error_description is not null or sim_date >= '2021-03-13'
        )
    ) as large
;

select count(dpk) as total_dpks
from pk
where dpk is not null;
