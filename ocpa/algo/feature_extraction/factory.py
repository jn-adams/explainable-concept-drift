import time

import ocpa.algo.feature_extraction.event_based_features.extraction_functions as event_features
import ocpa.algo.feature_extraction.execution_based_features.extraction_functions as execution_features
from ocpa.algo.feature_extraction.obj import Feature_Storage

EVENT_BASED = "event_based"
EXECUTION_BASED = "execution_based"

EVENT_NUM_OF_OBJECTS ="num_objects"
EVENT_SERVICE_TIME ="event_service"
EVENT_IDENTITY = "event_identity"

EXECUTION_NUM_OF_EVENTS ="num_events"
EXECUTION_NUM_OF_END_EVENTS = "num_end_events"
EXECUTION_THROUGHPUT = "exec_throughput"
EXECUTION_IDENTITY = "exec_identity"
EXECUTION_NUM_OBJECT= "exec_objects"
EXECUTION_UNIQUE_ACTIVITIES = "exec_uniq_activities"
EXECUTION_NUM_OF_STARTING_EVENTS = "exec_num_start_events"
EXECUTION_LAST_EVENT_TIME_BEFORE = "exec_last_event"
EXECUTION_FEATURE = "exec_feature"
EXECUTION_SERVICE_TIME = "exec_service_time"
EXECUTION_AVG_SERVICE_TIME = "exec_avg_service_time"


VERSIONS = {
    EVENT_BASED: {EVENT_NUM_OF_OBJECTS:event_features.number_of_objects,
                  EVENT_SERVICE_TIME:event_features.service_time,
                  EVENT_IDENTITY:event_features.event_identity},
    EXECUTION_BASED: {EXECUTION_NUM_OF_EVENTS:execution_features.number_of_events,
                      EXECUTION_NUM_OF_END_EVENTS:execution_features.number_of_ending_events,
                      EXECUTION_THROUGHPUT:execution_features.throughput_time,
                      EXECUTION_IDENTITY:execution_features.execution,
                      EXECUTION_NUM_OBJECT:execution_features.number_of_objects,
                      EXECUTION_UNIQUE_ACTIVITIES:execution_features.unique_activites,
                      EXECUTION_NUM_OF_STARTING_EVENTS:execution_features.number_of_starting_events,
                      EXECUTION_LAST_EVENT_TIME_BEFORE:execution_features.delta_last_event,
                      EXECUTION_FEATURE:execution_features.case_feature,
                      EXECUTION_SERVICE_TIME:execution_features.service_time,
                      EXECUTION_AVG_SERVICE_TIME:execution_features.avg_service_time
                      }
}




def apply(ocel, event_based_features =[], execution_based_features = [], event_attributes = [],event_object_attributes = [],execution_object_attributes = []):
    s_time = time.time()
    ocel.log["event_objects"] = ocel.log.apply(lambda x: [(ot, o) for ot in ocel.object_types for o in x[ot]], axis=1)
    ocel.create_efficiency_objects()
    feature_storage = Feature_Storage(event_features=event_based_features,execution_features=execution_based_features,ocel = ocel)
    object_f_time = time.time()-s_time
    id =0
    subgraph_time = 0
    execution_time = 0
    nodes_time = 0
    adding_time = 0
    for case in ocel.cases:
        s_time = time.time()
        case_graph = ocel.eog.subgraph(case)
        feature_graph = Feature_Storage.Feature_Graph(case_id=0, graph=case_graph, ocel=ocel)
        subgraph_time += time.time() - s_time
        s_time=time.time()
        for execution_feature in execution_based_features:
            execution_function, params = execution_feature
            feature_graph.add_attribute(execution_feature,VERSIONS[EXECUTION_BASED][execution_function](case_graph,ocel,params))
            for (object_type, attr, fun) in execution_object_attributes:
                #TODO add object frame
                feature_graph.add_attribute(object_type+"_"+attr+fun.__name__, fun([object_type[attr]]))
        execution_time += time.time() - s_time
        s_time = time.time()
        for node in feature_graph.nodes:
            for event_feature in event_based_features:
                event_function, params = event_feature
                node.add_attribute(event_feature,VERSIONS[EVENT_BASED][event_function](node,ocel, params))
            for attr in event_attributes:
                node.add_attribute(attr, ocel.get_value(node.event_id,attr))
                #node.add_attribute(attr,ocel.log.loc[node.event_id][attr])
            for (object_type, attr, fun) in event_object_attributes:
                #TODO add object frame
                feature_graph.add_attribute(object_type+"_"+attr+fun.__name__, fun([object_type[attr]]))
        nodes_time += time.time() - s_time
        s_time = time.time()
        feature_storage.add_feature_graph(feature_graph)
        adding_time += time.time() - s_time
        id+=1
    del ocel.log["event_objects"]
    #print("___")
    #print("Execution time "+str(execution_time))
    #print("Node Features " + str(nodes_time))
    #print("Adding Features " + str(adding_time))
    #print("Subgraph Features " + str(subgraph_time))
    #print("prep time " + str(object_f_time))
    return feature_storage