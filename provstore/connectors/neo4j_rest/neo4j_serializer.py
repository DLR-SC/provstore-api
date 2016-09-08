from neo4j import  *
from provstore.connectors.connector import *
from provstore.connectors.serializer import Serializer
class Neo4jRestSerializer(Serializer):
    def __init__(self, connection):
        Serializer.__init__(self)
        
        if connection is None:
            raise ProvSerializerException("Neo4j rest Serializer need a connection object ")
        self._connection = connection


    def create_node(self, node):
        # node is a MulitDiGrpah.Node / ProvRecord
        # see: http://networkx.readthedocs.io/en/networkx-1.10/reference/classes.multidigraph.html

        n = self._connection.nodes.create()

        if isinstance(node, ProvBundle):
            n.labels.add(BUNDLE_LABEL_NAME)
        elif isinstance(node, ProvElement):
            n.labels.add(str(node.get_type()))
            n.properties = dict(map(lambda (key, value): (str(key), str(value)), node.attributes))
        else:
            raise InvalidDataException("Not supportet node class you passed %s " % type(node))

        n.set(DOC_PROPERTY_NAME_LABEL, (str(node.identifier)))
        return n


    def create_relation(self, db_nodes, from_node, to_node, relation):
        # Attributes to string map
        attributes = map(lambda (key, value): (str(key), str(value)), relation.attributes)

        if relation.label == None:
            relationName = PROV_N_MAP[relation.get_type()]
        elif relation.identifier is not None:
            relationName = str(relation.identifier)  # @todo Test this part of the code
            attributes.append((DOC_PROPERTY_NAME_NAMESPACE_URI, relation.identifier.namescpae.uri))
            attributes.append((DOC_PROPERTY_NAME_NAMESPACE_PREFIX, relation.identifier.namescpae.prefix))
        else:
            raise InvalidDataException(
                "Relation is not valid. The type of the relation is not a default prov relation and has no identifier")

        db_from_node = db_nodes[from_node]
        db_to_node = db_nodes[to_node]

        return db_from_node.relationships.create(relationName, db_to_node, **dict(attributes))


    def create_bundle_relation(self, db_nodes, from_node, to_bundle):
        db_to_bundle = db_nodes[to_bundle.identifier]
        db_from_node = db_nodes[from_node]
        return db_from_node.relationships.create(BUNDLE_RELATION_NAME, db_to_bundle)

    def add_namespaces(self,db_node, prov_record):
        used_namespaces={}
        if isinstance(prov_record.identifier, QualifiedName):
            namespace = prov_record.identifier.namespace
            used_namespaces.update({str(namespace.prefix):namespace.uri})
        else:
           logger.info("Prov record %s has no identifier"%prov_record)

        for key,value in prov_record.attributes:
            if isinstance(key,QualifiedName):
                namespace = key.namespace
                used_namespaces.update({str(namespace.prefix): str(namespace.uri)})
            else:
               raise ProvSerializerException("Not support key type %s"%type(key))

        db_node.set(DOC_PROPERTY_NAME_NAMESPACE_URI,used_namespaces.values())
        db_node.set(DOC_PROPERTY_NAME_NAMESPACE_PREFIX,used_namespaces.keys())

    def add_id(self, db_node, doc_id):

        db_node.set(DOC_PROPERTY_NAME_ID, doc_id)