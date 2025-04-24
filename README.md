# MAI_Project_PHKG

REQUIREMENTS: Docker

Make sure docker daemon is running: ```sudo systemctl start docker```
### Installing MilleniumDB into docker
* Download the following github repository. https://github.com/avantlab/avantgraph
* cd into the folder you installed it at
* run ```docker build -t mdb .```
* You're done!

### Installing AvantGraph
* docker pull ghcr.io/avantlab/avantgraph:release-2024-01-31
