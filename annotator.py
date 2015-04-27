#!/usr/bin/env python

"""
Script for writing MIRIAM style annotations from an SBML file to a tabular file
and to write annotations from such a list into SBML

Author: Jannis Uhlendorf
"""


import sys, os
import libsbml
import pandas
import optparse


sbml_elements = [ 'Species', 'Reactions', 'Parameters', 'FunctionDefinitions', 'Compartments', 'Events' ]

sbml_2_qualifier_type =   { libsbml.MODEL_QUALIFIER: 'MODEL_QUALIFIER',
                            libsbml.BIOLOGICAL_QUALIFIER: 'BIOLOGICAL_QUALIFIER',
                            libsbml.UNKNOWN_QUALIFIER: 'UNKNOWN_QUALIFIER' }

sbml_2_model_qualifier =  { libsbml.BQM_IS: 'BQM_IS',
                            libsbml.BQM_IS_DESCRIBED_BY: 'BQM_IS_DESCRIBED_BY',
                            libsbml.BQM_IS_DERIVED_FROM: 'BQM_IS_DERIVED_FROM',
                            libsbml.BQM_IS_INSTANCE_OF: 'BQM_IS_INSTANCE_OF',
                            libsbml.BQM_HAS_INSTANCE: 'BQM_HAS_INSTANCE' }

sbml_2_biological_qualifier = { libsbml.BQB_IS: 'BQB_IS',
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

qualifier_type_2_sbml       = { sbml_2_qualifier_type[key]:key for key in sbml_2_qualifier_type }
model_qualifier_2_sbml      = { sbml_2_model_qualifier[key]:key for key in sbml_2_model_qualifier }
biological_qualifier_2_sbml = {sbml_2_biological_qualifier[key]: key for key in sbml_2_biological_qualifier}

def get_element_annotations( sbml_element ):
    """ get annotations for a single sbml element """
    annos = []
    if sbml_element.getNumCVTerms()>0:
        for cv in sbml_element.getCVTerms():
            for r in range(cv.getNumResources()):
                if cv.getQualifierType()==libsbml.MODEL_QUALIFIER:
                    qualifier = sbml_2_model_qualifier[cv.getModelQualifierType()]
                elif cv.getQualifierType()==libsbml.BIOLOGICAL_QUALIFIER:
                    qualifier = sbml_2_biological_qualifier[cv.getBiologicalQualifierType()]
                else:
                    raise Exception('Unknown annotation type')
                annos.append( { 'ID': sbml_element.getId(),
                                'qualifier_type': sbml_2_qualifier_type[cv.getQualifierType()],
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
            elem_annos = annotation_df[annotation_df['ID']==elem.getId()]
            # add model qualifiers
            cv = None
            for index,anno in elem_annos[elem_annos['qualifier_type']=='MODEL_QUALIFIER'].iterrows():
                #print anno
                if cv==None:
                    cv = libsbml.CVTerm()
                    cv.setQualifierType( qualifier_type_2_sbml[ 'MODEL_QUALIFIER' ] )
                cv.setModelQualifierType( model_qualifier_2_sbml[anno['qualifier']] )
            if cv!=None:
                print cv
                elem.addCVTerm(cv)
                cv = None
            # add biological qualifiers
            for index,anno in elem_annos[elem_annos['qualifier_type']=='BIOLOGICAL_QUALIFIER'].iterrows():
                #print anno
                if cv==None:
                    cv = libsbml.CVTerm()
                    cv.setQualifierType( qualifier_type_2_sbml[ 'BIOLOGICAL_QUALIFIER' ] )
                cv.setModelQualifierType( biological_qualifier_2_sbml[anno['qualifier']] )
            if cv!=None:
                print cv.toSBML()
                elem.addCVTerm(cv)
    print sbml_model.toSBML()
    return sbml_model

def remove_all_annotations( sbml_model ):
    for le in sbml_elements:
        for elem in getattr(sbml_model, 'getListOf'+le)():
            elem.setAnnotation('')
    return sbml_model



if __name__ == '__main__':

    parser = optparse.OptionParser(usage='usage: %prog [options] sbml_file')

    parser.add_option( '-g', '--get', dest='get', action='store_true', help='get annotations from SBML file'  )
    parser.add_option( '-w', '--write', dest='write', action='store_true', help='write annotations to SBML file' )
    parser.add_option( '-r', '--remove', dest='remove', action='store_true', help='remove annotations from SBML file' )
    parser.add_option( '-a', '--annotations', dest='annotations', help='filename of annotation TSV' )
    parser.add_option( '-o', '--outfile_sbml', dest='outfile_sbml', help='filename where SBML is written to' )

    (options,args) = parser.parse_args()
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit()

    doc = libsbml.readSBML( sys.argv[-1] )




    if options.get:
        df = get_annotations_from_sbml( doc.getModel() )
        if options.annotations!=None:
            anno_file = options.annotations
        else:
            root, ext = os.path.splitext( sys.argv[-1] )
            anno_file = root + '_annotations.tsv'
        df.to_csv( anno_file, sep='\t' )
        sys.stderr.write( 'Annotations from %s written to %s\n' %(sys.argv[-1],anno_file) )
        sys.exit()
    elif options.write:
        if options.annotations==None:
            sys.stderr.write('No annotation file given. Please specify one using the -a option\n')
            sys.exit()
        if not options.outfile_sbml:
            root, ext = os.path.splitext( sys.argv[-1] )
            sbml_out = root + '_annotated' + ext
        else:
            sbml_out = options.outfile_sbml
        df = pandas.read_csv( options.annotations, sep='\t' )
        sbml = write_annotations_to_sbml( doc.getModel(), df )
        #print sbml.toSBML()
        libsbml.writeSBMLToFile( doc, sbml_out )
        sys.stderr.write( 'SBML file with annotations written to %s.\n' %sbml_out)
        sys.exit()
    elif options.remove:
        if not options.outfile_sbml:
            root, ext = os.path.splitext( sys.argv[-1] )
            sbml_out = root + '_wo_annotations' + ext
        else:
            sbml_out = options.outfile_sbml
        remove_all_annotations( doc.getModel() )
        libsbml.writeSBMLToFile( doc, sbml_out )
        sys.stderr.write( 'SBML file without annotations written to %s.\n' %sbml_out)
        sys.exit()
