from abc import ABC, abstractmethod
import time
import millenniumdb_driver
from neo4j import GraphDatabase, Result
import docker
from PipelineStages import PipelineStep
import subprocess
import os


class QueryExecutorStep(PipelineStep):
    def __init__(self, engine_name="avantgraph", query_format="sparql", graph_path=None, verbose=False,
                 construct_graph=False):
        """
        Initializes the QueryExecutorStep with a query engine.
        :param query_engine: The query engine to be used (default is "MilleniumDB").
        :param query_format: The format of the query (default is "SPARQL").
        """
        self.engine_name = engine_name
        self.verbose = verbose
        self.query_format = query_format
        self.query_engine = self.initialize_query_engine(engine_name, graph_path, construct_graph,
                                                         "unix:///home/johannes/.docker/desktop/docker.sock")

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

    # def wait_for_server(self,driver_fn=GraphDatabase.driver, uri="bolt://localhost:7687", timeout=30, interval=1):
    #     """
    #     Waits for the Cypher server to be ready.
    #     :param driver_fn: The driver function (e.g., GraphDatabase.driver or milleniumdb.driver).
    #     :param uri: The URI to connect to.
    #     :param timeout: Max time to wait.
    #     :param interval: Retry interval in seconds.
    #     """
    #     # TODO: not functional atm, some issue. Sleeping for some time works as a replacement
    #     start_time = time.time()
    #     while True:
    #         try:
    #             driver = driver_fn(uri)
    #             driver.verify_connectivity()    
    #             return True
    #         except Exception:
    #             driver.close()
    #             if time.time() - start_time > timeout:
    #                 raise TimeoutError("Server did not start in time.")
    #             time.sleep(interval)
    #         finally:
    #             driver.close()
    # def server_query(self,query):
    #     """
    #     Runs a query using the BOLT protocol.
    #     :param query: The query to be executed.
    #     :return: Query results.
    #     """
    #     result = self.query_engine.run(query) 
    #     return result
    def query(self, query, path=True):
        """
        Executes a query using the query engine.

        :param query: The query to be executed.
        :return: Query results.
        """
        # TODO: normalize the query engine outputs
        match self.engine_name:
            case "milleniumDB":
                if path:
                    return self.mdb_server_query_path(query)
                else:
                    return self.mdb_server_query(query)
            case "avantgraph":
                if path:
                    return self.CLI_query_path(query)
                else:
                    return self.CLI_query_text(query, remove=True)
            case _:
                raise ValueError(f"Unsupported query engine: {self.engine_name}")

    def mdb_server_query(self, query):
        """ 
        Executes a query using the MillenniumDB server.
        :param query: The query to be executed.
        :return: Query results.
        """
        print(">>> Query being sent to MillenniumDB:\n", query)
        url = 'http://localhost:1234/'
        driver = millenniumdb_driver.driver(url)
        session = driver.session()
        result = session.run(query)
        return result

    def file_to_string(self, path):
        """
        Reads the content of a file and returns it as a string.

        :param path: The path to the file.
        :return: The content of the file as a string.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"The file at {path} does not exist.")
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()

    def mdb_server_query_path(self, query_path):
        """ 
        Executes a query using the MillenniumDB server, reading the query from a file.
        :param query: The query to be executed.
        :return: Query results.
        """
        #  check file extension = sparql
        if not query_path.endswith(".sparql"):
            raise ValueError("The query file must be a SPARQL file.")
        # check if the file exists
        if not os.path.exists(query_path):
            raise FileNotFoundError(f"The file at {query_path} does not exist.")
        # read the file
        query = self.file_to_string(query_path)
        return self.mdb_server_query(query)

    def initialize_query_engine(self, query_engine, graph_path=None, construct_graph=False, docker_context=""):
        """
        Initializes the query engine based on the specified type.

        :param query_engine: The type of query engine to initialize.
        :param graph_path: The path to the graph file (if applicable).
        :param construct_graph: Whether to construct the graph. If False, the graph must already exist for the respsective query engine.
        :return: An instance of the specified query engine.
        """
        if docker_context == "":
            client = docker.from_env()
        else:
            import os
            client = docker.DockerClient(
                base_url=os.getenv("DOCKER_HOST", docker_context))

        print("Checking available images...")
        for image in client.images.list():
            print(image.tags)

        self.graph_name = os.path.splitext(graph_path)[0]  # Remove the file extension
        match query_engine:
            case "milleniumDB":
                if construct_graph:
                    # if there is no graph path provided,  loa 
                    client.containers.run(
                        image="mdb",
                        command=f"mdb-import {graph_path} mdb_graph_load/{self.graph_name}",
                        volumes={
                            os.path.join(os.getcwd(), "data"): {
                                'bind': '/data',
                                'mode': 'rw'
                            }
                        },
                        remove=True,  # equivalent to --rm
                        detach=False  # run in foreground
                    )
                # start the millenniumdb server
                mdb = client.containers.run(
                    image="mdb",
                    command=f"mdb-server mdb_graph_load/{self.graph_name}",
                    volumes={
                        os.path.join(os.getcwd(), "data"): {
                            'bind': '/data',
                            'mode': 'rw'
                        }
                    },
                    ports={
                        '1234/tcp': 1234,
                        '4321/tcp': 4321
                    },
                    remove=True,  # equivalent to --rm
                    detach=True  # run in background
                )
                time.sleep(2)
                return mdb

            case "avantgraph":

                if self.verbose:
                    print("AvantGraph started, loading graph...")
                # Start docker client
                client = docker.from_env()

                avgraph = client.containers.run(
                    image="ghcr.io/avantlab/avantgraph:release-2024-01-31",
                    ports={f'{7687}/tcp': ('localhost', 7687)},
                    volumes={
                        os.getcwd(): {
                            'bind': '/code',
                            'mode': 'rw'
                        }
                    },
                    privileged=True,
                    remove=True,  # Equivalent to --rm
                    tty=True,  # Equivalent to -t
                    stdin_open=True,  # Equivalent to -i
                    detach=True  # Run in foreground, like CLI
                )

                # avgraph.exec_run()
                # """
                # ag-schema create-graph /code/data/new_graph_loads/graph1/
                # ag-schema create-vertex-table /code/data/new_graph_loads/graph1/ --vertex-label=DrugPrescription \ --vertex-property=id=CHAR_STRING\ 
                # --vertex-label=Drug \ --vertex-property=id=CHAR_STRING
                # ag-schema create-edge-table /code/data/new_graph_loads/graph1/ --edge-label=hasDrug \ --src-labels=DrugPrescription \ --trg-labels=Drug \ --edge-property=mybool=BOOLEAN
                # """
                # Load graph
                if construct_graph:
                    _, output = avgraph.exec_run(
                        "ag-load-graph --graph-format=ntriple " + "/code/data/" + graph_path + " /code/data/ag_graph_loads/" + self.graph_name + "/",
                        stream=True)
                    for line in output:
                        decoded_line = line.decode()
                        if self.verbose:
                            print(decoded_line)
                    if self.verbose:
                        print("Graph loaded successfully.")
                        print("-- AvantGraph is running --")
                return avgraph
            case _:
                raise ValueError(f"Unsupported query engine: {query_engine}")

    def CLI_query_text(self, query: str, remove: bool = False):
        """
        Executes a query using the command line interface (CLI) of the query engine.

        :param query: The query to be executed.
        :return: Query results.
        """
        if self.engine_name == "MilleniumDB":
            raise NotImplementedError("MilleniumDB CLI query execution is not implemented")

        # Run the query using the CLI
        file_extension = self.query_format.lower()
        query_file_path = f"temp/temp_query.{file_extension}"
        with open(query_file_path, "w") as query_file:
            query_file.write(query)
        results = self.CLI_query_path(query_file_path)
        if remove:
            os.remove(query_file_path)
        return results

    def CLI_query_path(self, query_path: str):
        """
        Executes a query using the command line interface (CLI) of the query engine.

        :param query: The query to be executed.
        :return: Query results.
        """
        if self.engine_name == "MilleniumDB":
            raise NotImplementedError("MilleniumDB CLI query execution is not implemented")
        _, output = self.query_engine.exec_run(
            "avantgraph   /code/data/ag_graph_loads/" + f"{self.graph_name}/" + " --query-type=" + f"{self.query_format.lower()} " + "/code/" + query_path)
        results = output.decode()
        return results

    def close(self):
        """
        Closes the query engine.
        """
        self.query_engine.remove(v=True, force=True)


if __name__ == "__main__":
    query_executor = QueryExecutorStep(engine_name="milleniumDB", graph_path="rdf_400_sphn.nt", verbose=True,
                                       query_format="sparql", construct_graph=True)
    result = query_executor.query("sparql_queries/query_002.sparql", path=True)
    print(result)
    query_executor.close()
    # """
    # ag-schema create-graph /code/data/new_graph_loads/graph1/
    # ag-schema create-vertex-table /code/data/new_graph_loads/graph1/ --vertex-label=DrugPrescription \ --vertex-property=id=CHAR_STRING\ 
    # --vertex-label=Drug \ --vertex-property=id=CHAR_STRING
    # ag-schema create-edge-table /code/data/new_graph_loads/graph1/ --edge-label=hasDrug \ --src-labels=DrugPrescription \ --trg-labels=Drug \ --edge-property=mybool=BOOLEAN
    # """
