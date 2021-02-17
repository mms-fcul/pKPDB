import sys
import os

from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.HSExposure import HSExposureCA, HSExposureCB, ExposureCN
from Bio.PDB.ResidueDepth import ResidueDepth
from Bio.PDB.DSSP import DSSP

sys.path.insert(1, "../../")
from db import session, Protein, Residue, Residue_props, Pk
from utils import get_pdb, get_sites


def calc_hseCA(model, chain_sites: dict) -> None:
    # HSExposureCA
    hseCA = HSExposureCA(model)
    for residue in hseCA.keys():
        hseCA_u, hseCA_d, hseCA_angle = hseCA[residue]
        chain_id, res_id = residue
        _, resnumb, _ = res_id

        if chain_id in chain_sites and resnumb in chain_sites[chain_id]:
            resid = chain_sites[chain_id][resnumb][1]
            new_res = chain_sites[chain_id][resnumb][2]

            new_res.hseca_u = hseCA_u
            new_res.hseca_d = hseCA_d
            new_res.hseca_angle = hseCA_angle
    session.commit()


def calc_hseCB(model, chain_sites: dict) -> None:
    # HSExposureCB
    try:
        hseCB = HSExposureCB(model)
    except:
        print("HSE CB failed!")
        hseCB = {}

    for residue in hseCB.keys():
        hseCB_u, hseCB_d, hseCB_angle = hseCB[residue]
        chain_id, res_id = residue
        _, resnumb, _ = res_id

        if chain_id in chain_sites and resnumb in chain_sites[chain_id]:
            resid = chain_sites[chain_id][resnumb][1]
            new_res = chain_sites[chain_id][resnumb][2]

            new_res.hsecb_u = hseCB_u
            new_res.hsecb_d = hseCB_d
    session.commit()


def calc_hseCN(model, chain_sites: dict) -> None:
    # HSExposureCN
    hseCN = ExposureCN(model)
    for residue in hseCN.keys():
        exposure = hseCN[residue]
        chain_id, res_id = residue
        _, resnumb, _ = res_id

        if chain_id in chain_sites and resnumb in chain_sites[chain_id]:
            resid = chain_sites[chain_id][resnumb][1]
            new_res = chain_sites[chain_id][resnumb][2]

            new_res.hsecn = exposure
    session.commit()


def calc_msms(model, chain_sites: dict) -> None:
    # ResidueDepth
    try:
        rd = ResidueDepth(model)
    except:
        print("msms failed!")
        rd = {}

    for residue in rd.keys():
        residue_depth, ca_depth = rd[residue]
        chain_id, res_id = residue
        _, resnumb, _ = res_id

        if chain_id in chain_sites and resnumb in chain_sites[chain_id]:
            resid = chain_sites[chain_id][resnumb][1]
            new_res = chain_sites[chain_id][resnumb][2]

            new_res.residue_depth = residue_depth
            new_res.ca_depth = ca_depth
    session.commit()


def calc_dssp(model, chain_sites: dict, pdb_name: str) -> None:
    # DSSP
    #    ============ ===
    #    Tuple Index  Value
    #    ============ ===
    #    0            DSSP index
    #    1            Amino acid
    #    2            Secondary structure
    #    3            Relative ASA
    #    4            Phi
    #    5            Psi
    #    6            NH-->O_1_relidx
    #    7            NH-->O_1_energy
    #    8            O-->NH_1_relidx
    #    9            O-->NH_1_energy
    #    10           NH-->O_2_relidx
    #    11           NH-->O_2_energy
    #    12           O-->NH_2_relidx
    #    13           O-->NH_2_energy
    #    ============ ===

    try:
        dssp = DSSP(model, pdb_name, dssp="mkdssp")
    except:
        dssp = {}
        print("dssp failed!")
    for residue in dssp.keys():
        (
            dssp_i,
            aa,
            sec_struct,
            sasa_r,
            phi,
            psi,
            nh_o1_relidx,
            nh_o1_e,
            o_nh1_relidx,
            o_nh1_e,
            nh_o2_relidx,
            nh_o2_e,
            o_nh2_relidx,
            o_nh2_e,
        ) = dssp[residue]

        chain_id, res_id = residue
        _, resnumb, _ = res_id

        if chain_id in chain_sites and resnumb in chain_sites[chain_id]:
            resid = chain_sites[chain_id][resnumb][1]
            new_res = chain_sites[chain_id][resnumb][2]

            new_res.sec_struct = sec_struct
            new_res.sasa_r = sasa_r
            new_res.phi = phi
            new_res.psi = psi
    session.commit()


def calc_all_metrics(pid: int, idcode: str) -> None:
    has_dssp = (
        session.query(Residue_props.resid)
        .filter(Residue_props.resid == Residue.resid)
        .filter(Residue.pid == 1)
        .filter(Residue_props.sec_struct != None)
        .first()
    )

    if has_dssp:
        to_print = f"{idcode} already had dssp! Skipping..."
        print(to_print)
        return

    _, _, pdb_name = get_pdb(pid, idcode, prefix="tmp_solv_")

    chain_sites = get_sites(pid)
    for chain in chain_sites:
        for resnumb in chain_sites[chain]:
            _, resid = chain_sites[chain][resnumb]
            new_res = Residue_props(resid=resid)
            session.add(new_res)
            chain_sites[chain][resnumb].append(new_res)
    session.flush()

    # biopython parser
    parser = PDBParser()
    structure = parser.get_structure("test", pdb_name)
    model = structure[0]

    calc_hseCA(model, chain_sites)
    calc_hseCB(model, chain_sites)
    calc_hseCN(model, chain_sites)
    calc_msms(model, chain_sites)
    calc_dssp(model, chain_sites, pdb_name)

    os.system(f"rm -f {pdb_name}")


if __name__ == "__main__":

    # for idcode in idcodes_to_process("urgent_idcodes"):

    idcode = sys.argv[1]
    print("############", idcode, "############")

    pid = session.query(Protein.pid).filter_by(idcode=idcode).first()[0]

    calc_all_metrics(pid, idcode)
