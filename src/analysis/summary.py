import os
import sys

file_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, f"{file_dir}/../")
from db import session, Protein, Pk_sim, SequenceAlign, Pk, Residue_props


if __name__ == "__main__":

    n_prots = (
        session.query(SequenceAlign.rcsb_id)
        .join(Pk_sim, Pk_sim.pid == SequenceAlign.pid)
        .filter(Pk_sim.tit_curve != None)
        .distinct()
        .count()
    )

    n_structures = (
        session.query(Pk_sim.pid).filter(Pk_sim.tit_curve != None).distinct().count()
    )

    n_pis = (
        session.query(Pk_sim.pid)
        .filter(Pk_sim.isoelectric_point != None)
        .filter(Pk_sim.isoelectric_point_limit == None)
        .distinct()
        .count()
    )

    n_pkas = session.query(Pk.pkid).filter(Pk.dpk != None).count()

    n_sasa = (
        session.query(Residue_props.resid)
        .distinct()
        .filter(Residue_props.sasa_r != None)
        .count()
    )

    md_table = f"""
    | Proteins | Structures | Isoelectric Points | pKa values | relative SASA |
    | {n_prots:8} | {n_structures:10} | {n_pis:18} | {n_pkas:10} | {n_sasa:13} |
    """
    print(md_table)