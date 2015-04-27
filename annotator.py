#!/usr/bin/env python

"""
Script for writing MIRIAM style annotations from an SBML file to a tabular file
and to write annotations from such a list into SBML

Author: Jannis Uhlendorf
"""


import sys
import libsbml
import pandas


sbml_elements = [ 'Species', 'Reactions', 'Parameters', 'FunctionDefinitions', 'Compartments', 'Events' ]

qualifier_types =       { libsbml.MODEL_QUALIFIER: 'MODEL_QUALIFIER',
                          libsbml.BIOLOGICAL_QUALIFIER: 'BIOLOGICAL_QUALIFIER',
                          libsbml.UNKNOWN_QUALIFIER: 'UNKNOWN_QUALIFIER' }

model_qualifiers =      { libsbml.BQM_IS: 'BQM_IS',
                          libsbml.BQM_IS_DESCRIBED_BY: 'BQM_IS_DESCRIBED_BY',
                          libsbml.BQM_IS_DERIVED_FROM: 'BQM_IS_DERIVED_FROM',
                          libsbml.BQM_IS_INSTANCE_OF: 'BQM_IS_INSTANCE_OF',
                          libsbml.BQM_HAS_INSTANCE: 'BQM_HAS_INSTANCE' }

biological_qualifiers = { libsbml.BQB_IS: 'BQB_IS',
                          libsbml.BQB_HAS_PART: 'BQB_HAS_PART',
                          libsbml.BQB_IS_PART_OF: 'BQB_IS_PART_OF',
                          libsbml.BQB_IS_VERSION_OF: 'BQB_IS_VERSION_OF',
                          libsbml.BQB_HAS_VERSION: 'BQB_HAS_VERSION',
                          libsbml.BQB_IS_HOMOLOG_TO: 'BQB_IS_HOMOLOG_TO',
                          libsbml.BQB_IS_DESCRIBED_BY: 'BQB_IS_DESCRIBED_BY',
                          libsbml.BQB_IS_ENCODED_BY: 'BQB_IS_ENCODED_BY',
                          libsbml.BQB_ENCODES: 'BQB_ENCODES',
                          libsbml.BQB_OCCURS_IN: 'BQB_OCCURS_IN',
                          libsbml.BQB_HAS_PROPERTY: 'BQB_HAS_PROPERTY',
                          libsbml.BQB_IS_PROPERTY_OF: 'BQB_IS_PROPERTY_OF',
                          libsbml.BQB_HAS_TAXON: 'BQB_HAS_TAXON' }


def get_element_annotations( sbml_element ):
    """ get annotations for a single sbml element """
    annos = []
    if sbml_element.getNumCVTerms()>0:
        for cv in sbml_element.getCVTerms():
            for r in range(cv.getNumResources()):
                if cv.getQualifierType()==libsbml.MODEL_QUALIFIER:
                    qualifier = model_qualifiers[cv.getModelQualifierType()]
                elif cv.getQualifierType()==libsbml.BIOLOGICAL_QUALIFIER:
                    qualifier = biological_qualifiers[cv.getBiologicalQualifierType()]
                else:
                    raise Exception('Unknown annotation type')
                annos.append( { 'ID': sbml_element.getId(),
                                'qualifier_type': qualifier_types[cv.getQualifierType()],
                                'qualifier': qualifier,
                                'URI': cv.getResourceURI(r) } )
    return annos

def get_annotations_from_sbml( sbml_model ):
    """ get annotations for an SBML model """
    df = pandas.DataFrame( columns=['ID', 'qualifier_type', 'qualifier', 'URI'] )
    for le in sbml_elements:
        for elem in getattr(sbml_model, 'getListOf'+le)():
            #for d in get_element_annotations( elem ):
            #    df = df.append( line )
            annos = get_element_annotations( elem )
            if annos!=[]:
                df = df.append(annos)
    df.index = range(len(df))
    return df

def get_sbml_element_by_id( sbml_model, id ):
    """ get a single SBML element, speciefied by its ID """
    for le in sbml_elements:
        for elem in getattr(sbml_model, 'getListOf'+le)():
            if elem.getId()==id:
                return elem

def write_annotations_to_sbml( sbml_model, annotation_df ):
    for le in sbml_elements:
        for elem in getattr(sbml_model, 'getListOf'+le)():
            pass




if __name__ == '__main__':

    doc = libsbml.readSBML( sys.argv[1] )
    for i in range(doc.getNumErrors()):
        e = doc.getError(i)
        sys.stderr.write( e.getShortMessage() + '\n' )
    if doc.getNumErrors()>0:
        sys.exit(1)
    df = get_annotations_from_sbml( doc.getModel() )
    print df
