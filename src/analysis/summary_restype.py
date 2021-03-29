import os
import sys

file_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, f"{file_dir}/../")
from db import session, Protein, Pk_sim, SequenceAlign, Pk, Residue_props, Residue
from db import db

if __name__ == "__main__":
    # $#examples$, $#structures$, $pK_{water}$, $<shift>$, $shift_{stdev}$, $<sasa_{r}>$
    n_pkas = session.query(Pk.pkid).filter(Pk.dpk != None).count()

    query = """
        SELECT 
            res.residue_type as res_type, 
            count(*) as res_total, 
            count(distinct pid), 
            round(AVG(Pk.pk)::numeric,2), 
            round(STDDEV(Pk.pk)::numeric,2), 
            round(AVG(props.sasa_r)::numeric,2),
            round(STDDEV(props.sasa_r)::numeric,2)
        FROM Residue as res
        LEFT JOIN Pk ON Pk.resid = res.resid
        LEFT JOIN Residue_props as props ON props.resid = res.resid
        WHERE Pk.dpk is not null
        GROUP BY res.residue_type
        ORDER BY count(*) DESC
    """
    results = db.execute(query).fetchall()

    md_table = "| residue | examples | % examples | structures | Avg pKa | StdDev pKa | Avg SASA_r | StdDev pKa |\n"
    for res in results:
        (restype, n_res, n_structs, avg_pk, stdev_pk, avg_sasa, stdev_sasa) = res
        perc_res = round(n_res / n_pkas * 100, 2)

        md_line = f"| {restype:7} | {n_res:8} | {perc_res:10} | {n_structs:10} | {avg_pk:7} | {stdev_pk:10} | {avg_sasa:10} | {stdev_sasa:10} | \n"
        md_table += md_line

    print(md_table)