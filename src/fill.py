#! /usr/bin/python3

import os
import argparse
import logging
import traceback
from sqlalchemy import func, exists, cast, String
from sqlalchemy.dialects.postgresql import insert
from typing import Tuple

from db import session, Protein, Pk_sim, PDB, Residue, Pk, Sim_settings
from utils import get_pdb, download_pdb, PK_MOD
import pypka
from pypka import __version__ as pypka_version

from fill_extra import run_all

parser = argparse.ArgumentParser()

parser.add_argument("--ncpus", default=8, type=int)
parser.add_argument("--idcode", type=str)
parser.add_argument("--nres-limit", default=500, type=int)
parser.add_argument("--no-post-processing", default=False, action="store_true")
parser.add_argument(
    "--verbose", default="INFO", type=str, choices=["DEBUG", "INFO", "WARNING"]
)

args = parser.parse_args()

VERBOSE_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
}

logging.basicConfig(
    format="%(levelname)s: %(message)s", level=VERBOSE_LEVELS[args.verbose]
)


def save_pdb(pid: int, fname: str) -> Tuple[float, PDB]:
    # Save the pdb file in the database
    content = ""
    nres = 0
    with open(fname) as f:
        previous_res = None
        for line in f:
            if line.startswith("ATOM "):
                resi = line[22:26]
                if resi != previous_res:
                    nres += 1
                previous_res = resi
                content += line
            if line.startswith("ENDMDL"):
                break

    new_pdb = PDB(pid=pid, pdb_file=content)
    session.add(new_pdb)

    CUR_PROTEIN.nres = nres
    session.commit()

    return nres, new_pdb


def run_pypka(fname: str, pdb_file_Hs: str) -> pypka.Titration:
    # Run pypka
    parameters = {
        "structure": fname,
        "epsin": 15,
        "ionicstr": 0.1,
        "pbc_dimensions": 0,
        "ncpus": args.ncpus,
        "pH": "-6,20",
        "convergence": 0.01,
        "save_pdb": pdb_file_Hs,
    }
    tit = pypka.Titration(parameters)

    return tit


def save_settings(tit: pypka.Titration) -> None:
    # Save settings
    pypka_params, delphi_params, mc_params = tit.getParametersDict()

    to_keep = [
        "CpHMD_mode",
        "ffID",
        "ff_family",
        "ffinput",
        "clean_pdb",
        "LIPIDS",
        "keep_ions",
        "ser_thr_titration",
        "cutoff",
        "slice",
    ]

    pypka_params = {key: value for key, value in pypka_params.items() if key in to_keep}
    pypka_params["version"] = pypka_version
    mc_params["pH_values"] = list(mc_params["pH_values"])

    bool_params = [
        "CpHMD_mode",
        "ser_thr_titration",
        "clean_pdb",
        "keep_ions",
        "pbx",
        "pby",
    ]

    query = session.query(Sim_settings.settid)
    for param in pypka_params:
        to_compare = str(pypka_params[param])
        if param in bool_params:
            to_compare = to_compare.lower()
        query = query.filter(Sim_settings.pypka_params[param].as_string() == to_compare)

    for param in delphi_params:
        to_compare = str(delphi_params[param])
        if param in bool_params:
            to_compare = to_compare.lower()
        query = query.filter(
            Sim_settings.delphi_params[param].as_string() == to_compare
        )

    for param in mc_params:
        to_compare = str(mc_params[param])
        if param in bool_params:
            to_compare = to_compare.lower()
        query = query.filter(Sim_settings.mc_params[param].as_string() == to_compare)

    settid = query.first()

    if not settid:
        new_sim_settings = Sim_settings(
            pypka_params=pypka_params, delphi_params=delphi_params, mc_params=mc_params
        )
        session.add(new_sim_settings)
        session.flush()

        settid = new_sim_settings.settid
    else:
        settid = settid[0]

    NEW_PK_SIM.settid = settid
    session.commit()


def save_pdbfile_hs(pdb_file_Hs) -> None:
    # Save Structure with Hydrogens
    with open(pdb_file_Hs) as f:
        content = f.read()
        safe_content = content
    CUR_PDB.pdb_file_hs = safe_content
    session.commit()


def save_titration_curve(tit):
    # Save total titration curve
    titration_curve = tit.getTitrationCurve()
    NEW_PK_SIM.tit_curve = titration_curve
    session.commit()


def save_isoelectric_point(tit):
    # Save total titration curve
    isoelectric_point = tit.getIsoelectricPoint()
    if type(isoelectric_point) == tuple:
        pH, limit, charge = isoelectric_point
        isoelectric_point = pH
        NEW_PK_SIM.isoelectric_point_limit = limit

    NEW_PK_SIM.isoelectric_point = isoelectric_point
    session.commit()


def save_residues(tit: pypka.Titration, pid: int) -> pypka.Titration:
    # Save residue-level details
    (
        all_sites,
        _,
        _,
        _,
    ) = tit.getSiteInteractions()

    for site in all_sites:

        residue_details = {
            "pid": pid,
            "residue_number": site.getResNumber(),
            "residue_type": site.res_name,
            "chain": site.molecule.chain,
        }

        res_insert = insert(Residue).values(residue_details)
        res_insert = res_insert.on_conflict_do_update(
            index_elements=["pid", "residue_number", "residue_type", "chain"],
            set_={"pid": pid},
        ).returning(Residue.resid)
        result = session.execute(res_insert)
        resid = result.fetchall()[0][0]

        site.resid = resid

    session.commit()
    return tit


