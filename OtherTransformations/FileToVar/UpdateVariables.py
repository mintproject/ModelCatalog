#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 31 12:14:19 2019

@author: Maria Stoica
@description: Script to update variables entries in 'VariablePresentation.csv'
"""

import pandas as pd

# file names:

rel_dir = '../'
rel_var_dir = rel_dir + 'Variables/'

PIHM_input = 'PIHM_input.csv'
PIHM_output = 'PIHM_output.csv'
FLDAS = 'FLDAS_Variables.csv'
ECON_input = 'ECON_input.csv'
ECON_output = 'ECON_output.csv'
#CYCLES_input = 'CYCLES_input.csv'
#CYCLES_output = 'CYCLES_output.csv'
variables_mc = 'VariablePresentation.csv'
variables_mc_backup = 'VariablePresentationBackup.csv'

# read data:
try:
    pihm = pd.read_csv( rel_var_dir + PIHM_input, usecols = [ 'Short Name', 'Long Name', 'GSN'] )
    pihm = pihm.append(pd.read_csv( rel_var_dir + PIHM_output, usecols = [ 'Short Name', 'Long Name', 'GSN'] )).fillna('')
except: 
    try:
        pihm = pd.read_csv( rel_var_dir + PIHM_input, usecols = [ 'Short Name', 'Long Name', 'GSN'], encoding = 'iso-8859-1' )
        pihm = pihm.append(pd.read_csv( rel_var_dir + PIHM_output, usecols = [ 'Short Name', 'Long Name', 'GSN'], encoding = 'iso-8859-1' )).fillna('')
    except:
        print('PIHM file unreadable.')
        
try:
    fldas = pd.read_csv( rel_var_dir + FLDAS, usecols = [ 'Short Name', 'Long Name', 'GSN'] ).fillna('')
except:
    try:
        fldas = pd.read_csv( rel_var_dir + FLDAS, usecols = [ 'Short Name', 'Long Name', 'GSN'], encoding = 'iso-8859-1' ).fillna('')
    except:
        print('FLDAS file unreadable.')   

try:
    econ = pd.read_csv( rel_var_dir + ECON_input, usecols = [ 'Short Name', 'Long Name', 'GSN'] )
    econ = econ.append(pd.read_csv( rel_var_dir + ECON_output, usecols = [ 'Short Name', 'Long Name', 'GSN'] )).fillna('')
except: 
    try:
        econ = pd.read_csv( rel_var_dir + ECON_input, usecols = [ 'Short Name', 'Long Name', 'GSN'], encoding = 'iso-8859-1' )
        econ = econ.append(pd.read_csv( rel_var_dir + ECON_output, usecols = [ 'Short Name', 'Long Name', 'GSN'], encoding = 'iso-8859-1' )).fillna('')
    except:
        print('ECON file unreadable.')


try:
    var_pres = pd.read_csv( rel_dir + variables_mc ).fillna('')
except:
    try:
        var_pres = pd.read_csv( rel_dir + variables_mc, encoding = 'iso-8859-1' )
    except:
        print('VariablePresentation.csv file unreadable.')
        var_pres = None

if not var_pres is None:
    var_pres.to_csv(rel_dir + variables_mc_backup, index=False)
    
label_col = 'https://w3id.org/mint/modelCatalog#hasStandardVariable'
model_col = 'https://w3id.org/mint/modelCatalog#VariablePresentation'
shortname_col = 'https://w3id.org/mint/modelCatalog#hasShortName'
longname_col = 'https://w3id.org/mint/modelCatalog#hasLongName'

for i in var_pres.index:
    model = var_pres.loc[i,model_col].split('_')[0]
    if model.lower() == 'pihm':
        sn = var_pres.loc[i,shortname_col]
        ln = var_pres.loc[i,longname_col]
        if (sn != '') or (ln != ''):
            try:
                pihm_var = []
                if (sn != ''):
                    pihm_var = pihm.loc[pihm['Short Name']==sn,'GSN']
                if len(pihm_var) == 0:
                    pihm_var = pihm.loc[pihm['Long Name']==ln,'GSN']
                pihm_var = pihm_var.iloc[0]
                label = var_pres.loc[i,label_col]
                if label != pihm_var:
                    print('Changing variable label for PIHM ',sn,' from ',label,' to ',pihm_var,'.')
                    var_pres.loc[i,label_col] = pihm_var
            except:
                print('Warning! PIHM short name ',sn,' not found!')
    if model.lower() == 'fldas':
        sn = var_pres.loc[i,shortname_col]
        if sn != '':
            try:
                fldas_var = fldas.loc[fldas['Short Name']==sn,'GSN'].iloc[0]
                label = var_pres.loc[i,label_col]
                if label != fldas_var:
                    print('Changing variable label for FLDAS ',sn,' from ',label,' to ',fldas_var,'.')
                    var_pres.loc[i,label_col] = fldas_var
            except:
                print('Warning! FLDAS short name ',sn,' not found!')
    if model.lower() == 'econ':
        sn = var_pres.loc[i,shortname_col]
        if sn!='':
            try:
                econ_var = econ.loc[econ['Short Name']==sn,'GSN'].iloc[0]
                label = var_pres.loc[i,label_col]
                if label != econ_var:
                    print('Changing variable label for ECON ',sn,' from ',label,' to ',econ_var,'.')
                    var_pres.loc[i,label_col] = econ_var
            except:
                print('Warning! ECON short name ',sn,' not found!')

var_pres.to_csv( rel_dir + variables_mc, index = False)        