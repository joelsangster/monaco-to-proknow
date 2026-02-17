# monaco-to-proknow-scorecard
Convert Monaco DVH criteria (isodosesettings.xml) into a ProKnow Scorecard Template (JSON)  
This program is useful if you need to quickly create a scorecard that exactly matches your Monaco Dosimetric Criteria.  

The isodosesettings.xml file is stored on the Monaco file system under the patient plan:  
e.g. \path-to-your-clinic\PATIENT_ID\plan\PLAN_NAME\isodosesettings.xml  

This script will extract the relevant data and convert it into a JSON file that can be read by ProKnow.   

<img width="676" height="685" alt="image" src="https://github.com/user-attachments/assets/174c16a3-3740-4ab3-a70b-da4555f9ab5c" />  

To run this script:  
1. Edit the config.ini file with the path to your Monaco installation folder.  
2. Run the Python script which will bring up the GUI.   
3. If the installation folder in the config file is correct, the available clinic names will appear in the drop down.  
4. Select the patient and plan, and generate the json file.  
5. In ProKnow, create a scorecard on the patient with no template. Upload the json file into it.  
    

NOTES:  
- Compatible with Monaco versions 5 and 6.  
- WIP for Eclipse compatibility.  
- The maximum precision for volumes in ProKnow is 0.01cc. So 0.035cc will be rounded to 0.04cc.  
- Proknow uses a different algorithm to calculate dose/volumes, the computed metrics may be slighlty different despite the objectives being exactly the same. I've never seen this take a result from pass to fail, but it's possible.  


Types available:  
"Monaco" : "ProKnow"  
"1": "MIN_DOSE_ROI",  
"2": "MAX_DOSE_ROI",  
"3": "MEAN_DOSE_ROI", #min   
"4": "MEAN_DOSE_ROI", # max  
"5": "DOSE_VOLUME_PERCENT_ROI",  
"6": "DOSE_VOLUME_CC_ROI",  
"7": "DOSE_VOLUME_PERCENT_ROI",  
"8": "DOSE_VOLUME_CC_ROI",  
"9": "VOLUME_PERCENT_DOSE_ROI",  
"10": "VOLUME_CC_DOSE_ROI",  
"11": "VOLUME_PERCENT_DOSE_ROI",  
"12": "VOLUME_CC_DOSE_ROI",  
"13": "INHOMOGENEITY_INDEX",  
"14": "CONFORMALITY_INDEX"  
                
