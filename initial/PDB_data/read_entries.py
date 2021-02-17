import sys

sys.path.insert(1, "../../src/")
from pkpdb import PKPDB

db = PKPDB()


def format_date(date):
    month, day, year = date.split("/")
    if int(year[0]) in (0, 1, 2, 3):
        year = "20" + year
    else:
        year = "19" + year
    date = f"{year}-{month}-{day}"
    return date


with open("entries.idx") as f:
    content = f.readlines()[2:]
    for line in content:
        cols = line.strip().split("\t")
        (
            idcode,
            header,
            acc_date,
            compound,
            source,
            authors,
            resolution,
            experiment,
        ) = cols
        idcode = idcode.lower()

        acc_date = format_date(acc_date)

        res_parts = resolution.split(", ")
        if res_parts != 1:
            resolution = res_parts[0]

        if resolution == "NOT":
            resolution = -1.0

        if db.check_pdbcode_exists(idcode):
            sql_query = f"""
UPDATE Protein
SET ACC_DATE = '{acc_date}',
    RESOLUTION = {resolution},
    EXPERIMENT= '{experiment}'
WHERE IDCODE = '{idcode}'"""
            db.exec_statement(sql_query)
        else:
            sql_query = f"""
INSERT INTO Protein(IDCODE, ACC_DATE, RESOLUTION, EXPERIMENT)
VALUES ('{idcode}', '{acc_date}', {resolution}, '{experiment}') """
            db.exec_statement(sql_query)

db.commit()