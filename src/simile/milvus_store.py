from .vecstore import Store
from pymilvus import (
    connections,
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection,
)
import numpy
from .tb_readers import *
# from itertools import islice


class MilvusVecstore(Store):

    fmt = "\n=== {:30} ===\n"    
    collection: Collection
    maxContentLength=5000 # varchar length for field content
    
    # vector dim is the size of the vectors that you expect to store
    def __init__(self, address = "localhost:19530", 
                 collectionName="default",
                 vector_dimension=384,
                 storeContent: bool = False):
        self.storeContent=storeContent
        p(f'MilvusVecstore, storeContent: {self.storeContent}')
        connections.connect("default",  address=address)
        self.createCollection(collectionName, vector_dimension)
        

    def createCollection(self, collectionName, vector_dimension):
        collectionExists = utility.has_collection(collectionName)
        p(f"Does collection [{collectionName}] exist in Milvus: {collectionExists}")
                
        if collectionExists:
            self.collection = Collection(collectionName)
        else:
            fields: list
            if (self.storeContent):
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=500),
                    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=self.maxContentLength),
                    FieldSchema(name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=vector_dimension)
                ]
            else:
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=500),
                    FieldSchema(name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=vector_dimension)
                ]

            schema = CollectionSchema(fields, "Embedding vectors representing text")

            p(f"created collection [{collectionName}]")
            self.collection = Collection(collectionName, schema, consistency_level="Strong")


    def createIndex(self):
        self.createIndex_DISKANN_OnEmbeddings()
        # self.createIndex_IVFFLAT_OnEmbeddings()

    # NB: this might eat up RAM
    def createIndex_IVFFLAT_OnEmbeddings(self):
        print(self.fmt.format("Start Creating index IVF_FLAT"))
        index = {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 128},
            }

        self.collection.create_index("embeddings", index)

    def createIndex_DISKANN_OnEmbeddings(self):
        print(self.fmt.format("Start Creating index DISKANN"))
        index_params = {
            "index_type": "DISKANN",
            "metric_type": "L2",
            "params": {}
        }

        self.collection.create_index("embeddings", index_params)

    def put(self, key: object, value: numpy.ndarray, content: str = None):
        toInsert: list
        if (self.storeContent):
            content = content[0 : self.maxContentLength]
            assert len(content) <= self.maxContentLength
            toInsert = [
                [key],
                [content],
                [value]
            ]
        else:
            toInsert = [
                [key],
                [value]
            ]
        insert_result = self.collection.insert(toInsert)

    def flush(self):
        self.collection.flush()

    def listIds(self):
        # self.collection.search
        pass

    def count(self):
        return self.collection.num_entities

    def listCollections(self):
        return utility.list_collections()

def p(args): print(args)
        
if __name__ == '__main__':
    pass    
