# monaco-to-proknow
Convert Monaco DVH Criteria Template (XML) into ProKnow Scorecard Template (JSON)
This program is useful if you need to quickly create a scorecard that exactly matches your Monaco Dosimetric Criteria.

To export the criteria template from Monaco:
1. Go to the 'Statistics' tab under 'DVH Statistics'.
2. Click 'Save as Template' in the top left.
3. You can find your saved template in a folder called 'MonacoDvhCriteriaTemplates' wherever your Monaco data is stored.

The Monaco template is in XML format. This script will extract the relevant data and convert it into a JSON file that can be read by ProKnow.

To use this script you have 2 options:
1. RECOMMENDED: Click the 'JSONScorecard.exe' executable and just follow the steps through. The converted file will show up in the same directory as the .exe. 
2. Run the Python script, which will bring up the GUI. You may alter the script however you wish if you need different functionality.


NOTES:
-The script does not create extra tolerance values that were not present in Monaco.
-There are 11 types of criteria in Monaco, but far more goal types in Proknow. Only the corresponding 11 are used. 
-The maximum precision for volumes in ProKnow is 0.01cc. So 0.035cc will be rounded to 0.04cc.
-Feel free to alter the script or improve it however you wish!


Types available:
"Monaco" : "ProKnow"
"1": "MIN_DOSE_ROI",
"2": "MAX_DOSE_ROI",
"3": "MEAN_DOSE_ROI",
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
                
