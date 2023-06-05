from src.config.config import CONFIG
from src.service.neo4j import Neo4j

if __name__ == "__main__":
    neo4j: Neo4j = Neo4j(CONFIG.DB_HOST)
    neo4j.cleanDB()
    neo4j.close()
