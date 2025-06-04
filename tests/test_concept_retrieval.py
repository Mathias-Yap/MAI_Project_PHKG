"""
Pytest for Concept Retrieval using Vector Store

Run by: pytest -m tests/test_concept_retrieval.py
"""
import yaml
import time
import pandas as pd
import pytest
import os


from src.logical_form_generation.vector_store import VectorStore


# Create results directory if it does not exist
if not os.path.exists("tests/results"):
    os.makedirs("tests/results")

# Load Test Questions
file = "tests/test_questions.yml"
with open(file, "r") as f:
    test_settings = yaml.safe_load(f)
    questions = test_settings["test_questions"]

# Load the vector store
vector_store = VectorStore()

# Test the vector store with each question
# @pytest.mark.parametrize("question_id", questions.keys())
def test_concept_retrieval_vector_store_alone():
    results = []

    for question_id in questions.keys():
        expected_classes =  questions[question_id]['classes']
        expected_predicates = questions[question_id]['predicates']

        tik = time.time()

        # Prediction Step
        found_classes, found_predicates  = vector_store.query(questions[question_id]["question_en"], threshold=300)
        print(f"Found classes: {found_classes}")
        print(f"Found predicates: {found_predicates}")

        # Obtain the name instead of the URI
        tok = time.time()
        found_classes = [c.split("/")[-1] for c in found_classes]
        found_predicates = [p.split("/")[-1] for p in found_predicates]

        # Calculate the results
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
    df.to_csv("tests/results/test_concept_retrieval_vector_store_alone.csv")
        
# Test the vector store and connecting with each question
# @pytest.mark.parametrize("question_id", questions.keys())
def test_concept_retrieval_with_connecting():
    results = []

    for question_id in questions.keys():
        expected_classes =  questions[question_id]['classes']
        expected_predicates = questions[question_id]['predicates']

        tik = time.time()

        # Prediction Step
        found_classes, found_datatype_properties  = vector_store.query(questions[question_id]["question_en"])

        # Connecting classes and predicates
        found_classes = found_classes # + ... TODO: Find connecting classes and their predicates
        found_predicates = found_datatype_properties # ... + TODO:  (object_properties)

        # Obtain the name instead of the URI
        tok = time.time()
        found_classes = [c.split("/")[-1] for c in found_classes]
        found_predicates = [p.split("/")[-1] for p in found_predicates]

        # Calculate the results
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
    df.to_csv("tests/results/test_concept_retrieval_with_connecting.csv")

if __name__ == "__main__":
    test_concept_retrieval_vector_store_alone()
    print("Tests completed successfully.")