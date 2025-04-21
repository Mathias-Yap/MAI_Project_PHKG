from abc import ABC, abstractmethod
import time
from neo4j import GraphDatabase, Result
import docker
from PipelineStages import PipelineStep
import subprocess
import os

class QueryExecutorStep(PipelineStep):
    def __init__(self, engine_name = "avantgraph", query_format = "SPARQL", graph_path = None, verbose = False):
        """
        Initializes the QueryExecutorStep with a query engine.
        :param query_engine: The query engine to be used (default is "MilleniumDB").
        :param query_format: The format of the query (default is "SPARQL").
        """
        self.engine_name = engine_name
        self.verbose = verbose
        self.query_format = query_format
        self.query_engine = self.initialize_query_engine(engine_name, graph_path)
    def run(self, data, **kwargs):
        """
        Executes the query using the query engine.

        :param data: Input data required for query execution.
        :param kwargs: Additional arguments.
        :return: Query results.
        """
        return self.execute(data)
    def initialize(self, data, **kwargs):
        return super().initialize(data, **kwargs)
    def execute(self, data):
        """
        Executes the query using the query engine.

        :param data: Input data required for query execution.
        :return: Query results.
        """
        if not data or 'query' not in data:
            raise ValueError("Input data must contain a 'query' key.")
        
        query = data['query']
        return self.query_engine.run_query(query)
    
    def run_query(self, query):
        """
        Executes the query using the query engine.

        :param query: The query to be executed.
        :return: Query results.
        """
        match self.engine_name:
            case "MilleniumDB":
                pass
            case "avantgraph":
                pass
            case _:
                raise ValueError(f"Unsupported query engine: {self.engine_name}")
            

    def wait_for_server(self,driver_fn=GraphDatabase.driver, uri="bolt://localhost:7687", timeout=30, interval=1):
        """
        Waits for the Cypher server to be ready.
        :param driver_fn: The driver function (e.g., GraphDatabase.driver or milleniumdb.driver).
        :param uri: The URI to connect to.
        :param timeout: Max time to wait.
        :param interval: Retry interval in seconds.
        """
        start_time = time.time()
        while True:
            try:
                driver = driver_fn(uri)
                with driver.session() as session:
                    session.run("RETURN 1")
                return True
            except Exception:
                driver.close()
                if time.time() - start_time > timeout:
                    raise TimeoutError("Server did not start in time.")
                time.sleep(interval)
            finally:
                driver.close()
    def server_query(query):
        """
        Runs a query using the BOLT protocol.
        :param query: The query to be executed.
        :return: Query results.
        """
        # match self.engine_name:
        #     case "MilleniumDB":
        #         pass
        #     case "avantgraph":
        driver = GraphDatabase.driver("bolt://localhost:7687") 
        session = driver.session()
        return driver.execute_query(query, result_transformer_=Result.to_df)

    def initialize_query_engine(self, query_engine, graph_path=None, port = 7687):
        """
        Initializes the query engine based on the specified type.

        :param query_engine: The type of query engine to initialize.
        :return: An instance of the specified query engine.
        """
        match query_engine:
            case "MilleniumDB":
                pass
            case "avantgraph":
                if self.verbose:
                    print("AvantGraph started, loading graph...")
                # Start docker client
                client = docker.from_env()
                mount = docker.types.Mount(
                    target="/Code",
                    source=os.path.join(os.getcwd(), "data"),
                    type="bind"
                )
                avGraph = client.containers.run(
                    "ghcr.io/avantlab/avantgraph:release-2024-01-31",
                    detach=True,
                    mounts = mount,
                    name = "avantgraph",
                    ports={'7687/tcp': 7687},
                    privileged=True,
                    tty=True
                )
                _,output = avGraph.exec_run("ls -l /Code")
                # Load graph
                _,output = avGraph.exec_run("ag-load-graph --graph-format=ntriple " + "/Code/"+graph_path + " output_graph/")
                _,output = avGraph.exec_run("ls -lh output_graph")
                print(output)
                if self.verbose:
                    print(output.decode())
                    print("Graph loaded successfully.")
                    print("-- AvantGraph is running --")
                if self.query_format == "Cypher" or self.query_format == "Graphalg":
                    # These can be run through the server, so we need to start it
                    # Start the server
                    avGraph.exec_run("ag-server --listen 0.0.0.0:"+f"{port}"+" output_graph/", detach=True)
                    time.sleep(3)
                return avGraph
            case _:
                raise ValueError(f"Unsupported query engine: {query_engine}")

    def close(self):
        """
        Closes the query engine.
        """
        match self.engine_name:
            case "MilleniumDB":
                pass
            case "avantgraph":
                # Stop the AvantGraph container
                self.query_engine.remove(v = True, force = True)
                if self.verbose:
                    print("AvantGraph container stopped and removed.")
            case _:
                raise ValueError(f"Unsupported query engine: {self.query_engine}")

if __name__ == "__main__":
    print(QueryExecutorStep.server_query("MATCH (n) RETURN n"))
    
#     query_executor = QueryExecutorStep(engine_name="avantgraph", graph_path="rdf_100_sphn.nt",verbose=True, query_format="Cypher")
#     cypher_query = """
# MATCH (n) RETURN n 
# """
#     SPARQL_query = {
#         'query': """
#         SELECT *
#         WHERE { ?s ?p ?o . }
#         LIMIT 100
#         """
#     }
#     result = query_executor.server_query(cypher_query)
#     print(result.head())
#     print(result)
#     # Save the result to a CSV file
#     result.to_csv("query_results.csv", index=False)
#     if query_executor.verbose:
#         print("Results saved to query_results.csv")
    # result = query_executor.execute(data)
    # print(result)