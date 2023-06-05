# Located at Gonesse
MATCH (n)-[LOCATED]-(b:aLocation)
RETURN n

// aPJ at Gonesse
MATCH (n:aPJ)-[LOCATED]-(b:aLocation)
RETURN n

// aPJ tués à Gonesse
MATCH (n:aPJ)-[LOCATED]-(b:aLocation {name: "Gonesse"}), (n:aPJ)-[aTuer]->(z)
RETURN n

// aPJ vivants à Gonesse
MATCH (n:aPJ)-[LOCATED]-(b:aLocation {name: "Gonesse"}), (n:aPJ)-[aTuer]->(z)
RETURN z

// aPJ qui sont un nain
MATCH (n: aRace {name: "nain"})<-[IS]-(b:aPJ) RETURN b