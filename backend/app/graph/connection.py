import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")


def get_driver():
    """
    Return a Neo4j driver when credentials are configured.
    Person 2: replace stub with real AuraDB connection.
    """
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        return None

    # TODO (Person 2): uncomment when AuraDB is ready
    # from neo4j import GraphDatabase
    # return GraphDatabase.driver(uri, auth=(user, password))

    return None
