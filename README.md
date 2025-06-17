# MAI_Project_PHKG



## Query Engine

Make sure docker daemon is running: ```sudo systemctl start docker```
### Installing MilleniumDB into docker
* Download the following github repository. https://github.com/avantlab/avantgraph
* cd into the folder you installed it at
* run ```docker build -t mdb .```
* You're done!

## LLM setup
To use the SPARQL query generation section, you need an OpenAI key, provide this in the ```gpt_pipeline``` file. 

## Example usages:
- An example of how to use the query engine can be found in the ```run_queries``` notebook.
- An example of how to run the full pipeline can be found in the ```test_full_pipeline``` notebook, here the results for this project were generated.
- The results for the validation section were generated in the ```validation_tests``` notebook.
- Creation and processing of the test set was performed in the TODO: ADD ANNAMARIA'S NOTEBOOKS HERE ```alt_nl_questions``` (paraphrasing), ```templates_to_examples``` (filling templates to instances) notebooks.

