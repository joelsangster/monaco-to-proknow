from json import dump
from os import scandir, path
from xml.etree.ElementTree import parse
from tkinter import Tk, END, WORD, ttk, messagebox, scrolledtext, StringVar, filedialog
from configparser import ConfigParser

"""
Author: Joel Sangster
Email: joel.sangster@stgeorges.org.nz
Date: 26/02/2025

This script takes an isodosesettings.xml file from your Monaco (v5 or v6) file system, 
and converts it into a Proknow scorecard in .json format.
The scorecard can be uploaded directly to Proknow.

Please edit the config.ini file with the path to you Monaco installation folder. 
This folder should contain folders with the Clinic names.

"""


# create path to look for files
config=ConfigParser()
config.read("config.ini")
installation = config.get("General", "installation_directory")

# get list of clinics from installation directory
clinics = [f.name for f in scandir(installation) if f.is_dir()]


manual_file_path = ""

def get_plans():
    while nhi_box != "":
        nhi = nhi_box.get()  # user enters NHI
        # search clinic dir for patients
        patients = [f.path for f in scandir(f'{installation}\\{clinic_combobox.get()}') if f.is_dir()]
        patient_dir = None
        # set the patient_dir to the directory of the selected patient
        for p in patients:
            if nhi in p:
                patient_dir = p
            # else: patient not found
        # set the plans dir
        plans_dir = fr'{patient_dir}\plan'
        # get a list of the plan names to populate the combobox
        plans = [f.name for f in scandir(plans_dir)]
        return plans, plans_dir

def populate_plans(*args):
    # populate plan combobox
    plan_combobox['values'],plans_dir = get_plans()

def load_file_dialog():
    global manual_file_path
    manual_file_path = filedialog.askopenfilename(
         title="Select an XML file",
         filetypes=[("XML files", "*.xml")])
    # get just the file name
    #dir, file = path.split(manual_file_path)
    # place the xml file name in the text box
    XML_box.insert(index=0, string=manual_file_path)

# create lookup table to cross-reference goal types
type_lookup = { "1": "MIN_DOSE_ROI",
                "2": "MAX_DOSE_ROI",
                "3": "MEAN_DOSE_ROI",
                "4": "MEAN_DOSE_ROI",
                "5": "DOSE_VOLUME_PERCENT_ROI",
                "6": "DOSE_VOLUME_CC_ROI",
                "7": "DOSE_VOLUME_PERCENT_ROI",
                "8": "DOSE_VOLUME_CC_ROI",
                "9": "VOLUME_PERCENT_DOSE_ROI",
                "10": "VOLUME_CC_DOSE_ROI",
                "11": "VOLUME_PERCENT_DOSE_ROI",
                "12": "VOLUME_CC_DOSE_ROI",
                }


