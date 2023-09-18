# athens-graphops

## Installation 
* Clone it with ```git clone git@github.com:symbench/athens-graphops.git --recurse-submodules```
* Install it with ```pip3 install -e .```

## Usage

### Create a Platform Variation

To create a platform variant design in the JanusGraph database, run:

```athens-graphops platform <design>```

Current design options: 
* new_axe, pick_axe
* falcon_m4,falcon_m4_rotated
* falcon_s4,falcon_s4_rotated,falcon_s8_rotated
* falcon_sm4,falcon_sm4_rotated
* falcon_t4,falcon_t4_with_tail,falcon_t8
* falcon_x4,falcon_x4_with_tail
* inline,uno_inline
* minimal_uam
* minimal_uav,minimal_uav_cargo
* tailsitter_joyride,tailsitter_narrow
* super_quad,test_quad
* tie4
* tiltie,tiltie_dyno,tiltie_tailed,tiltie_trimmed
* vari_vudoo,vudoo

After the design is created, a CSV file is created using the study parameter designs defined. This file is saved locally in the folder the user is currently using.

To run the `uam_direct2cad` workbench in the Jenkins system, add `-r` or `--run` to the command. This will upload the locally saved CSV study parameter file to the system indicated MinIO Bucket (see "System Configurations"), run the Jenkins tool and retrieve the results (data.zip and design description json file). The results will be placed in the `results/`folder in this repo.

> Note: When running the `uam_direct2cad` workbench, the user needs to first start Creo Parametric and the creoson server (by opening a command window and starting `C:\CreosonServerWithSetup-2.8.0-win64>creoson_run.bat`)

#### Platform Development Notes

To create new designs, place a python file under the platform folder.  The main building of the design will be done under a function name `<your base design>_platform`.  To create variants of the design, use functions with `create_<variant name>` naming convention.  The variants can toggle feature options identified in the platform function.

### Run Parameter Study on Existing Designs

As platform designs are created using the instructions in "Run a Platform Variation", a configuration file (.yaml) is created and saved into the `platform/configs` folder.  The configuration file saves off the design study parameters and sets the min/max values for structural parameters to be equal.  

The configuration file can be modified to create a parameter study of flight dynamic parameters and/or structural parameters.  The flight dynamic parameters can be either a single or list of values.  For UAV designs, `cargo_mass` is available to allow results from flight paths (i.e. 9) to run with and without cargo. For structural parameters, the `min` and `max` values are defined along with a `num_samples` to indicate how many design configurations to run.  The parameter for each of the designs will be a randomly selected value between the min and max values.  To indicate a fixed value, set min and max to the same value. 

To run a parameter study using the configuration file:

```athens-graphops platform random_design --configfile <config.yaml>```

### Workflow on Existing Design

The current Jenkins workflows (`uam_direct2cad` and `UAM_Workflows`) can be run on designs that exist in the current JanusGraph database.  Parameter of the runs should be specified as indicated below: 

* `uam_direct2cad`
  * graphGUID: `--design design` 
    * Indicates design name in JanusGraph 
  * minioBucket: setup by system configuration `--miniobucket NAME`, placed in front of the workflow keyword
    * Location of bucket which contains the <design_name>_study.csv and will be used for upload of data.zip results
  * paramFile: `--paramfile inputname`
    * List of parameters to run, <design_name>_study.csv
  * resultsFileName: `--resultname results`
    * Name of results file to be stored in MinioBucket
  
* `UAM_Workflows`
  * graphGUID: `--design design` 
    * Indicates design name in JanusGraph 
  * PETName: `--testname {/D_Testing/PET/FlightDyn_V2,/D_Testing/PET/FlightDyn_V2_AllPaths}`
    * Indicates name of the computational workflow to execute on the design, currently only 2 test options
  * NumSamples: `--samples samples`
    * Number of samples to execute for Monte Carlo DOE, uniformly sampled
  * DesignVars: `--parameters parameters` 
    * Provides design flight dynamic and structural parameter values (single or range), space delimited

### System Configurations

Default settings for Jenkins and MinIO setup parameters can be found in `athens_graphops/__init__.py`.  Change this to fit your platform needs or override the defaults with the following settings on the `athens-graphops` command line.

* `--host IP`
  * Host IP address of where Jenkins is running
* `--jenkinsuser user` 
  * username of the Jenkins installation
* `--jenkinspwd pwd` 
  * password of the Jenkins installation
* `--timeout SEC`
  * sets the Gremlin query timeout, a good value to use is 25000000; use this when querying JanusGraph database
* `--miniohost HOSTNAME`
  * MinIO hostname used to retrieve and put data in the Minio server 
* `--miniouser user`
  * username of the MinIO server
* `--miniopwd user`
  * password of the MinIO server
