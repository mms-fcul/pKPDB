from sqlalchemy import create_engine, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy import Column, Integer, Date, CHAR, JSON, Time, Text, VARCHAR, REAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import psycopg2
from dotenv import dotenv_values
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
config = dotenv_values(f"{dir_path}/../.env")

user = config["user"]
password = config["password"]
ip = config["ip"]
port = config["port"]
database = config["database"]

db_path = f"postgresql://{user}:{password}@{ip}:{port}/{database}"

db = create_engine(db_path)
Base = declarative_base()

Session = sessionmaker(db)
session = Session()


class Protein(Base):
    __tablename__ = "protein"

    pid = Column(Integer, primary_key=True)
    idcode = Column(CHAR, unique=True)
    acc_date = Column(Date)
    protein_type = Column(Text)
    resolution = Column(REAL)
    experiment = Column(Text)
    exp_ph = Column(REAL)
    exp_temp = Column(REAL)
    nres = Column(Integer)


class SequenceAlign(Base):
    __tablename__ = "sequence_align"
    said = Column(Integer, primary_key=True)
    pid = Column(Integer, nullable=False)
    entity = Column(Integer, nullable=False)
    rcsb_id = Column(VARCHAR, nullable=False)
    uniprot_accession_codes = Column(VARCHAR, nullable=False)
    chains = Column(CHAR, nullable=False)
    seq_align_beg = Column(Integer, nullable=False)
    seq_align_end = Column(Integer)
    ForeignKeyConstraint(["pid"], ["protein.pid"])


class StructureValidation(Base):
    __tablename__ = "structure_validation"

    pid = Column(Integer, primary_key=True)
    rfree = Column(REAL)
    clashscore = Column(REAL)
    rama = Column(REAL)
    rota = Column(REAL)
    rsrz = Column(REAL)
    ForeignKeyConstraint(["pid"], ["protein.pid"])


class PDB(Base):
    __tablename__ = "pdb"

    pid = Column(Integer, primary_key=True)
    pdb_file = Column(JSON, nullable=False)
    pdb_file_hs = Column(JSON)
    ForeignKeyConstraint(["pid"], ["protein.pid"])


class Pk_sim(Base):
    __tablename__ = "pk_sim"

    pksimid = Column(Integer, primary_key=True)
    pid = Column(Integer, unique=True, nullable=False)
    tit_curve = Column(JSON)
    isoelectric_point = Column(REAL)
    isoelectric_point_limit = Column(CHAR)
    sim_date = Column(Date)
    sim_time = Column(Time)
    settid = Column(Integer)
    error_description = Column(Text)
    ForeignKeyConstraint(["pid", "settid"], ["protein.pid", "sim_settings.settid"])


class Residue(Base):
    __tablename__ = "residue"

    resid = Column(Integer, primary_key=True)
    pid = Column(Integer, nullable=False)
    residue_number = Column(Integer, nullable=False)
    residue_type = Column(VARCHAR, nullable=False)
    chain = Column(VARCHAR, nullable=False)
    ForeignKeyConstraint(["pid"], ["protein.pid"])
    UniqueConstraint("pid", "residue_number", "residue_type", "chain")


class Exp_pk(Base):
    __tablename__ = "exp_pk"

    expid = Column(Integer, primary_key=True)
    resid = Column(Integer, nullable=False)
    pka = Column(REAL, nullable=False)
    uncertainty = Column(REAL)
    exp_method = Column(Text)
    temp = Column(REAL)
    reference = Column(Text)
    ForeignKeyConstraint(["resid"], ["residue.resid"])


class Pk(Base):
    __tablename__ = "pk"

    pkid = Column(Integer, primary_key=True)
    resid = Column(Integer, nullable=False)
    pksimid = Column(Integer, nullable=False)
    pk = Column(REAL)
    dpk = Column(REAL)
    tautomers = Column(CHAR, nullable=False)
    tautomer_probs = Column(JSON, nullable=False)
    tit_curve = Column(JSON, nullable=False)
    ForeignKeyConstraint(["resid", "pksimid"], ["residue.resid", "pk_sim.pksimid"])
    UniqueConstraint("resid", "pksimid")


class Sim_settings(Base):
    __tablename__ = "sim_settings"

    settid = Column(Integer, primary_key=True)
    pypka_params = Column(JSON, nullable=False)
    delphi_params = Column(JSON, nullable=False)
    mc_params = Column(JSON, nullable=False)


class Contact_map(Base):
    __tablename__ = "contact_map"

    pid = Column(Integer, primary_key=True)
    distances = Column(REAL, nullable=False)
    anumbs = Column(Integer, nullable=False)
    anames = Column(CHAR, nullable=False)
    chains = Column(CHAR, nullable=False)
    resnumbs = Column(Integer, nullable=False)
    resnames = Column(CHAR, nullable=False)
    ForeignKeyConstraint(["pid"], ["protein.pid"])


class Residue_props(Base):
    __tablename__ = "residue_props"

    resid = Column(Integer, primary_key=True)
    hseca_u = Column(REAL)
    hseca_d = Column(REAL)
    hseca_angle = Column(REAL)
    hsecb_u = Column(REAL)
    hsecb_d = Column(REAL)
    hsecn = Column(REAL)
    residue_depth = Column(REAL)
    ca_depth = Column(REAL)
    sec_struct = Column(CHAR)
    sasa_r = Column(REAL)
    phi = Column(REAL)
    psi = Column(REAL)
    ForeignKeyConstraint(["resid"], ["residue.resid"])


class Fasta(Base):
    __tablename__ = "fasta"

    pid = Column(Integer, primary_key=True)
    fasta_file = Column(JSON, nullable=False)
    ForeignKeyConstraint(["pid"], ["protein.pid"])


class Similarity(Base):
    __tablename__ = "similarity"

    similid = Column(Integer, primary_key=True)
    pid = Column(Integer)
    cluster = Column(CHAR, nullable=False)
    seqid = Column(REAL, nullable=False)
    ForeignKeyConstraint(["pid"], ["protein.pid"])


class PKPDB:
    """For bulk operations"""

    def __init__(
        self,
        host="localhost",
        port=5432,
        user="pedror",
        password="pypkaserver",
        database="pkpdb",
    ):
        """Opens a new database connection if there is none yet for the
        current application context.
        """
        self.connection = None
        self.cursor = None

        self.pid = None
        self.pksim_id = None

        self.connection = psycopg2.connect(
            user=user, password=password, host=host, database=database, port=port
        )
        self.cursor = self.connection.cursor()

    def close_db(self):
        self.connection.close()

    def exec_statement(self, statement, commit=False, fetchall=False):
        self.cursor.execute(statement)
        if commit:
            self.connection.commit()
        if fetchall:
            return self.cursor.fetchall()
        return self.cursor

    def commit(self):
        self.connection.commit()

    def check_pdbcode_exists(self, pdbcode: str) -> bool:
        sql_query = f"""
    SELECT IDCODE
    FROM Protein
    WHERE IDCODE = '{string(pdbcode)}'
        """
        results = self.exec_statement(sql_query, fetchall=True)
        return len(results) > 0


def string(field):
    if field != "NULL":
        field = "{0}".format(field.replace("'", "''"))
    return field
