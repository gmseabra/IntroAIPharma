"""
Just some utilities used by various files
"""

# --Python
from typing import List, Dict
from pathlib import Path
import pandas as pd
import numpy as np

# Fingerprinting
from rdkit import Chem
from rdkit.Chem import PandasTools
from rdkit.Chem.rdmolops import RDKFingerprint
from rdkit.Chem.AllChem import GetMorganFingerprintAsBitVect

# Add Fingerprints
def get_morganfingerprints(mol):
    """
    Given a mol object, returns its Morgan Fingerprint (ECFP4)

    Args:
        mol (RDKit Mol): The molecule to be fingerprinted

    Returns:
        np.array: Fingerprint
    """
    
    fp = GetMorganFingerprintAsBitVect(mol,2)
    return np.array(list(map(int,fp.ToBitString())))

def get_fingerprint_from_smiles(smi):
    mol = Chem.MolFromSmiles(smi, sanitize=False)
    if mol is None:
        print("INVALID SMILES RECEIVED:", smi)
        fp = np.zeros(2048,dtype=int)
    else:
        fp = RDKFingerprint(mol)
        fp = np.array(list(map(int,fp.ToBitString())))
    return fp

def get_rdkfingerprint(mol):
    """
    Given a mol object, returns its RDKit Fingerprint

    Args:
        mol (RDKit Mol): The molecule to be fingerprinted

    Returns:
        np.array: Fingerprint
    """
    fp = RDKFingerprint(mol)
    return np.array(list(map(int,fp.ToBitString())))

def add_fingerprint(frame: pd.DataFrame, fp: str='rdkit') -> pd.DataFrame:
    """
    Given a Pandas DataFrame with a SMILES column and molecules in rows,
    returns the same DataFrame, now with the 'FINGERPRINT' column, containing
    the fingerprint for the molecule.

    Args:
        frame (pd.DataFrame): DataFrame containing a SMILES column
        fp (str, optional): ['rdkit'] The fingerprint type to use. Defaults to 'rdkit'.

    Returns:
        pd.DataFrame: The same DataFrame, now with the added 'FINGERPRINT' column.
    """

    fp = fp.lower()
    assert (fp in ['rdkit']), "Fingerprint type not available"

    if fp == 'rdkit':
        if 'ROMol' not in frame.columns:
            PandasTools.AddMoleculeColumnToFrame(frame,smilesCol="SMILES")

        print("Generating RDKit Fingerprints... ", end='')
        frame['FINGERPRINT'] = frame['ROMol'].apply(get_rdkfingerprint)
        print("Done")
    return frame

def print_dict(dict_to_print:dict):
    """Pretty-prints a dictionary containing properties for 
       molecules. The dictionary must have the property names 
       for keys, and lists of values for values:
           {prop1:[value1,vlue2,...],
            prop2:[value1,vlue2,...],
            ...}
    Args:
        dict_to_print (dict): dict_to_print
    """
    n_samples = 0
    print("Molecule  ", end="")
    for prop in dict_to_print.keys():
        print(f"{prop[:15]:>20s}", end="")
        n_samples = len(dict_to_print[prop])
    print("\n",end="")
    print(f"{'-'*10}{'-'*20*len(dict_to_print)}")
    for sample in range(n_samples):
        print(f"{sample+1:8d}  ",end="")
        for prop,val in dict_to_print.items():
            print(f"{val[sample]:>20f}", end="")
        print("\n", end="")
    return

# Progress Table
def print_progress_table(reward_properties:Dict, predictions:Dict, rewards:Dict):
    print("-"*55)
    print(f"|  {'CURRENT PROPERTY AVERAGES':^50} |")
    print("-"*55)
    print(f"|  {'PROPERTY':<25s} |  {'VALUE':>8s}  |  {'REWARD':>8s} |")
    print("-"*55)
    for prop in reward_properties.keys():
        line= (f"|  {prop:<25s} "
            f"|  {np.average(predictions[prop]):8.3f}  "
            f"|  {np.average(rewards[prop])    :8.3f} |")
        print(line)
    print("-"*55)
    return

