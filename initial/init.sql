CREATE TABLE protein(
    pid            SERIAL,
    IDCODE         CHAR(4),
    ACC_DATE       DATE,
    PROTEIN_TYPE   TEXT,
    RESOLUTION     FLOAT,
    EXPERIMENT     TEXT,
    nres           INT,
    PRIMARY KEY (pid),
    UNIQUE (idcode)
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
    distances   FLOAT[][] NOT NULL,
    anumbs      INT[] NOT NULL,
    anames      VARCHAR(4)[] NOT NULL,
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
    pid         INT,
    cluster     CHAR(4)[] NOT NULL,
    seqid       FLOAT NOT NULL,    
    FOREIGN KEY (pid) REFERENCES Protein (pid),
    PRIMARY KEY (pid)    
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

CREATE TABLE residue_props (
    resid INT,
    hseCA_u FLOAT,
    hseCA_d FLOAT,
    hseCA_angle FLOAT,
    hseCB_u FLOAT,
    hseCB_d FLOAT,
    hseCN FLOAT,
    residue_depth FLOAT,
    ca_depth FLOAT,
    sec_struct CHAR(1),
    sasa_r FLOAT,
    phi FLOAT,
    psi FLOAT,
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
    pksimid        SERIAL,
    pid            INTEGER NOT NULL,
    tit_curve      JSON,
    sim_date       DATE,
    sim_time       TIME,
    settid         INT,
    PRIMARY KEY (pksimid),
    FOREIGN KEY (pid) REFERENCES Protein (pid),
    FOREIGN KEY (settid) REFERENCES sim_settings (settid),
    UNIQUE (pid)
);

CREATE TABLE pK (
    pkid           SERIAL,
    resid          INTEGER NOT NULL,
    pksimid        INTEGER NOT NULL,
    pK             FLOAT,
    dpK            FLOAT,
    pK_exp         FLOAT,
    pK_propka      FLOAT,
    tautomers      CHAR(3)[] NOT NULL,
    tautomer_probs JSON NOT NULL,
    tit_curve      JSON NOT NULL,
    PRIMARY KEY (pkid),
    FOREIGN KEY (resid) REFERENCES Residue (resid),
    FOREIGN KEY (pksimid) REFERENCES pK_sim (pksimid),
    UNIQUE (resid, pksimid)
);