def convert(output_filename):
    global manual_file_path
    if manual_file_path != "":
        xml_file_path = manual_file_path
    else:
        _, plan_dir = get_plans()
        xml_file_path = fr'{plan_dir}\{plan_str_var.get()}\isodosesettings.xml'

    if output_filename != "":
        # enter the file name as a header
        structures_box.insert(END, "------------------\n")
        structures_box.insert(END, f"{output_filename}\n")
        structures_box.insert(END, "------------------\n")
        # initialise list of goals
        goaldict_list = []
        # Parse the contents of the selected XML file
        tree = parse(xml_file_path)
        root = tree.getroot()

        # loop through all structures
        for struct in root.find("Data").find("IsodoseSettings").find("DoseStructureParametersList").findall("DoseStructureParameter"):
            structure_name = struct.find("StructureName").text
            goals = struct.find("DoseGoalList").findall("DoseGoal")
            # loop through all goals in the structure
            for goal in goals:
                goaldict = {}
                goaltype = goal.find("GoalType").text
                # set type, name, and other default values
                goaldict["type"] = type_lookup[goaltype]
                goaldict["roi_name"] = structure_name
                goaldict["rx"] = None
                goaldict["rx_scale"] = None
                goaldict["arg_1"] = None # default to None
                goaldict["arg_2"] = None

                # Min Dose Roi: D >= Gy
                if goaltype == "1":
                    dose = float(goal.find("Dose").text) / 100
                    # set the objectives
                    objectives = [{"label": "FAIL", "color": [255, 0, 0]},
                                  {"label": "PASS", "color": [18, 191, 0], "min": dose}]
                    structures_box.insert(END, f"Min Dose to {structure_name}: {dose}Gy\n")
                    # add a warning level if there is a tolerance
                    if goal.find("Tolerance").text != "0":
                        tol = float(goal.find("Tolerance").text) / 100
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "min": dose - tol})
                        # delete the line we just put in above
                        structures_box.delete("end-2l", "end-1l")
                        # add in the new line with the tol included
                        structures_box.insert(END, f"Min Dose to {structure_name}: {dose}Gy (-{tol})\n")
                    goaldict["objectives"] = objectives
                    # print the goal to the text box


                # Max Dose Roi: D <= Gy
                elif goaltype == "2":
                    dose = float(goal.find("Dose").text) / 100
                    objectives = [{"label": "PASS", "color": [18, 191, 0], "max": dose},
                                  {"label": "FAIL", "color": [255, 0, 0]}]
                    structures_box.insert(END, f"Max Dose to {structure_name}: {dose}Gy\n")
                    if goal.find("Tolerance").text != "0":
                        tol = float(goal.find("Tolerance").text) / 100
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "max": dose + tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(END, f"Max Dose to {structure_name}: {dose}Gy (+{tol})\n")
                    goaldict["objectives"] = objectives


                # Mean Dose Roi
                elif goaltype == "3":  # then its D >= Gy
                    if goal.find("Dose").text not in ['0', 'INF']:  # then its D >= Gy
                        dose=float(goal.find("Dose").text) / 100
                        objectives = [{"label": "FAIL", "color": [255, 0, 0]},
                                      {"label": "PASS", "color": [18, 191, 0], "min": dose}]
                        structures_box.insert(END, f"{structure_name}:Dmean >= {dose}Gy\n")

                        if goal.find("Tolerance").text != "0": # then it's D >= Gy(-Gy)
                            tol = float(goal.find("Tolerance").text) / 100
                            objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                           "min": (dose - tol)})
                            # delete the line we just put in above
                            structures_box.delete("end-2l", "end-1l")
                            # add in the new line with the tol included
                            structures_box.insert(END,
                                             f"{structure_name}: Dmean >= {dose}Gy (-{tol}Gy)\n")


                        if goal.find("MeanDoseMaximum") != None: # monaco v5 doesn't have this part.
                            if goal.find("MeanDoseMaximum").text != "INF":  # then it's Gy >= D >= Gy
                                meanmax = float(goal.find("MeanDoseMaximum").text) / 100
                                if goal.find(
                                        "MeanDoseMaxTolerance").text == "0":  # then it's Gy(-Gy) <= D <= Gy. # switched sign order as this is what Monaco does.
                                    objectives.append({"label": "FAIL", "color": [255, 0, 0],
                                                       "min": meanmax})
                                    structures_box.delete("end-2l", "end-1l")
                                    structures_box.insert(END,
                                                          f"{structure_name}: {dose}Gy (-{tol}Gy) <= Dmean <= {meanmax}Gy\n")
                                else:  # then it's Gy(-Gy) <= D <= Gy(+Gy)
                                    meanmaxtol = float(goal.find("MeanDoseMaxTolerance").text) / 100
                                    objectives.append({"label": "WARNING", "color": [255, 216, 0],
                                                       "min": meanmax})
                                    objectives.append({"label": "FAIL", "color": [255, 0, 0], "min": meanmax + meanmaxtol})
                                    structures_box.delete("end-2l", "end-1l")
                                    structures_box.insert(END,
                                                          f"{structure_name}: {dose}Gy(-{tol}Gy) <= Dmean <= {meanmax}Gy (+{meanmaxtol}Gy)\n")

                    # for monaco v5, this will always be goaltype 4.
                    else:  # D <= Gy
                        meanmax = float(goal.find("MeanDoseMaximum").text) / 100
                        objectives = [{"label": "PASS", "color": [18, 191, 0],
                                       "max": meanmax},
                                      {"label": "FAIL", "color": [255, 0, 0]}]
                        structures_box.insert(END,
                                              f"{structure_name}: Dmean <= {meanmax}Gy\n")
                        if goal.find("MeanDoseMaxTolerance").text != "0":  # D <= Gy(+Gy)
                            meanmaxtol = float(
                                goal.find("MeanDoseMaxTolerance").text) / 100
                            objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                                  "max": meanmax + meanmaxtol})
                            structures_box.delete("end-2l", "end-1l")
                            structures_box.insert(END,
                                                  f"{structure_name}: Dmean <= {meanmax}Gy (+{meanmaxtol}Gy)\n")
                    goaldict["objectives"] = objectives


                # monaco 6 combined 3 and 4 into just 3, so this is only here for v5 files.
                elif goaltype == "4": # then its: D <= Gy
                    dose = float(goal.find("Dose").text) / 100
                    objectives = [{"label": "PASS", "color": [18, 191, 0],
                                   "max": dose},
                                  {"label": "FAIL", "color": [255, 0, 0]}]
                    structures_box.insert(END,
                                     f"{structure_name}: Dmean <= {dose}Gy\n")
                    if goal.find("Tolerance").text != "0": #  D <= Gy(+Gy)
                        tol = float(
                            goal.find("Tolerance").text) / 100
                        objectives.insert(1,  {"label": "WARNING", "color": [255, 216, 0],
                                       "max": dose + tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(END,
                                         f"{structure_name}: Dmean <= {dose}Gy (+{tol}Gy)\n")

                    goaldict["objectives"] = objectives


                elif goaltype == "5": # DtoVol% >= Gy
                    vol = float(goal.find("Volume").text)
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = vol

                    objectives = [{"label": "FAIL", "color": [255, 0, 0]},
                                  {"label": "PASS", "color": [18, 191, 0], "min": dose}]
                    structures_box.insert(END,
                                     f"D{vol}% >= {dose}Gy\n")
                    if goal.find("Tolerance").text != "0": #  DtoVol% >= Gy(-Gy)
                        tol = float(goal.find("Tolerance").text) / 100
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "min": dose - tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(END,
                                         f"{structure_name}: D{vol}% >= {dose}Gy (-{tol}Gy)\n")
                    goaldict["objectives"] = objectives


                elif goaltype == "6": #  DtoVolcc >= Gy
                    vol = float(goal.find("Volume").text) / 1000 # convert to cc
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = vol

                    objectives = [{"label": "FAIL", "color": [255, 0, 0]},
                                  {"label": "PASS", "color": [18, 191, 0], "min": dose}]
                    structures_box.insert(END,
                                     f"D{vol}cc >= {dose}Gy\n")
                    if goal.find("Tolerance").text != "0": #  DtoVolcc >= Gy(-Gy)
                        tol = float(goal.find("Tolerance").text) / 100
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                              "min": dose - tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(END,
                                         f"{structure_name}: D{vol}cc >= {dose}Gy (-{tol}Gy)\n")
                    goaldict["objectives"] = objectives


                elif goaltype == "7": # DtoVol% <= Gy
                    vol = float(goal.find("Volume").text)
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = vol

                    objectives = [{"label": "PASS", "color": [18, 191, 0], "max": dose},
                                  {"label": "FAIL", "color": [255, 0, 0]}]
                    structures_box.insert(END,
                                     f"{structure_name}: D{vol}% <= {dose}Gy\n")

                    if goal.find("Tolerance").text != "0": # DtoVol% <= Gy(+Gy)
                        tol = float(goal.find("Tolerance").text) / 100
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "max": dose + tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(END,
                                         f"{structure_name}: D{vol}% <= {dose}Gy (+{tol}Gy)\n")

                    goaldict["objectives"] = objectives


                elif goaltype == "8": # DtoVolcc <= Gy
                    vol = float(goal.find("Volume").text) / 1000
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = vol

                    objectives = [{"label": "PASS", "color": [18, 191, 0], "max": dose},
                                  {"label": "FAIL", "color": [255, 0, 0]}]
                    structures_box.insert(END,
                                     f"{structure_name}: D{vol}cc <= {dose}Gy\n")

                    if goal.find("Tolerance").text != "0": # DtoVolcc <= Gy(+Gy)
                        tol = float(goal.find("Tolerance").text) / 100
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                              "max": dose + tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(END,
                                         f"{structure_name}: D{vol}cc <= {dose}Gy (+{tol}Gy)\n")

                    goaldict["objectives"] = objectives


                elif goaltype == "9": # VolGy >= %
                    dose = float(goal.find("Dose").text) / 100
                    vol = (float(goal.find("Volume").text))
                    goaldict["arg_1"] = dose

                    objectives = [{"label": "FAIL", "color": [255, 0, 0]},
                                  {"label": "PASS", "color": [18, 191, 0], "min": float(goal.find("Volume").text)}]
                    structures_box.insert(END,
                                     f"{structure_name}: V{dose}Gy >= {vol}%\n")
                    if goal.find("Tolerance").text != "0": # VolGy >= %(-%)
                        tol = float(goal.find("Tolerance").text)
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "min": vol - tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(END,
                                         f"{structure_name}: V{dose}Gy >= {vol}%(-{tol}%)\n")
                    goaldict["objectives"] = objectives


                elif goaltype == "10": # VolGy >= cc
                    vol = float(goal.find("Volume").text) / 1000
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = dose

                    objectives = [{"label": "FAIL", "color": [255, 0, 0]},
                                  {"label": "PASS", "color": [18, 191, 0], "min": vol}]
                    structures_box.insert(END,
                                     f"{structure_name}: V{dose}Gy >= {vol}cc\n")
                    if goal.find("Tolerance").text != "0": # VolGy >= cc(-cc)
                        tol = float(goal.find("Tolerance").text) / 1000
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "min": vol - tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(END,
                                         f"{structure_name}: V{dose}Gy >= {vol}cc(-{tol}cc)\n")
                    goaldict["objectives"] = objectives


                elif goaltype == "11": # VolGy <= %
                    vol = float(goal.find("Volume").text)
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = dose
                    objectives = [{"label": "PASS", "color": [18, 191, 0], "max": vol},
                                  {"label": "FAIL", "color": [255, 0, 0]}]
                    structures_box.insert(END,
                                     f"{structure_name}: V{dose}Gy <= {vol}%\n")
                    if goal.find("Tolerance").text != "0": # VolGy <= %(+%)
                        tol = float(goal.find("Tolerance").text)
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "max": vol + tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(END,
                                         f"{structure_name}: V{dose}Gy <= {vol}%(+{tol}%)\n")
                    goaldict["objectives"] = objectives


                elif goaltype == "12": # VolGy <= cc
                    vol = float(goal.find("Volume").text) / 1000
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = dose
                    objectives = [{"label": "PASS", "color": [18, 191, 0], "max": vol},
                                  {"label": "FAIL", "color": [255, 0, 0]}]
                    structures_box.insert(END,
                                     f"{structure_name}: V{dose}Gy <= {vol}cc\n")
                    if goal.find("Tolerance").text != "0": # VolGy <= cc(+cc)
                        tol = float(goal.find("Tolerance").text) / 1000
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                              "max": vol + tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(END,
                                         f"{structure_name}: V{dose}Gy <= {vol}cc(+{tol}cc)\n")
                    goaldict["objectives"] = objectives

                # add the goal to the list of goals
                goaldict_list.append(goaldict)


        # add the list of goals to the scorecard dict
        scorecard = {"computed": goaldict_list,
                     "custom": []}

        # Write the dictionary to a JSON file
        with open(f"{output_filename}.json", "w") as json_file:
            dump(scorecard, json_file, indent=2)

        # remove text from boxes
        out_box.delete(0,END)
        XML_box.delete(0, END)
        nhi_box.delete(0,END)
        plan_combobox.delete(0, END)
        clinic_combobox.delete(0, END)
        manual_file_path = ""
        messagebox.showinfo("Success!", message=f"Scorecard Template saved as: {output_filename}.json")


#create GUI window
window = Tk()
window.title("Monaco to ProKnow Scorecard")
window.geometry("500x500")

# Set the theme with the theme_use method
ttk.Style().theme_use("clam")

# create clinic label
clinic_label = ttk.Label(window, text="Select Clinic:")
clinic_label.grid(row=0, column=0, pady=10)

# create clinic dropdown
clinic_combobox = ttk.Combobox(window)
clinic_combobox.grid(row=1, column=0, pady=10)
#populate the combobox with the clinics we found earlier
clinic_combobox['values'] = clinics


# create nhi label
nhi_label = ttk.Label(window, text="Enter patient ID:")
nhi_label.grid(row=0, column=1, pady=10)
# create NHI entry box
nhi_str_var = StringVar(window)
nhi_str_var.trace("w", populate_plans)
nhi_box = ttk.Entry(window, width=25, textvariable=nhi_str_var)
nhi_box.grid(row=1, column=1)

# create plan label
plan_label = ttk.Label(window, text="Select Plan:")
plan_label.grid(row=0, column=2, pady=10)
# create plan dropdown
plan_str_var = StringVar(window)
plan_combobox = ttk.Combobox(window, textvariable=plan_str_var)
plan_combobox.grid(row=1, column=2, pady=10)

s = ttk.Separator(window, orient="horizontal")

# create file selector button.
select_button = ttk.Button(window, text="OR: Select File", state="enabled", command=lambda: load_file_dialog())
select_button.grid(row=2, column=1, pady=10)
XML_box = ttk.Entry(window, width=30)
XML_box.grid(row=3, column=1, columnspan=2, sticky='w')


# create label
file_label = ttk.Label(window, text="Enter scorecard file name:")
file_label.grid(row=6, columnspan=3, pady=10)

# Create the entry box
out_box = ttk.Entry(window, width=25)
out_box.grid(row=7, column=1)

# create .json label
json_label = ttk.Label(window, text=".json", anchor="w")
json_label.grid(row=7, column=2, sticky="w")
# create generate button which is disabled until the XML is selected
button = ttk.Button(window, text="Generate", state="enabled", command=lambda: convert(out_box.get()))
button.grid(row=8, columnspan=3, pady=10)

# Create the text box for logging (with scroll functionality)
structures_box = scrolledtext.ScrolledText(window, width=60, height=14, wrap=WORD)
structures_box.grid(row=9, columnspan=3)

window.mainloop()
