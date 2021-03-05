#! /usr/bin/python3

import os
import sys
import logging
import subprocess

file_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, f"{file_dir}/../")
from db import session, Protein, Fasta, Similarity
from utils import download_fasta


def save_fasta(idcode: str, pid: int) -> None:
    exists_fasta = session.query(Fasta.pid).filter_by(pid=pid).first()
    if exists_fasta:
        logging.info(f"{idcode} fasta file already exists.")
        return

    fasta_file = download_fasta(idcode, pid)
    if fasta_file:
        new_fasta = Fasta(pid=pid, fasta_file=fasta_file)
        session.add(new_fasta)
        session.commit()


def get_similar_idcodes(idcode: str, pid: int, seqid: float = 0.9) -> list:
    if not os.path.isfile(idcode):
        fasta_file = download_fasta(idcode, pid)
        if not fasta_file:
            logging.error("Failed to dowload FASTA of {}".format(idcode))

    succeeded = False
    try:
        output_f = f"alnRes_{idcode}.m8"
        DB_FILE_PATH = file_dir + "/DB_PDB/DB_PDB"

        cmd = f"mmseqs easy-search {idcode} {DB_FILE_PATH} {output_f} tmp --min-seq-id {seqid} --max-seqs 1000000"
        subprocess.run(
            cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        succeeded = True
    except subprocess.CalledProcessError as e:
        logging.warning(
            f"mmseqs did not run successfully\tMessage: {e.stderr.decode('ascii')}"
        )

    similar = None
    if succeeded:
        similar = []
        with open(output_f) as f:
            for line in f:
                exc_idcode, _ = line.strip().split()[1].split("_")
                if exc_idcode != idcode:
                    similar.append(exc_idcode)

        os.system(f"rm -f {idcode} {output_f}")

    return similar


def save_similar_idcodes(idcode: str, pid: int, seqid: float = 0.9):

    exists_cluster = session.query(Similarity.pid).filter_by(pid=pid).first()
    if exists_cluster:
        logging.info(f"{idcode} similarity cluster already exists.")
        return

    similar = get_similar_idcodes(idcode, pid, seqid=seqid)
    if similar:
        new_cluster = Similarity(pid=pid, cluster=similar, seqid=seqid)
        session.add(new_cluster)
        session.commit()


if __name__ == "__main__":
    # for idcode in idcodes_to_process("urgent_idcodes"):

    idcode = sys.argv[1]
    print("############", idcode, "############")

    pid = session.query(Protein.pid).filter_by(idcode=idcode).first()[0]

    save_fasta(idcode, pid)
    save_similar_idcodes(idcode, pid)
