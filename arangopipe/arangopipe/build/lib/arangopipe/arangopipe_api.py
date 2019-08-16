#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 13 08:35:58 2019

@author: admin2
"""

from arango import ArangoClient
import logging
from arangopipe.arangopipe_config import ArangoPipeConfig


# create logger with 'spam_application'
logger = logging.getLogger('arangopipe_logger')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('arangopipe.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

class ArangoPipe:
    
    """ An instance of ArangoPipe is meant to be used to log a run of a pipeline execution. To use it:
        (1) Create a ArangoPipe object
        (2) Register your dataset with ArangoPipe
        (3) Register your featureset with ArangoPipe
        (4) Register you model with ArangoPipe
"""
    def __init__(self, config = None, persist = False):
        self.emlg = None
        if config is None:
            self.cfg = self.get_config()
        else:
            self.cfg = config.cfg
            if persist:
                config.dump_data()
        self.init_graph()

  


    def get_config(self):
        apc = ArangoPipeConfig()
        return apc.get_cfg()
        


    def lookup_dataset(self, dataset_name):
            
        """ Return a dataset identifier given a name. This can be used to get the dataset id that is used to log run information associated with execution of the pipeline."""
        client = ArangoClient(protocol='http',\
                              host=self.cfg['arangodb']['host'],\
                              port=self.cfg['arangodb']['port'])
        db = client.db(name=self.cfg['arangodb']['arangopipe_dbname'],\
                       username=self.cfg['arangodb']['arangopipe_admin_username'],\
                       password=self.cfg['arangodb']['arangopipe_admin_password'])
        # Execute the query
        cursor = db.aql.execute(
                'FOR doc IN datasets FILTER doc.name == @value RETURN doc',
                bind_vars={'value': dataset_name})
        dataset_keys = [doc for doc in cursor]
    
        return dataset_keys[0]
    


    def lookup_featureset(self, feature_set_name):
                
        """ Return a featureset identifier given a name. This can be used to get the featureset id that is used to log run information associated with execution of the pipeline."""
        client = ArangoClient(protocol='http',\
                              host=self.cfg['arangodb']['host'],\
                              port=self.cfg['arangodb']['port'])
        db = client.db(name=self.cfg['arangodb']['arangopipe_dbname'],\
                       username=self.cfg['arangodb']['arangopipe_admin_username'],\
                       password=self.cfg['arangodb']['arangopipe_admin_password'])
        # Execute the query
        cursor = db.aql.execute(
                'FOR doc IN featuresets FILTER doc.name == @value RETURN doc',
                bind_vars={'value': feature_set_name})
        feature_set_keys = [doc for doc in cursor]
    
        return feature_set_keys[0]


    def lookup_model(self, model_name):
            
        """ Return a model identifier given a name. This can be used to get the model id that is used to log run information associated with execution of the pipeline."""
        client = ArangoClient(protocol='http',\
                              host=self.cfg['arangodb']['host'],\
                              port=self.cfg['arangodb']['port'])
        db = client.db(name=self.cfg['arangodb']['arangopipe_dbname'],\
                       username=self.cfg['arangodb']['arangopipe_admin_username'],\
                       password=self.cfg['arangodb']['arangopipe_admin_password'])
        # Execute the query
        cursor = db.aql.execute(
                'FOR doc IN models FILTER doc.name == @value RETURN doc',
                bind_vars={'value': model_name})
        model_keys = [doc for doc in cursor]
    
        return model_keys[0]
    
    
    def lookup_modelparams(self, tag_value):
            
        """ Return a model parameter result given a tag."""
        client = ArangoClient(protocol='http',\
                              host=self.cfg['arangodb']['host'],\
                              port=self.cfg['arangodb']['port'])
        db = client.db(name=self.cfg['arangodb']['arangopipe_dbname'],\
                       username=self.cfg['arangodb']['arangopipe_admin_username'],\
                       password=self.cfg['arangodb']['arangopipe_admin_password'])
        # Execute the query
        cursor = db.aql.execute(
                'FOR r IN run\
                    FILTER r.tag == @value \
                        FOR mp IN 1..1 OUTBOUND r run_modelparams\
                            RETURN mp ', bind_vars={'value': tag_value})
        mp_keys = [doc for doc in cursor]
    
        return mp_keys[0]
    
    def lookup_modelperf(self, tag_value):
            
        """ Return a model dev performance given a tag."""
        client = ArangoClient(protocol='http',\
                              host=self.cfg['arangodb']['host'],\
                              port=self.cfg['arangodb']['port'])
        db = client.db(name=self.cfg['arangodb']['arangopipe_dbname'],\
                       username=self.cfg['arangodb']['arangopipe_admin_username'],\
                       password=self.cfg['arangodb']['arangopipe_admin_password'])
        # Execute the query
        cursor = db.aql.execute(
                'FOR r IN run\
                    FILTER r.tag == @value \
                        FOR dp IN 1..1 OUTBOUND r run_devperf\
                            RETURN dp ', bind_vars={'value': tag_value})
        dp_keys = [doc for doc in cursor]
    
        return dp_keys[0]



    def init_graph(self):
        """ Initialize a graph when an instance of ArangoPipe is provisioned. """
        client = ArangoClient(protocol='http',\
                              host=self.cfg['arangodb']['host'],\
                              port=self.cfg['arangodb']['port'])
    
        # Connect to "_system" database as root user.
        # This returns an API wrapper for "_system" database.
        sys_db = client.db('_system',\
                           username=self.cfg['arangodb']['root_user'],\
                           password=self.cfg['arangodb']['root_user_password'])
        
        if not sys_db.has_database(self.cfg['arangodb']['arangopipe_dbname']):
            logger.error("arangopipe database has not been created.")
            raise AttributeError("arangopipe database has not been created!")
        else:
            db = client.db(name=self.cfg['arangodb']['arangopipe_dbname'],\
                           username=self.cfg['arangodb']['arangopipe_admin_username'],\
                           password=self.cfg['arangodb']['arangopipe_admin_password'])
            if db.has_graph(self.cfg['mlgraph']['graphname']):
                self.emlg = db.graph(self.cfg['mlgraph']['graphname'])
            else:
                logger.error("ML tracking graph was not created. ")
                raise AttributeError("ML tracking graph has not been created")
        logger.info("Arango Pipe ML Graph initialized")
        return
    

    
    
    def register_model(self, mi, user_id = "authorized_user",\
                       project = "Wine-Quality-Regression-Modelling"):
        """ Register a model. The operation requires specifying a user id. If the user id is permitted to register a model, then the registration proceeds, otherwise an unauthorized operation is indicated. """
        models = self.emlg.vertex_collection("models")
        model_reg = models.insert(mi)
        
        client = ArangoClient(protocol='http',\
                              host=self.cfg['arangodb']['host'],\
                              port=self.cfg['arangodb']['port'])
        db = client.db(name=self.cfg['arangodb']['arangopipe_dbname'],\
                       username=self.cfg['arangodb']['arangopipe_admin_username'],\
                       password=self.cfg['arangodb']['arangopipe_admin_password'])
        # Execute the query
        cursor = db.aql.execute(
                'FOR doc IN project FILTER doc.name == @value RETURN doc',
                bind_vars={'value': project})
        project_keys = [doc for doc in cursor]
        the_project_info = project_keys[0]
        
        project_model_edge = self.emlg.edge_collection("project_models")
        project_model_key = the_project_info["_key"] + "-" + model_reg["_key"]
        
        a_project_model_edge = {"_key": project_model_key,\
                        "_from": "project/" + the_project_info["_key"],\
                        "_to": "models/" + model_reg["_key"]}
        pm_reg = project_model_edge.insert(a_project_model_edge)
        logger.info("Recording project model link " + str(pm_reg))
        
        
        return model_reg

    def register_dataset(self, ds_info, user_id = "authorized_user"):
        """ Register a dataset. The operation requires specifying a user id. If the user id is permitted to register a dataset, then the registration proceeds, otherwise an unauthorized operation is indicated. """
        ds = self.emlg.vertex_collection("datasets")
        ds_reg = ds.insert(ds_info)
        logger.info("Recording dataset dataset link " + str(ds_reg))

        return ds_reg

    
    def register_featureset(self, fs_info, dataset_id, \
                            user_id = "authorized_user"):
        """ Register a featureset. The operation requires specifying a user id. If the user id is permitted to register a featureset, then the registration proceeds, otherwise an unauthorized operation is indicated. """
        fs = self.emlg.vertex_collection("featuresets")
        fs_reg = fs.insert(fs_info)
        logger.info("Recording featureset " + str(fs_reg))
        featureset_dataset_edge = self.emlg.edge_collection("featureset_dataset")
        featureset_dataset_key = fs_reg["_key"] + "-" + dataset_id
        
        a_featureset_dataset_edge = {"_key": featureset_dataset_key,\
                        "_from": "featuresets/" + fs_reg["_key"],\
                        "_to": "datasets/" + dataset_id}
        fsds_reg = featureset_dataset_edge.insert(a_featureset_dataset_edge)
        logger.info("Recording featureset dataset link " + str(fsds_reg))

    
        return fs_reg

    
    def log_run(self, ri):
    
        """ Log a run. Logging a run requires specifying a dataset, featureset and a model against which this run is recored. A run records model parameters and model performance. The run object is probably most useful for the analysis of model performance with respect to a featureset, model hyper-parameters and a dataset.""" 

        rrid = ri["run_id"]
        mp = ri["model-params"]
        mp["_key"] = mp["run_id"]
        mperf = ri["model-perf"]
        mperf["_key"] = mperf["run_id"]
        model_key = ri["model"]
        
        run = self.emlg.vertex_collection("run")
        run_info = {"_key": rrid, 
                    "timestamp": mperf["timestamp"]}
        if "deployment_tag" in ri:
            run_info["deployment_tag"] = ri["deployment_tag"]
        if "tag" in ri:
            run_info["tag"] = ri["tag"]
        logger.info("Run info " + str(run_info))
        run_reg = run.insert(run_info)
        logger.info("Recording run " + str(run_reg))
    
        run_model_key = run_reg["_key"] + "-" + model_key
        a_run_model_edge = {"_key": run_model_key,\
                            "_from" :"models/" + model_key, \
                          "_to": "run/" + rrid}
        run_model_edge = self.emlg.edge_collection("run_models")
        rme_reg = run_model_edge.insert(a_run_model_edge)
        logger.info("Recording model run link " + str(rme_reg))

        
        model_param = self.emlg.vertex_collection("modelparams")
        mp_reg = model_param.insert(mp)
        logger.info("Recording model params " + str(mp_reg))
      
        run_fs_edge = self.emlg.edge_collection("run_featuresets")
        run_fs_key = rrid + "-" +  ri["featureset"]
        
        a_edge_run_fs = {"_key": run_fs_key,\
                        "_from": "run/" + rrid,\
                        "_to": "featuresets/" +  ri["featureset"]}
            
        rfse_reg = run_fs_edge.insert(a_edge_run_fs)
        logger.info("Recording run featureset link " + str(rfse_reg))
    
        run_mp_edge = self.emlg.edge_collection("run_modelparams")
        run_mp_key = rrid + "-" + mp["run_id"]
        
        a_run_mp_edge = {"_key": run_mp_key,\
                        "_from": "run/" + rrid,\
                        "_to": "modelparams/" + mp_reg["_key"]}
            
        rmp_reg = run_mp_edge.insert(a_run_mp_edge)
        logger.info("Recording run model params " + str(rmp_reg))
        
        model_perf = self.emlg.vertex_collection("devperf")
        dp_reg = model_perf.insert(mperf)
        logger.info("Recording model dev performance  " + str(dp_reg))
        
        run_devperf_edge = self.emlg.edge_collection("run_devperf")
        run_devperf_key = rrid + "-" + dp_reg["_key"]
        
        a_run_devperfedge = {"_key": run_devperf_key,\
                        "_from": "run/" + rrid,\
                        "_to": "devperf/" + dp_reg["_key"]}
        rdp_reg = run_devperf_edge.insert(a_run_devperfedge)
        logger.info("Recording run dev perf link " + str(rdp_reg))
            
        run_dataset_edge = self.emlg.edge_collection("run_datasets")
        run_dataset_key = rrid + "-" + ri["dataset"]
        
        a_run_dataset_edge = {"_key": run_dataset_key,\
                        "_from": "run/" + rrid,\
                        "_to": "datasets/" + ri["dataset"]}
        rds_reg = run_dataset_edge.insert(a_run_dataset_edge)
        logger.info("Recording run dev perf link " + str(rds_reg))
            

        return
    
    def log_serving_perf(self, sp, dep_tag, userid = "authorized user"):
    
        """ Log serving performance against a deployed model. The user making the request needs to be authorized to log this performance update. A serving performance vertex is created and is linked with its deployment vertex""" 
        servingperf = self.emlg.vertex_collection("servingperf")
        sp_reg = servingperf.insert(sp)
        # Locate the deployment record
        client = ArangoClient(protocol='http',\
                              host=self.cfg['arangodb']['host'],\
                              port=self.cfg['arangodb']['port'])
        db = client.db(name=self.cfg['arangodb']['arangopipe_dbname'],\
                       username=self.cfg['arangodb']['arangopipe_admin_username'],\
                       password=self.cfg['arangodb']['arangopipe_admin_password'])
        # Execute the query
        cursor = db.aql.execute(
                'FOR doc IN deployment FILTER doc.tag == @value RETURN doc',
                bind_vars={'value': dep_tag})
        dep_docs = [doc for doc in cursor]
        the_dep_doc = dep_docs[0]
        # Link the service performance record with the deployment record
        dep_servingperf_edge = self.emlg.edge_collection("deployment_servingperf")
        dep_servingperf_key = the_dep_doc["_key"] + "-" + sp_reg["_key"]
        the_dep_servingperf_edge = { "_key": dep_servingperf_key,\
                                "_from": the_dep_doc["_id"],\
                                "_to": sp_reg["_id"]}
        
        dep_servingperf_reg = dep_servingperf_edge.insert(the_dep_servingperf_edge)
        return dep_servingperf_reg
    

        
        
    
    
    
    
        

    
    
    