* `--miniobucket NAME`
  * name of MinIO bucket to retrieve and store data
* `--aws`
  * indicates the run is happening on an aws instance (needed due to differing location of the MinIO directory)

## Advanced Usage Options

### Corpus Updates and Validation

Definition of the available component types in the corpus database (derived from the graphml files that are loaded into the JanusGraph) is located in `data\corpus_schema.json`.  It outlines component names, corpus type (UAM or UAV), expected properties (fixed values), parameters (values that are expected to vary in the design definitions) and available connections.  The `data\corpus_data.json` contains all the available components in the corpus database (identified by "model" name) and their assigned default settings. The parameter values may include indications of minimum, maximum and assigned values for the parameters.

 When the corpus database is updated, the schema should be update manually to add any new component types.  To capture the latest component set, run the following command and save the file in the `data` folder:

 ```
 athens-graphops --timeout 25000000 query --corpus-data > corpus_data.json
 ```

The information in the `corpus_data.json` can be validate from two different perspectives:  (1) verifying that corpus data against the corpus schema (i.e. are all defined elements available for all components in the corpus data) and (2) looking for definitions in the corpus_data that are not available in the corpus schema (i.e. a new parameter or new component type ...).  Output from these commands can help to find missing information and complete definition as needed.  At the end, there is a list of component types and the number of components available for UAV or UAM or Both corpuses. Call these validations as follows:

```
(1) athens-graphops --timeout 25000000 validate --corpus-data corpus
(2) athens-graphops --timeout 25000000 validate --corpus-data schema
```

Various other design configurations were setup to validate the usability of different component types and exercise all the possible components of a class.  Here are some of them created:

* `--create-instances`
  * creates a simple UAM design and validate that a design instance is created and a component with specific parameters match the requested setup
* `--create-many-cylinders`
  * creates a UAM design with various cylinders of different diameter, thickness and length
* `--create-all-motors`
  * creates a UAM design with all motors attached
* `--validate-all-motors`
  * validate a UAM design has all motors attached
* `--create-all-propellers`    
  * creates a UAM design with all propellers attached
* `--validate-all-propellers`
  * validate a UAM design has all propellers attached
* `--design-loc`
  * sets the design folder for validation of all motors and all propeller designs created here

### Query

Query is used to pull information from the JanusGraph database.

`athens-graphops query` 

optional arguments:
  * `--design-names`
    * prints all design names (default: False)
  * `--design-data NAME`
    * prints the components of the given design (default: None)
  * `--corpus-data`
    * prints all component models (default: False)
  * `--corpus-model MOD`
    * prints a single component model (default: None)
  * `--property-table CLS`
    * prints the property table for a component class as json (default: None)
  * `--property-table-csv CLS`
    * prints the property table for a component class as csv (default: None)
  * `--raw QUERY`
    * executes the given raw query string (default: None)
  * `--script FILE`
    * executes the given groovy script query (default: None)
  * `--params [X ...]`
    * use this parameter list for scripts (default: [])
  * `--delete-design NAME`
    * deletes the given design (default: None)

An example to create a design data JSON from an existing (in Janusgraph DB) design:

`athens-graphops --timeout 25000000 query --design-data TestQuad > TestQuad-design-data.json`

### Dataset 

Another way to retrieve all the components of a class from the graph database and save to a file: 

```athens-graphops dataset --property-table <CLS> >> <filename>.json```
where CLS is `Battery`, `Motor` or `Propeller`

### Autoseed

Create a CSV file that lists the graph queries needed to add a design to the JanusGraph database.  

`athens-graphops autoseed --timeout 25000000 --name <design_name> <CSV filename>`

### Autograph

Using a CSV file with a list of graph queries to add a design into the JanusGraph database.

`athens-graphops --timeout 25000000 autograph <CSV filename>`

### Update

The `update` option will take the results data.zip file folder contents (with modified designParameter.json files and create a new version of the design in the Janusgraph with the updated parameter values.

```athens-graphops update [--name NAME] folder```

The design folder should be an absolute path. The design name can be the same as before or new.

Input jsons needed (found in top directory of data.zip file):
* info_paramMap4.json
* info_componentMapList1.json
* info_connectionMap6.json

Need to create:
* info_corpusComponents4.json

Steps taken:
1) Check if input json files are available
2) Update info_paramMap4.json from data.zip file - archive/result_1/designParam.json
3) Create the .csv file to create a design (using autoseed)
4) run autograph to create design in Janusgraph DB
5) re-create the `<design name>_design_data.json` file (prove change reflected in graph)

### json-designer

```athens-graphops json-designer -f JSON_FILE [-o] [-n NEW_NAME```

where `-o` is used to overwrite the existing design and `-n` allows indication of a new design name