def save_pks(pid: int, tit: pypka.Titration) -> None:
    # Save pK predictions
    for site in tit:
        resid = site.resid
        pK = site.pK
        dpK = None
        if pK:
            dpK = pK - PK_MOD[site.res_name]

        tit_curve = site.getTitrationCurve()
        tautomers = list(site.tautomers.keys())
        ref_tautomer = site.ref_tautomer.name
        tautomers.append(ref_tautomer)

        tautomers_probs = site.states_prob

        new_pk = Pk(
            pksimid=NEW_PK_SIM.pksimid,
            resid=resid,
            pk=pK,
            dpk=dpK,
            tautomers=tautomers,
            tautomer_probs=tautomers_probs,
            tit_curve=tit_curve,
        )
        session.add(new_pk)
    session.commit()


def choose_protein() -> Tuple[int, str, Pk_sim, Protein]:
    def register_sim(pid: int, force=False) -> Pk_sim:
        try:
            new_sim = Pk_sim(
                pid=pid, sim_date=func.current_date(), sim_time=func.current_time()
            )
            session.add(new_sim)
            session.commit()
        except:
            if force:
                session.rollback()

                del_pksimid = session.query(Pk_sim.pksimid).filter(Pk_sim.pid == pid)
                to_del = session.query(Pk).filter(Pk.pksimid == del_pksimid)
                to_del.delete(synchronize_session=False)

                to_del = session.query(Pk_sim).filter(Pk_sim.pid == pid)
                to_del.delete(synchronize_session=False)

                session.commit()

                new_sim = Pk_sim(
                    pid=pid, sim_date=func.current_date(), sim_time=func.current_time()
                )
                session.add(new_sim)
                session.commit()
            else:
                logging.error("The protein has already been calculated")
                exit()
        return new_sim

    if args.idcode:
        # Use input idcode
        idcode = args.idcode
        pid = session.query(Protein.pid).filter_by(idcode=idcode).first()[0]
        NEW_PK_SIM = register_sim(pid, force=True)

    else:
        # Get a protein that with no previous pka prediction
        next_sim = (
            (
                session.query(Protein.pid, Protein.idcode)
                .filter(Protein.protein_type == "prot")
                .filter(Protein.nres < args.nres_limit)
                .filter(~exists().where(Pk_sim.pid == Protein.pid))
            )
            .order_by(func.random())
            .first()
        )

        if next_sim:
            pid, idcode = next_sim
            NEW_PK_SIM = register_sim(pid)
        else:
            # Get a protein for which there is no nres record
            next_sim = (
                (
                    session.query(Protein.pid, Protein.idcode)
                    .filter(Protein.protein_type == "prot")
                    .filter(~exists().where(Pk_sim.pid == Protein.pid))
                )
                .order_by(func.random())
                .first()
            )

            if next_sim:
                pid, idcode = next_sim
                NEW_PK_SIM = register_sim(pid)

            else:
                logging.info("No more proteins to simulate!")
                exit()

    CUR_PROTEIN = session.query(Protein).filter_by(pid=pid).first()
    return pid, idcode, NEW_PK_SIM, CUR_PROTEIN


def try_to_run_pypka(pid: int, idcode: str, fpdb_name: str) -> bool:
    success_status = False
    try:
        pdb_file_Hs = idcode + "_Hs.pdb"
        tit = run_pypka(fpdb_name, pdb_file_Hs)
        logging.info(f"PypKa run of {idcode} succeeded!")

        save_pdbfile_hs(pdb_file_Hs)
        save_titration_curve(tit)
        save_isoelectric_point(tit)
        save_settings(tit)
        tit = save_residues(tit, pid)
        save_pks(pid, tit)
        logging.info(f"Saving {idcode} results succeeded!")

        success_status = True

    except Exception as e:
        tit = None
        logging.error(f"{idcode} failed!")
        with open("FAILED", "a") as f:
            error_message = f"{idcode}\n{e}\n"
            f.write(error_message)
            f.write(traceback.format_exc())
        NEW_PK_SIM.error_description = str(e)
        session.commit()
        raise

    os.system(f"rm -f {idcode}*.pdb")
    return success_status


def fetch_pdb(pid: int, idcode: str) -> Tuple[int, PDB, str]:
    pdb_exists = session.query(PDB).filter_by(pid=pid).first()
    if not pdb_exists:
        fpdb_name = download_pdb(idcode)
        if not fpdb_name:
            NEW_PK_SIM.error_description = "Failed to download PDB of {}".format(idcode)
            session.commit()
            raise
        nres, CUR_PDB = save_pdb(pid, fpdb_name)

    else:
        nres, CUR_PDB, fpdb_name = get_pdb(pid, idcode)

    return nres, CUR_PDB, fpdb_name


if __name__ == "__main__":

    pid, idcode, NEW_PK_SIM, CUR_PROTEIN = choose_protein()
    logging.info(f"Choose {idcode} with PID: {pid}")

    nres, CUR_PDB, fpdb_name = fetch_pdb(pid, idcode)

    if nres > args.nres_limit and not args.idcode:
        logging.info(
            f"Protein {idcode} has {nres}. nres-limit is set to {args.nres_limit}"
        )
        os.system(f"rm {idcode}.pdb*")
        exit()

    success_status = try_to_run_pypka(pid, idcode, fpdb_name)

    if success_status and not args.no_post_processing:
        run_all(pid, idcode)  # run_post_processing(pid, idcode, pdbDB)
        logging.info(f"Post-processing of {idcode} succeeded!")
