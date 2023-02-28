# Configuration YAML File for Existing Design Parameter Variations

This configuration file will allow definition of the design parameters that are desired for variations of a design that is existing in the graphDB (either seed designs or created designs).  

There are four sections:
* Run Information

  This includes: targeted design name (must exist in graphDB), a descriptions (for information only), corpus type and number of samples.

  - `design_name` is a targeted design name currently available in the graphDB
  - `description` is informational only to provide additional information for future users
  - `corpus_type` is either "UAM" or "UAV"
  - `num_samples` will define the number of random values generated for the parameters that will be varied.  

* FDM Parameter Definition

  These values can be either a single value or a list.  The `Flight_Path` is expected to be a list defining the desired flight paths to run.  All flight paths would be [1, 3, 4, 5].  If any of the other parameters are lists, they must be the same size as the flight path definition.

  Information expected in fdm_params:
  
    - Analysis_Type - typically 3
    - Flight_Paths - current options are [1, 3, 4, 5, 6, 7, 8, 9]
    - Requested_Lateral_Speed
    - Requested_Vertical_Speed
    - Requested_Vertical_Down_Speed
    - Requested_Lateral_Acceleration
    - Requested_Lateral_Deceleration
    - Requested_Vertical_Acceleration
    - Requested_Vertical_Deceleration
    - Landing_Approach_Height
    - Vertical_Landing_Speed
    - Vertical_Landing_Speed_At_Ground
    - Q_Position - value from 0-1
    - Q_Velocity - value from 0-1
    - Q_Angular_Velocity - value from 0-1
    - Q_Angles - value from 0-1
    - Ctrl_R - value from 0-1

* Parameter Variation Definition

  This provides the list of study parameters available and the min/max selected for variation. When creating platform designs, a configuration file will be created with the min/max values being the same value.  Users can modify this in future uses to match their desired study parameters.

* Cargo Mass (For UAV designs only)

  Provides the study parameters when the cargo is present (0.5) and when it is empty (0.001) for UAV designs.
