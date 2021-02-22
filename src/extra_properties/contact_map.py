import os
import sys
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from typing import Tuple, Dict, List, Any, Optional

file_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, f"{file_dir}/../")
from db import session, Protein, PDB, Contact_map
from utils import get_sites, get_pdb

titratable_hs = {
    "NT3": ("H1", "H2", "H3"),
    "LY3": ("HZ1", "HZ2", "HZ3"),
    "HI2": ("HD1", "HD2", "HE1", "HE2"),
    "CT4": ("HO11", "HO12", "HO21", "HO22"),
    "AS4": ("HD11", "HD12", "HD21", "HD22"),
    "GL4": ("HE11", "HE12", "HE21", "HE22"),
    "CY3": ("HG1", "HG2", "HG3"),
    "TY2": ("HH1", "HH2"),
    "TH3": ("HG1", "HG2", "HG3"),
    "SE3": ("HG1", "HG2", "HG3"),
}


class atoms_distances:
    def __init__(self):
        self.atom1 = None
        self.atom2 = None
        self.distance = None


def read_pdb_line(line: str) -> tuple:
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


def dist_between(
    x: float, y: float, z: float, x2: float, y2: float, z2: float
) -> float:
    return (x - x2) ** 2 + (y - y2) ** 2 + (z - z2) ** 2


def clean_pdb_atoms(pid: int) -> list:
    """Removes all atoms from pdb_f that are not Nitrogen, Sulfur, or Oxygen

    Args:
        pid (int)

    Returns:
        list: each line is a original line from pdb_f where
              the atom type is either a Nitrogen, Sulfur, or Oxygen
    """
    pdb_content = session.query(PDB.pdb_file_hs).filter_by(pid=pid).first()[0]

    short_pdb = []
    for line in pdb_content.splitlines():
        if line.startswith("ATOM "):
            line_cols = read_pdb_line(line)
            (aname, anumb, b, resname, chain, resnumb, x, y, z, icode) = line_cols

            if b not in (" ", "A") or icode != " ":
                continue

            if aname[0] not in "NOS":
                if resname not in titratable_hs:
                    continue
                if aname not in titratable_hs[resname]:
                    continue

            short_pdb.append((aname, anumb, resname, chain, resnumb, x, y, z))

            # with open("ccc_short.pdb", "a") as f:
            #    f.write(line.strip() + "\n")

    return short_pdb


def calc_dists(short_pdb: list, pid: int) -> None:

    df = pd.DataFrame(
        short_pdb[:5],
        columns=["aname", "anumb", "resname", "chain", "resnumb", "x", "y", "z"],
    )

    dists = pdist(df[["x", "y", "z"]])
    # squareform(dists)
    return df, dists


aa_atoms = {
    "ASP": ["OD1", "OD2"],
    "CTR": ["OD1", "OXT"],
    "CYS": ["SG"],
    "GLU": ["OE1", "OE2"],
    "HIS": ["ND1", "NE2"],
    "LYS": ["NZ"],
    "NTR": ["N"],
    "TYR": ["OH"],
}


def save_contact_map(idcode: str, pid: int) -> None:

    short_pdb = clean_pdb_atoms(pid)

    df, dists = calc_dists(short_pdb, pid)

    new_cm = Contact_map(
        pid=pid,
        distances=dists.tolist(),
        anumbs=df.anumb.values.tolist(),
        anames=df.aname.values.tolist(),
        chains=df.chain.values.tolist(),
        resnumbs=df.resnumb.values.tolist(),
        resnames=df.resname.values.tolist(),
    )  #        chains = df.chain.values,
    session.add(new_cm)
    session.commit()


if __name__ == "__main__":

    # for idcode in idcodes_to_process("urgent_idcodes"):

    idcode = sys.argv[1]
    print("############", idcode, "############")

    pid = session.query(Protein.pid).filter_by(idcode=idcode).first()[0]

    save_contact_map(idcode, pid)
