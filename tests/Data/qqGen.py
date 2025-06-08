
# def install_and_import(package):
#     import importlib
#     try:
#         importlib.import_module(package)
#     except ImportError:
#         import pip
#         pip.main(['install', package])
#     finally:
#         globals()[package] = importlib.import_module(package)


# install_and_import('rdflib')
# install_and_import('pyyaml')

from rdflib import Graph, URIRef
import os

data_folder = "Data"
g = Graph()

cwd = os.getcwd()
print(os.listdir())
# for filename in os.listdir(data_folder):
#     if filename.endswith(".ttl") or filename.endswith(".rdf") or filename.endswith(".txt"):
#         file_path = os.path.join(data_folder, filename)
#         #f = open(file_path)
#         if filename != 'rdf_200_sphn.txt':
#             g.parse(file_path, format="turtle")


#g.parse("Data/rdf_100_sphn.txt", format="turtle")
#g.parse("Data/rdf_300_sphn.txt", format="turtle")
#g.parse("Data/rdf_400_sphn.txt", format="turtle")
#print(f"Loaded {len(g)} triples.")