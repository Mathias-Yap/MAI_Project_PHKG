import docker

client = docker.from_env()
container = client.containers.run(
    "ghcr.io/avantlab/avantgraph:release-2024-01-31",
    detach=True,
    name="graph_engine")
try:
    container.exec_run("ag-load-graph --graph-format=json  output_graph/")
except:
    print("help") 
finally:
    container.stop()
    container.remove(force=True)