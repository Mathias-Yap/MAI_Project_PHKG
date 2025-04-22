from abc import ABC, abstractmethod
import time
from neo4j import GraphDatabase, Result
import docker
from PipelineStages import PipelineStep
import subprocess
import os

class QueryExecutorStep(PipelineStep):
    def __init__(self, engine_name = "avantgraph", query_format = "sparql", graph_path = None, verbose = False):
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
        # TODO: not functional atm, some issue. Sleeping for some time works as a replacement
        start_time = time.time()
        while True:
            try:
                driver = driver_fn(uri)
                driver.verify_connectivity()    
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
        # TODO: get working for python
        # match self.engine_name:
        #     case "MilleniumDB":
        #         pass
        #     case "avantgraph":
        driver = GraphDatabase.driver("bolt://localhost:7687") 
        # print("starting")
        records, summary, keys = driver.execute_query("MATCH (n) RETURN n")
        print(keys) 
        return records

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

                avGraph = client.containers.run(
                    image="ghcr.io/avantlab/avantgraph:release-2024-01-31",
                    ports={'7687/tcp': ('127.0.0.1', 7687)},
                    volumes={
                        "/home/mathiasyap/Code/university/phkg/MAI_Project_PHKG": {
                            'bind': '/code',
                            'mode': 'rw'
                        }
                    },
                    privileged=True,
                    remove=True,  # Equivalent to --rm
                    tty=True,     # Equivalent to -t
                    stdin_open=True,  # Equivalent to -i
                    detach=True  # Run in foreground, like CLI
                )
                # Load graph
                _,output = avGraph.exec_run("ag-load-graph --graph-format=ntriple " + "/code/data/"+graph_path + " output_graph/")
                if self.verbose:
                    print(output.decode())
                    print("Graph loaded successfully.")
                    print("-- AvantGraph is running --")
                # if self.query_format == "Cypher" or self.query_format == "Graphalg":
                #     # These can be run through the server, so we need to start it
                #     # Start the server
                #     avGraph.exec_run("ag-server --listen 0.0.0.0:"+f"{port}"+" output_graph/", detach=True)
                #     # Wait for the server to be ready
                #     time.sleep(5)
                #     # self.wait_for_server(driver_fn=GraphDatabase.driver, uri="bolt://localhost:7687")
                return avGraph
            case _:
                raise ValueError(f"Unsupported query engine: {query_engine}")

    def CLI_query_text(self, query: str,remove: bool = False ):
        """
        Executes a query using the command line interface (CLI) of the query engine.

        :param query: The query to be executed.
        :return: Query results.
        """
                # Run the query using the CLI
        file_extension =  self.query_format.lower()
        query_file_path = f"temp/temp_query.{file_extension}"
        with open(query_file_path, "w") as query_file:
            query_file.write(query)
        _, output = self.query_engine.exec_run("avantgraph output_graph/ --query-type="+f"{self.query_format.lower()} " + "/code/"+query_file_path, stream=True)
        output_text = ""
        for line in output:
            decoded_line = line.decode()
            output_text += decoded_line
            if self.verbose:
                print(decoded_line)
        # Remove the temporary query file
        if remove:
            os.remove(query_file_path)
        return output
    
    
    def CLI_query_path(self, query_path: str):
        """
        Executes a query using the command line interface (CLI) of the query engine.

        :param query: The query to be executed.
        :return: Query results.
        """
        _, output = self.query_engine.exec_run("avantgraph output_graph/ --query-type="+f"{self.query_format.lower()} " + "/code/"+query_path, stream=True)
        output_text = ""
        for line in output:
            decoded_line = line.decode()
            output_text += decoded_line
            if self.verbose:
                print(decoded_line)
        return output_text
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
    query_executor = QueryExecutorStep(engine_name="avantgraph", graph_path="rdf_100_sphn.nt", verbose=True, query_format="Cypher")
    result = query_executor.CLI_query_text("MATCH (n) RETURN n")
    for record in result:
        print(record)
    query_executor.close()
    # for record in result:
    #     print(record)
    # Print the first 10 entries of the summary
    counter = 0
    # for record in result:
    #     print(record.values())
    #     counter += 1
        
        
        
    # for record in result:
    #     print(record)
    # query_executor.close()
    
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
#     if query_executor.verbose:
#         print("Results saved to query_results.csv")
    # result = query_executor.execute(data)
    # print(result)