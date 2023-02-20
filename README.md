# athens-graphops

## Installation 
* Clone it with `git clone git@github.com:symbench/athens-graphops.git --recurse-submodules`
* Install it with `pip3 install -e .`

## Usage

> MM TODO: update with instructions, currently just notes 

### Run a Platform variation
`athens-graphops platform <design>`

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

To run the `uam_direct2cad` workbench in the Jenkins system, add `-r` or `--run` to the command. This will 
run the tool and retrieve the results (data.zip and design description json file). The results will be placed in the `results/`folder in this repo.

> Note: When running the `uam_direct2cad` workbench, the user needs to start Creo Parametric and the creoson server (by opening a command window and starting `C:\CreosonServerWithSetup-2.8.0-win64>creoson_run.bat`)

#### Platform Development Notes

To create new designs, place a python file under the platform folder.  The main building of the design will be done under a function name `<your base design>_platform`.  To create variants of the design, use functions with `create_<variant name>` naming convention.  The variants can toggle feature options identified in the platform function.

### Workflow
C:\symbench-repos\athens-graphops>athens-graphops workflow
usage: athens-graphops workflow [-h] [--jenkinsurl name] [--design design] [--testname {/D_Testing/PET/FlightDyn_V2,/D_Testing/PET/FlightDyn_V2_AllPaths}]
                                [--samples samples] [--parameters parameters] [--bucket minio] [--paramfile inputname] [--resultname results]
                                {UAM_Workflows,uam_direct2cad}
athens-graphops workflow: error: the following arguments are required: workflow


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



### Update
C:\symbench-repos\athens-graphops>athens-graphops update
usage: athens-graphops update [-h] [--name NAME] folder
athens-graphops update: error: the following arguments are required: folder
### Query
Connected to ws://localhost:8182/gremlin
Closed connection

Used individually????
## Dataset - internal only?
## Autoseed
usage: athens-graphops autoseed [-h] [--name NAME] file
## Autograph
usage: athens-graphops autograph [-h] file
## json-designer
usage: JSON Designer [-h] -f JSON_FILE [-o] [-n NEW_NAME]
JSON Designer: error: the following arguments are required: -f/--json-file
## architect
 vari-vudo --variable-design-name <design name> --num-designs 1  --workbench uam_direct2cad

  [--corpus {uam,uav}] [--variable-design-name VARIABLE_DESIGN_NAME] [--num-designs NUM_DESIGNS] [--num-samples NUM_SAMPLES]
                                 [--config-file CONFIG_FILE] [--workbench {UAM_Workflows,uam_direct2cad}] [--bucket minio]
                                 {random-existing}
## designer - internal only?

### Customization Options

#### Login to Jenkins

Default settings for these parameters can be found in `athens_graphops/__init__.py`.  Change this to fit your platform needs or override the defaults with the following settings on the `athens-graphops` command line.

* [--host IP] - Host IP address of where Jenkins is running
* [--jenkinsuser user] - username of the Jenkins installation
* [--jenkinspwd pwd] - password of the Jenkins installation
* [--timeout SEC] - sets the Gremlin query timeout, a good value to use is 25000000
* [--miniohost HOSTNAME] - MinIO hostname used to retrieve and put data in the Minio server 
* [--miniouser user] - username of the MinIO server
* [--miniopwd user] - password of the MinIO server
* [--miniobucket NAME] - name of MinIO bucket to retrieve and store data
* [--aws] - indicates the run is happening on an aws instance (needed due to differing location of the MinIO directory)







Examples to include in information above (if still relevant)
Randomize parameters defined in a configuration (yaml) file for existing designs
athens-graphops --host xxx.xxx.xxx.xxx --timeout 25000000 --jenkinsuser symbench --jenkinspwd symbench architect random-existing --config-file "NewAxe_test_study_params.yaml" --bucket "graphops"

	Ø Run direct2cad using vari-vudoo based design:

Athens-graphops --host xxx.xxx.xxx.xxx --timeout 25000000 architect vari-vudoo --variable-design-name TestD --num-designs 1 --workbench uam_direct2cad

Note: Vari-vudoo is a randomized version of the vudoo design from the first design challenge problem effort.  Can add `--bucket "<a folder in c:/NewDeploy/minioData>"` to indicate placement of config file.

	Ø Create design data JSON from an existing (in Janusgraph DB) design:

athens-graphops --host xxx.xxx.xxx.xxx --timeout 25000000 query --design-data TestQuad > TestQuad-design-data.json

	Ø Create design in gremlin DB from an autograph created csv file:
	
athens-graphops --host xxx.xxx.xxx.xxx --timeout 2500000 autograph ../designs/VUdoo1.csv
	
	Ø Update a design parameter set:

athens-graphops --host xxx.xxx.xxx.xxx --timeout 25000000 update "C:\symbench-repos\athens-graphops\athens_graphops\testing\TestA0_data" --name TestA0

