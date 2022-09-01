# Configuration YAML File for Existing Design Parameter Variations

This configuration file will allow definition of the design parameters that are desired for variations of a design that is existing in the graphDB (either seed designs or created designs).  

There are three sections:
* Run Information

  This includes the targeted design name (must exist in graphDB), a descriptions (for information only) and number of samples.

  - `num_samples` will define the number of random values generated for the parameters that will be varied.  

* FDM Parameter Definition

  These values can be either a single value or a list.  The `Flight_Path` is expected to be a list defining the desired flight paths to run.  All flight paths would be [1, 3, 4, 5].  If any of the other parameters are lists, they must be the same size as the flight path definition.

  Information expected in fdm_params:
  
    - Analysis_Type - typically 3
    - Flight_Paths - current options are [1, 3, 4, 5]
    - Requested_Lateral_Speed
    - Requested_Vertical_Speed
    - Q_Position - value from 0-1
    - Q_Velocity - value from 0-1
    - Q_Angular_Velocity - value from 0-1
    - Q_Angles - value from 0-1
    - Ctrl_R - value from 0-1

* Parameter Variation Definition

  The first item is an informational indicate of a component set that will be defined.  A component set is a set of component names that have the same value for the parameter defined.  This is used for preserving symmetry of the design.  So, if a section of a design is created to have the same parameter value (for example a cylinder length that is reused), it is defined in the same set so that the random value determine is applied to each of the named component instances (under `name`).

  Min/Max values should be provided.  For random design where this file is created in the process, this values may be set to the `corpus_data.json` defined min/max values.

  
When the CSV file is created, a single result run will represent all of the component sets changing in the run for the indicated number of samples over the indicated FDM parameters.  So, for the `NewAxe_test_study_params.yaml` provided as an testing example, the number of samples is 3 with 4 flight paths.  So, 12 rows will be setup for the CSV file where each of the rows includes a single flight path (and associated FDM parameters) and a random value for all the component sets.  For the this example, a CSV row will contain 9 values for the FDM parameters and 5 values for component parameter values. The resultant CSV file is shown below.  The data.zip from the workflow run in Jenkins will contain a results folder for each of the rows under the `archive` folder.  


```
Analysis_Type,Flight_Path,Requested_Lateral_Speed,Requested_Vertical_Speed,Q_Position,Q_Velocity,Q_Angular_Velocity,Q_Angles,Ctrl_R,Front_Rail_Length,Rear_Rail_Length,Mid_Tube_Length,Top_Leg_Tube_Length,Vertical_Tube_Length
3,1,19,1.1,1,1,1,1,0.1,95.77280911108201,95.77280911108201,152.7435664719062,152.7435664719062,152.7435664719062
3,3,21,1.1,1,1,1,1,0.1,95.77280911108201,95.77280911108201,152.7435664719062,152.7435664719062,152.7435664719062
3,4,11,1.1,1,1,1,1,0.1,95.77280911108201,95.77280911108201,152.7435664719062,152.7435664719062,152.7435664719062
3,5,10,1.1,1,1,1,1,0.1,95.77280911108201,95.77280911108201,152.7435664719062,152.7435664719062,152.7435664719062
3,1,19,1.1,1,1,1,1,0.1,117.33826122991299,117.33826122991299,101.58541973378937,101.58541973378937,101.58541973378937
3,3,21,1.1,1,1,1,1,0.1,117.33826122991299,117.33826122991299,101.58541973378937,101.58541973378937,101.58541973378937
3,4,11,1.1,1,1,1,1,0.1,117.33826122991299,117.33826122991299,101.58541973378937,101.58541973378937,101.58541973378937
3,5,10,1.1,1,1,1,1,0.1,117.33826122991299,117.33826122991299,101.58541973378937,101.58541973378937,101.58541973378937
3,1,19,1.1,1,1,1,1,0.1,211.5355992045786,211.5355992045786,108.19035391555227,108.19035391555227,108.19035391555227
3,3,21,1.1,1,1,1,1,0.1,211.5355992045786,211.5355992045786,108.19035391555227,108.19035391555227,108.19035391555227
3,4,11,1.1,1,1,1,1,0.1,211.5355992045786,211.5355992045786,108.19035391555227,108.19035391555227,108.19035391555227
3,5,10,1.1,1,1,1,1,0.1,211.5355992045786,211.5355992045786,108.19035391555227,108.19035391555227,108.19035391555227
```

> Note: Running this way seems to save about 25% of the run time (based on a single run set of the NewAxe design compared to using this config file).  In the Jenkins runs, the design is built up once in Creo and then each of the parameter updates are made in Creo between runs.  This time savings comes from the updating of the parameter information vs. rebuilding the model in Creo every time.  For larger runs, the time savings might be more significant.