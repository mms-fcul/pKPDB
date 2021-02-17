import sys

from db import (
    session,
    Protein,
    Pk_sim,
)  # , Protein, Pk_sim, PDB, Residue, Pk, Sim_settings
from utils import idcodes_to_process
from extra_properties import solvent_exposure, fasta

# from prep_closest_res import run_prep_closest_res
# from prep_hse import calc_extra_properties
# from prep_seqalign import download_fasta, run_mmseqs
# from prep_residues import run_around_seq


def run_all(pid: int, idcode: str) -> None:

    # closest15_anames, closest15_dists
    # run_prep_closest_res(pdbDB, idcode) # WARNING: MISSING THE MOST IMPORTANT PARAMETER

    # hse, residue depth, solvent exposure, dssp...
    solvent_exposure.calc_all_metrics(pid, idcode)

    # fasta_file
    fasta.save_fasta(idcode, pid)

    # cluster090
    fasta.save_similar_idcodes(idcode, pid)


if __name__ == "__main__":

    # for idcode in idcodes_to_process("urgent_idcodes"):

    idcode = sys.argv[1]
    print("############", idcode, "############")

    pid = session.query(Protein.pid).filter_by(idcode=idcode).first()[0]
    run_all(pid, idcode)