# Reads a SMILES file
def read_smi_file(smiles_file):
    """Reads a SMILES file, and returns a list of RDKit ROMol molecules

    Args:
        smiles_file (str or Path): The path to the SMILES file

    Returns:
        [RDKit Mol]: A list of RDKit Mol objects
        [str]: A list of SMILES strings
    """
    mols, smis = [], []
    smiles_file = Path(smiles_file)
    if smiles_file.is_file():
        with open(smiles_file,'r') as smif:
            for row, line in enumerate(smif.readlines()):
                if line.startswith("#") or "Smiles" in line or "SMILES" in line:
                    continue
                if "," in line:
                    smi = line.split(",")[0]
                else:
                    smi = line.split()[0]
                
                mol = Chem.MolFromSmiles(smi)
                
                if mol is None:
                    print( f"WARNING: Invalid SMILES: <{smi}> in row {row}. Skipping.")
                else:
                    mols.append(mol)
                    smis.append(smi)
    else:
        msg = ( "ERROR when reading config file:\n"
               f"Could not find the smiles_file <{smiles_file.absolute()}>.")
        quit(msg)
        
    return mols, smis

# Save a SMILES file
def save_smi_file(filename, smiles, predictions):
    """ Saves the molecules and predictions in a .smi file
    """
    with open(filename,'w') as output:
       
        # ----- Print predictions -------------------------------------------------------
        line = f"SMILES,Name,{','.join([str(x) for x in predictions.keys()])}\n"
        output.write(line)
        i=1
        for smi, *pred in zip(smiles, *[predictions[x] for x in predictions]):
            line = f"{smi},Gen-{i:05d}," + ','.join([f"{x:.2f}" for x in pred]) +  "\n"
            output.write(line)
            i += 1

# Print results
def print_results(mols, results, header="", LENGTH_LIM=30, include_stats=True):
    """Prints a table with results

    Args:
        mols ([str]): Molecules in SMILES format
        results (Dict): The results to be printed
        include_stats (Bool): Whether to include stats. Defaults to True.
    """
    
    print(header)
    print(f"{'#':>6s}  {'Molecule':{LENGTH_LIM+3}s}", end="")
    for prop, cls in results.items():
        title_len = max(len(prop),6)
        print(f"  {prop:>{title_len}s}", end="")
    print("")
    
    for ind, smi in enumerate(mols):
        CONT = "..." if len(smi) > LENGTH_LIM else "   "
        print(f"{ind:>6d}  {smi:{LENGTH_LIM}.{LENGTH_LIM}s}{CONT}", end="")

        for prop, cls in results.items():
            title_len = max(len(prop),6)
            value = results[prop][ind]
            print(f"  {value:>{title_len}.2f}", end="")
        print("")

    if include_stats:
        print_stats(results)
    print("")

def print_stats(results, header="", LENGTH_LIM=30, print_header=False):
    """Prints statistics on the results

    Args:
        results (Dict): The results
        LENGTH_LIM (int, optional): A lenght for the SMILES field of results. Defaults to 30.
    """
    if print_header:
        print(f"{'#':>6s}  {header:{LENGTH_LIM+3}s}", end="")
        for prop, cls in results.items():
            title_len = max(len(prop),6)
            print(f"  {prop:>{title_len}s}", end="")
        print("")

    # Stats
    print(f"{'':>6s}  {'MAXIMUM:':{LENGTH_LIM}.{LENGTH_LIM}s}   ", end="")
    for prop, cls in results.items():
        title_len = max(len(prop),6)
        maximum = np.max(results[prop])
        print(f"  {maximum:>{title_len}.2f}", end="")
    print("")

    print(f"{'':>6s}  {'AVERAGES:':{LENGTH_LIM}.{LENGTH_LIM}s}   ", end="")
    for prop, cls in results.items():
        title_len = max(len(prop),6)
        average = np.average(results[prop])
        print(f"  {average:>{title_len}.2f}", end="")
    print("")
        
    print(f"{'':>6s}  {'MINIMUM:':{LENGTH_LIM}.{LENGTH_LIM}s}   ", end="")
    for prop, cls in results.items():
        title_len = max(len(prop),6)
        minimum = np.min(results[prop])
        print(f"  {minimum:>{title_len}.2f}", end="")
    print("")

    print(f"{'':>6s}  {'STD DEV:':{LENGTH_LIM}.{LENGTH_LIM}s}   ", end="")
    for prop, cls in results.items():
        title_len = max(len(prop),6)
        stdev = np.std(results[prop])
        print(f"  {stdev:>{title_len}.2f}", end="")
    print("")

