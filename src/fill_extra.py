import sys

from db import (
    session,
    Protein,
    Pk_sim,
)  # , Protein, Pk_sim, PDB, Residue, Pk, Sim_settings
from utils import idcodes_to_process
from extra_properties import solvent_exposure, fasta, contact_map, annotations


def run_all(pid: int, idcode: str) -> None:

    # contact_map
    contact_map.save_contact_map(idcode, pid)

    # residue_props
    solvent_exposure.calc_all_metrics(pid, idcode)

    # fasta
    fasta.save_fasta(idcode, pid)

    # similarity
    fasta.save_similar_idcodes(idcode, pid)

    # annotations
    annotations.save_experimental_conditions(idcode, pid)
    annotations.save_sequence_info(idcode, pid)
    annotations.save_structure_quality(idcode, pid)


if __name__ == "__main__":

    # for idcode in idcodes_to_process("urgent_idcodes"):

    idcode = sys.argv[1]
    print("############", idcode, "############")

    pid = session.query(Protein.pid).filter_by(idcode=idcode).first()[0]
    run_all(pid, idcode)
