class Metrics:
    def __init__(self): self.data_collected=0.0; self.collection_count=0; self.value_collected=0.0
    def record_collection(self,resource):
        self.data_collected += resource.data_size; self.value_collected += resource.value; self.collection_count += 1
