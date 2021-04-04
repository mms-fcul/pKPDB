CREATE TABLE protein(
    pid            SERIAL,
    IDCODE         CHAR(4),
    ACC_DATE       DATE,
    PROTEIN_TYPE   TEXT,
    RESOLUTION     REAL,
    EXPERIMENT     TEXT,
    EXP_PH         REAL,
    EXP_TEMP       REAL,
    nres           INT,
    PRIMARY KEY (pid),
    UNIQUE (idcode)
);

CREATE TABLE sequence_align (
    said SERIAL,
    pid INT NOT NULL,
    entity INT NOT NULL,
    rcsb_id VARCHAR(10) NOT NULL,
    chains       CHAR(1)[] NOT NULL,
    uniprot_accession_codes VARCHAR(10)[] NOT NULL,
    seq_align_beg  INT NOT NULL,
    seq_align_end  INT,
    FOREIGN KEY (pid) REFERENCES Protein (pid),
    PRIMARY KEY (said)   
); 

CREATE TABLE structure_validation (
    pid         INT,
    rfree       REAL,
    clashscore  REAL,
    rama        REAL,
    rota        REAL,
    rsrz        REAL,
    FOREIGN KEY (pid) REFERENCES Protein (pid),
    PRIMARY KEY (pid)
);


CREATE TABLE PDB(
    pid         INT,
    pdb_file    JSON NOT NULL,
    pdb_file_Hs JSON,
    FOREIGN KEY (pid) REFERENCES Protein (pid),
    PRIMARY KEY (pid)
);

/* include titratable Hs*/

CREATE TABLE contact_map(
    pid         INT,
    distances   REAL[][] NOT NULL,
    anumbs      INT[] NOT NULL,
    anames      VARCHAR(4)[] NOT NULL,
    chains       CHAR(1)[] NOT NULL,
    resnumbs    INT[] NOT NULL,
    resnames    VARCHAR(4)[] NOT NULL,
    FOREIGN KEY (pid) REFERENCES Protein (pid),
    PRIMARY KEY (pid)
);

CREATE TABLE FASTA(
    pid         INT,
    fasta_file  JSON NOT NULL,
    FOREIGN KEY (pid) REFERENCES Protein (pid),
    PRIMARY KEY (pid)
);

CREATE TABLE similarity(
    similid     SERIAL,
    pid         INT,
    cluster     CHAR(4)[] NOT NULL,
    seqid       REAL NOT NULL,    
    FOREIGN KEY (pid) REFERENCES Protein (pid),
    PRIMARY KEY (similid)    
);

CREATE TABLE residue(
    resid          SERIAL,
    pid            INTEGER NOT NULL,
    residue_number INTEGER NOT NULL,
    residue_type   VARCHAR(10) NOT NULL,
    chain          VARCHAR(5) NOT NULL,
    PRIMARY KEY (resid),
    FOREIGN KEY (pid) REFERENCES Protein (pid),
    UNIQUE (pid, residue_number, residue_type, chain)    
);

CREATE TABLE exp_pk(
    expid SERIAL,
    resid INT NOT NULL,
    pka REAL NOT NULL,
    uncertainty REAL,
    exp_method TEXT,
    temp REAL,
    reference TEXT,
    FOREIGN KEY (resid) REFERENCES Residue (resid),
    PRIMARY KEY (expid)
);

CREATE TABLE residue_props (
    resid INT,
    hseCA_u REAL,
    hseCA_d REAL,
    hseCA_angle REAL,
    hseCB_u REAL,
    hseCB_d REAL,
    hseCN REAL,
    residue_depth REAL,
    ca_depth REAL,
    sec_struct CHAR(1),
    sasa_r REAL,
    phi REAL,
    psi REAL,
    FOREIGN KEY (resid) REFERENCES Residue (resid),
    PRIMARY KEY (resid)
);

CREATE TABLE sim_settings (
    settid SERIAL,
    pypka_params   JSON NOT NULL,
    delphi_params  JSON NOT NULL,
    mc_params      JSON NOT NULL,
    PRIMARY KEY (settid)    
);

CREATE TABLE pK_sim (
    pksimid            SERIAL,
    pid                INTEGER NOT NULL,
    tit_curve          JSON,
    isoelectric_point  REAL,
    isoelectric_point_limit  CHAR(1),
    sim_date           DATE,
    sim_time           TIME,
    settid             INT,
    error_description  TEXT,
    PRIMARY KEY (pksimid),
    FOREIGN KEY (pid) REFERENCES Protein (pid),
    FOREIGN KEY (settid) REFERENCES sim_settings (settid),
    UNIQUE (pid)
);

CREATE TABLE pK (
    pkid           SERIAL,
    resid          INTEGER NOT NULL,
    pksimid        INTEGER NOT NULL,
    pK             REAL,
    dpK            REAL,
    tautomers      CHAR(3)[] NOT NULL,
    tautomer_probs JSON NOT NULL,
    tit_curve      JSON NOT NULL,
    PRIMARY KEY (pkid),
    FOREIGN KEY (resid) REFERENCES Residue (resid),
    FOREIGN KEY (pksimid) REFERENCES pK_sim (pksimid),
    UNIQUE (resid, pksimid)
);

CREATE INDEX pk_dpks_index ON pk (resid, pksimid, pk, dpk);
ALTER TABLE pk SET (
   autovacuum_analyze_scale_factor = 0,
   autovacuum_analyze_threshold = 500000
);