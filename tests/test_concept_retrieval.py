"""
Pytest for Concept Retrieval using Vector Store
"""
import yaml
import time
import pandas as pd

from src.logical_form_generation.vector_store import VectorStore

# Load Test Questions
file = "test_questions.yml"
with open(file, "r") as f:
    test_settings = yaml.safe_load(f)
    questions = test_settings["test_questions"]

# Load the vector store
vector_store = VectorStore()

# Test the vector store with each question
def test_concept_retrieval_vector_store_alone():
    results = []

    for question_id in questions.keys():
        expected_classes =  questions[question_id]['classes']
        expected_predicates = questions[question_id]['object_properties']

        tik = time.time()

        # Prediction Step
        found_classes, found_predicates  = vector_store.query(questions[question_id]["question"])

        # Calculate the results
        tok = time.time()
        results.append(
            {
                "question": question_id,
                "found_classes": found_classes,
                "found_predicates": found_predicates,
                "expected_classes": expected_classes,
                "expected_predicates": expected_predicates,
                "recall": len(set(found_classes + found_predicates).intersection(set(expected_classes + expected_predicates))) / len(expected_classes + expected_predicates),
                "precision": len(set(found_classes + found_predicates).intersection(set(expected_classes + expected_predicates))) / len(found_classes + found_predicates) if (found_classes + found_predicates) else 1,
                "time": tik - tok,
            }
        )

    # Save results as pandas dataframe
    df = pd.DataFrame(results)
    df.to_csv("results/test_concept_retrieval_vector_store_alone.csv")
        
# Test the vector store and connecting with each question
def test_concept_retrieval_with_connecting():
    results = []

    for question_id in questions.keys():
        expected_classes =  questions[question_id]['classes']
        expected_predicates = questions[question_id]['object_properties']

        tik = time.time()

        # Prediction Step
        found_classes, found_datatype_properties  = vector_store.query(questions[question_id]["question"])

        # Connecting classes and predicates
        found_classes = list(found_classes) + # ... TODO: Find connecting classes and their predicates
        found_predicates = list(found_datatype_properties) # ... TODO: +  (object_properties)

        # Calculate the results
        tok = time.time()
        results.append(
            {
                "question": question_id,
                "found_classes": found_classes,
                "found_predicates": found_predicates,
                "expected_classes": expected_classes,
                "expected_predicates": expected_predicates,
                "recall": len(set(found_classes + found_predicates).intersection(set(expected_classes + expected_predicates))) / len(expected_classes + expected_predicates),
                "precision": len(set(found_classes + found_predicates).intersection(set(expected_classes + expected_predicates))) / len(found_classes + found_predicates) if (found_classes + found_predicates) else 1,
                "time": tik - tok,
            }
        )
    
    # Save results as pandas dataframe
    df = pd.DataFrame(results)
    df.to_csv("results/test_concept_retrieval_with_connecting.csv")
