import os
import sys
import logging

file_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, f"{file_dir}/../")
from db import session, Protein, SequenceAlign, StructureValidation
from utils import download_cif
from sqlalchemy import or_
import requests

logging.basicConfig(format="%(levelname)s: %(message)s", level="INFO")


def handle_cif_line(line, expectedtype):
    value = None
    parts = line.split()
    if len(parts) > 1:
        try:
            value = expectedtype(parts[1])
        except:
            pass
    return value


def save_experimental_conditions(idcode, pid):
    """
    _exptl_crystal_grow.pH              4.5      70%
    _exptl_crystal_grow.temp            277.15   73.0%

    _em_buffer.pH                           7.5

    _pdbx_nmr_exptl_sample_conditions.temperature         308
    _pdbx_nmr_exptl_sample_conditions.pH                  3.8
    """
    exists_experimental = (
        session.query(Protein.pid)
        .filter(Protein.pid == pid)
        .filter(or_(Protein.exp_ph != None, Protein.exp_temp != None))
        .first()
    )
    if exists_experimental:
        logging.info(f"{idcode} experimental conditions already exist.")
        return

    cif_file = download_cif(idcode, pid)

    temperature = None
    ph = None
    for line in cif_file.splitlines():
        if line.startswith("_exptl_crystal_grow.pH"):
            tmp_ph = handle_cif_line(line, float)
            if tmp_ph:
                ph = tmp_ph
        elif line.startswith("_exptl_crystal_grow.temp"):
            tmp_temp = handle_cif_line(line, float)
            if tmp_temp:
                temperature = tmp_temp
        elif line.startswith("_em_buffer.pH"):
            tmp_ph = handle_cif_line(line, float)
            if tmp_ph:
                ph = tmp_ph
        elif line.startswith("_pdbx_nmr_exptl_sample_conditions.temperature"):
            tmp_temp = handle_cif_line(line, float)
            if tmp_temp:
                temperature = tmp_temp
        elif line.startswith("_em_buffer.pH"):
            tmp_ph = handle_cif_line(line, float)
            if tmp_ph:
                ph = tmp_ph

    if ph or temperature:
        protein = session.query(Protein).filter_by(pid=pid).first()
        if ph:
            protein.exp_ph = ph
        if temperature:
            protein.exp_temp = temperature
        session.commit()


def save_sequence_info(idcode, pid):
    """
    https://data.rcsb.org/rest/v1/core/entry/2AT1
    "polymer_entity_ids":["1","2"]

    https://data.rcsb.org/rest/v1/core/polymer_entity/2AT1/1
    "asym_ids":["A","C"]

    https://data.rcsb.org/rest/v1/core/uniprot/2AT1/1
    "rcsb_id":"P0A786"
    "rcsb_uniprot_accession":["P0A786","P00479","Q2M662","Q47555","Q47557"]
    "feature_positions":[{"beg_seq_id":2,"end_seq_id":311}]}
    """
    exists_sequence = (
        session.query(SequenceAlign.pid).filter(SequenceAlign.pid == pid).first()
    )
    if exists_sequence:
        logging.info(f"{idcode} sequence alignment information already exist.")
        return

    r = requests.get(f"https://data.rcsb.org/rest/v1/core/entry/{idcode}")
    if not r.ok:
        return

    entities = r.json()["rcsb_entry_container_identifiers"]["polymer_entity_ids"]

    for entity in entities:
        r = requests.get(
            f"https://data.rcsb.org/rest/v1/core/polymer_entity/{idcode}/{entity}"
        )
        if not r.ok:
            continue
        content = r.json()
        chains = None
        if (
            "rcsb_polymer_entity_container_identifiers" in content
            and "auth_asym_ids" in content["rcsb_polymer_entity_container_identifiers"]
        ):
            chains = content["rcsb_polymer_entity_container_identifiers"][
                "auth_asym_ids"
            ]

        r = requests.get(
            f"https://data.rcsb.org/rest/v1/core/uniprot/{idcode}/{entity}"
        )
        if not r.ok:
            continue

        content = r.json()[0]

        rcsb_id = None
        uniprot_accession_codes = None
        seq_align_beg = None
        seq_align_end = None

        if "rcsb_id" in content:
            rcsb_id = content["rcsb_id"]
        if "rcsb_uniprot_accession" in content:
            uniprot_accession_codes = content["rcsb_uniprot_accession"]
        if (
            "rcsb_uniprot_feature" in content
            and "feature_positions" in content["rcsb_uniprot_feature"][0]
        ):
            align = content["rcsb_uniprot_feature"][0]["feature_positions"][0]
            if "beg_seq_id" in align:
                seq_align_beg = align["beg_seq_id"]
            if "end_seq_id" in align:
                seq_align_end = align["end_seq_id"]

        new_seqalign = SequenceAlign(
            pid=pid,
            entity=entity,
            rcsb_id=rcsb_id,
            uniprot_accession_codes=uniprot_accession_codes,
            chains=chains,
            seq_align_beg=seq_align_beg,
            seq_align_end=seq_align_end,
        )
        session.add(new_seqalign)
    session.commit()


def save_structure_quality(idcode, pid):
    """
    https://data.rcsb.org/rest/v1/core/entry/4LZT
    ls_rfactor_rfree
    clashscore
    percent_ramachandran_outliers
    percent_rotamer_outliers
    percent_rsrzoutliers
    """
    exists_validation = (
        session.query(StructureValidation.pid)
        .filter(StructureValidation.pid == pid)
        .all()
    )
    if exists_validation:
        logging.info(f"{idcode} structure validation already exist.")
        return

    r = requests.get(f"https://data.rcsb.org/rest/v1/core/entry/{idcode}")
    if not r.ok:
        logging.error(f"Unable to get structure validation info about {idcode}")
        return

    content = r.json()
    rfree = None
    clashscore = None
    percent_ramachandran_outliers = None
    percent_rotamer_outliers = None
    percent_rsrzoutliers = None

    if "refine" in content and "ls_rfactor_rfree" in content["refine"][0]:
        rfree = content["refine"][0]["ls_rfactor_rfree"]
    if "pdbx_vrpt_summary" in content:
        val_summ = content["pdbx_vrpt_summary"]

        if "clashscore" in val_summ:
            clashscore = val_summ["clashscore"]
        if "percent_ramachandran_outliers" in val_summ:
            percent_ramachandran_outliers = val_summ["percent_ramachandran_outliers"]
        if "percent_rotamer_outliers" in val_summ:
            percent_rotamer_outliers = val_summ["percent_rotamer_outliers"]
        if "percent_rsrzoutliers" in val_summ:
            percent_rsrzoutliers = val_summ["percent_rsrzoutliers"]

    new_val = StructureValidation(
        pid=pid,
        rfree=rfree,
        clashscore=clashscore,
        rama=percent_ramachandran_outliers,
        rota=percent_rotamer_outliers,
        rsrz=percent_rsrzoutliers,
    )
    session.add(new_val)
    session.commit()


if __name__ == "__main__":

    idcode = sys.argv[1].lower()
    print("############", idcode, "############")

    pid = session.query(Protein.pid).filter_by(idcode=idcode).first()[0]
    save_experimental_conditions(idcode, pid)
    save_sequence_info(idcode, pid)
    save_structure_quality(idcode, pid)