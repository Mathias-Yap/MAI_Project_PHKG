class OntologyDesc:
    """This class describes the ontology for a healthcare system, it defines the classes, properties, and their relationships.
    """
    def __init__(self):
        self.classes = {
            'Patient', 'DrugPrescription', 'Drug', 'Substance', 
            'LabTestEvent', 'LabResult', 'MedicalProcedure', 
            'Diagnosis', 'Code', 'CodingSystem'
        }
        
        # Define object properties with their domains and ranges
        self.properties = {
            'hasDrug': {
                'domain': {'DrugPrescription'}, 
                'range': {'Drug'}
            },
            'hasActiveIngredient': {
                'domain': {'Drug'}, 
                'range': {'Substance'}
            },
            'hasLabTest': {
                'domain': {'LabTestEvent'}, 
                'range': {'LabResult'}
            },
            'hasCode': {
                'domain': {'LabResult', 'Diagnosis', 'MedicalProcedure', 'Drug'}, 
                'range': {'Code'}
            },
            'hasCodingSystemAndVersion': {
                'domain': {'Diagnosis', 'MedicalProcedure', 'Code'}, 
                'range': {'CodingSystem'}
            },
            'hasSubjectPseudIdentifier': {
                'domain': {'DrugPrescription', 'LabTestEvent', 'MedicalProcedure', 'Diagnosis'}, 
                'range': {'Patient'}
            }
        }
    