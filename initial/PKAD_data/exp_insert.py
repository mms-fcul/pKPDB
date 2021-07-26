import pandas as pd
import sys

sys.path.insert(1, "../../src/")

from db import session, Exp_pk, Residue, Protein


def get_missing(row):
    resid = (
        session.query(Residue.resid)
        .join(Protein, Protein.pid == Residue.pid)
        .filter(Protein.idcode == row["PDB ID"].lower())
        .filter(Residue.chain == row["Chain"])
        .filter(Residue.residue_number == row["Res ID"])
        .filter(Residue.residue_type == row["Res Name"])
        .first()
    )
    if not resid:
        return row["PDB ID"]


def insert_exp(row):
    def try_float(i):
        try:
            i = float(i)
        except:
            i = None
        return i

    resname = row["Res Name"]
    if resname == "N-term":
        resname = "NTR"
    elif resname == "C-term":
        resname = "CTR"
    resid = (
        session.query(Residue.resid)
        .join(Protein, Protein.pid == Residue.pid)
        .filter(Protein.idcode == row["PDB ID"].lower())
        .filter(Residue.chain == row["Chain"])
        .filter(Residue.residue_number == row["Res ID"])
        .filter(Residue.residue_type == resname)
        .first()
    )
    if resid:

        pka = try_float(row["Expt. pKa"])
        uncertainty = try_float(row["Expt. Uncertainty"])
        temp = try_float(row["Expt. temp"])

        if pka:
            new = Exp_pk(
                resid=resid[0],
                pka=pka,
                uncertainty=uncertainty,
                exp_method=row["Expt. method"],
                temp=temp,
                reference=row["Reference"],
            )
            session.add(new)
            session.commit()


df = pd.read_csv("WT_pka.csv")

df.apply(lambda x: insert_exp(x), axis=1)

# df_missing = df.apply(lambda x: get_missing(x), axis=1)

# print('MISSING')
# print(df_new.dropna().value_counts())
