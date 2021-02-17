from db import session, Protein, PDB, Residue, Pk
import os
from typing import Generator, Tuple

PK_MOD = {
    "ASP": 3.79,
    "CTR": 2.90,
    "CYS": 8.67,
    "GLU": 4.20,
    "HIS": 6.74,
    "LYS": 10.46,
    "NTR": 7.99,
    "TYR": 9.59,
}


def download_pdb(pdb_idcode: str) -> str:
    # Get the pdb file from PDB
    cmd = (
        f"wget https://files.rcsb.org/download/{pdb_idcode}.pdb.gz;"
        f"gunzip -f {pdb_idcode}.pdb.gz"
    )
    os.system(cmd)

    fname = f"{pdb_idcode}.pdb"
    return fname


def get_pdb(pid: int, idcode: str, prefix="") -> Tuple[int, PDB, str]:
    pdb_content = session.query(PDB.pdb_file).filter_by(pid=pid).first()[0]
    fname = f"{prefix}{idcode}.pdb"
    with open(fname, "w") as f_new:
        f_new.write(pdb_content)

    nres = session.query(Protein.nres).filter(Protein.pid == pid).first()[0]
    CUR_PDB = session.query(PDB).filter_by(pid=pid)
    return nres, CUR_PDB, fname


def download_fasta(idcode: str, pid: int) -> str:
    # Get the pdb file from PDB
    cmd = f"wget https://www.rcsb.org/fasta/entry/{idcode}"
    os.system(cmd)

    with open(f"{idcode}") as f:
        fasta_file = f.read()

    return fasta_file


def idcodes_to_process(fname) -> Generator:
    with open(fname) as f:
        for line in f:
            idcode = line.strip()
            yield idcode


def read_pdb_line(line):
    aname = line[12:16].strip()
    anumb = int(line[5:11].strip())
    b = line[16]
    resname = line[17:21].strip()
    chain = line[21]
    resnumb = int(line[22:26])
    icode = line[26]
    x = float(line[30:38])
    y = float(line[38:46])
    z = float(line[46:54])
    return (aname, anumb, b, resname, chain, resnumb, x, y, z, icode)


def get_sites(pid: str) -> dict:
    sites = (
        session.query(
            Residue.chain, Residue.residue_number, Residue.residue_type, Residue.resid
        )
        .filter(Residue.resid == Pk.resid)
        .filter(Residue.pid == pid)
        .filter(Pk.pk != None)
    )

    chain_sites = {}
    for chain, resnumb, resname, resid in sites:
        if chain not in chain_sites.keys():
            chain_sites[chain] = {}
        chain_sites[chain][resnumb] = [resname, resid]

    return chain_sites
