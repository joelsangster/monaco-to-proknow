import json
import os.path
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext

# create lookup table to cross-reference goal types
type_lookup = { "1": "MIN_DOSE_ROI",
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
                }

def selectXML():
    # Open file dialog and get the file path
    global file_path
    file_path= filedialog.askopenfilename(
        title="Select an XML file",
        filetypes=[("XML files", "*.xml")])
    # get just the file name
    dir, file = os.path.split(file_path)
    # place the xml file name in the text box
    XML_box.insert(index=0, string=file)
    # enable the 'generate' button
    button.config(state="normal")


def convert(file_path, output_filename):
    if output_filename != "":
        # enter the file name as a header
        structures_box.insert(tk.END, f"{output_filename}\n")
        structures_box.insert(tk.END, "------------------\n")
        # initialise list of goals
        goaldict_list = []
        # Parse the contents of the selected XML file
        tree = ET.parse(file_path)
        root = tree.getroot()

        # loop through all structures
        for struct in root.find("DoseStructureParameters").findall("DoseStructureParametersData"):
            structure_name = struct.find("StructName").text
            goals = struct.find("DoseGoals").findall("DoseGoalData")
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
                    # set the objectives
                    objectives = [{"label": "FAIL", "color": [255, 0, 0]},
                                  {"label": "PASS", "color": [18, 191, 0], "min": float(goal.find("Dose").text) / 100}]
                    # add a warning level if there is a tolerance
                    if goal.find("Tolerance").text != "0":
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "min": (float(goal.find("Dose").text) - float(goal.find("Tolerance").text)) / 100})

                    goaldict["objectives"] = objectives
                    # print the goal to the text box
                    structures_box.insert(tk.END, f"Min Dose to {structure_name}\n")

                # Max Dose Roi: D <= Gy
                elif goaltype == "2":
                    objectives = [{"label": "PASS", "color": [18, 191, 0], "max": float(goal.find("Dose").text) / 100},
                                  {"label": "FAIL", "color": [255, 0, 0]}]
                    if goal.find("Tolerance").text != "0":
                        objectives.insert({"label": "WARNING", "color": [255, 216, 0],
                                       "max": (float(goal.find("Dose").text) + float(goal.find("Tolerance").text)) / 100})
                    goaldict["objectives"] = objectives
                    structures_box.insert(tk.END, f"Max Dose to {structure_name}\n")

                # Mean Dose Roi
                elif goaltype == "3":
                    if goal.find("Dose").text != "INF":  # then its D >= Gy
                        dose=float(goal.find("Dose").text) / 100
                        objectives = [{"label": "FAIL", "color": [255, 0, 0]},
                                      {"label": "PASS", "color": [18, 191, 0], "min": dose}]
                        structures_box.insert(tk.END, f"{structure_name}:Dmean >= {dose}Gy\n")

                        if goal.find("Tolerance").text != "INF": # then it's D >= Gy(-Gy)
                            tol = float(goal.find("Tolerance").text) / 100
                            objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                           "min": (dose - tol)})
                            # delete the line we just put in above
                            structures_box.delete("end-2l", "end-1l")
                            structures_box.insert(tk.END,
                                             f"{structure_name}: Dmean >= {dose}Gy (-{tol}Gy)\n")

                        if goal.find("MeanDoseMaximum").text != "INF":  # then it's Gy >= D >= Gy
                            meanmax=float(goal.find("MeanDoseMaximum").text) / 100
                            if goal.find("MeanDoseMaxTolerance").text == "0": # then it's Gy(-Gy) <= D <= Gy. # switched sign order as this is what Monaco does.
                                objectives.append({"label": "FAIL", "color": [255, 0, 0],
                                                   "min": meanmax})
                                structures_box.delete("end-2l", "end-1l")
                                structures_box.insert(tk.END,
                                                 f"{structure_name}: {dose}Gy (-{tol}Gy) <= Dmean <= {meanmax}Gy\n" )
                            else: # then it's Gy(-Gy) <= D <= Gy(+Gy)
                                meanmaxtol=float(goal.find("MeanDoseMaxTolerance").text) / 100
                                objectives.append({"label": "WARNING", "color": [255, 216, 0],
                                                   "min": meanmax})
                                objectives.append({"label": "FAIL", "color": [255, 0, 0], "min": meanmax + meanmaxtol})
                                structures_box.delete("end-2l", "end-1l")
                                structures_box.insert(tk.END,
                                                 f"{structure_name}: {dose}Gy(-{tol}Gy) <= Dmean <= {meanmax}Gy (+{meanmaxtol}Gy)\n")


                    else:  #  D <= Gy
                        meanmax = float(goal.find("MeanDoseMaximum").text) / 100
                        objectives = [{"label": "PASS", "color": [18, 191, 0],
                                       "max": meanmax},
                                      {"label": "FAIL", "color": [255, 0, 0]}]
                        structures_box.insert(tk.END,
                                         f"{structure_name}: Dmean <= {meanmax}Gy\n")
                        if goal.find("MeanDoseMaxTolerance").text != "0": #  D <= Gy(+Gy)
                            meanmaxtol = float(
                                goal.find("MeanDoseMaxTolerance").text) / 100
                            objectives.insert(1,  {"label": "WARNING", "color": [255, 216, 0],
                                           "max": meanmax + meanmaxtol})
                            structures_box.delete("end-2l", "end-1l")
                            structures_box.insert(tk.END,
                                             f"{structure_name}: Dmean <= {meanmax}Gy (+{meanmaxtol}Gy)\n")

                    goaldict["objectives"] = objectives


                elif goaltype == "5": # DtoVol% >= Gy
                    vol = float(goal.find("Volume").text)
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = vol

                    objectives = [{"label": "FAIL", "color": [255, 0, 0]},
                                  {"label": "PASS", "color": [18, 191, 0], "min": dose}]
                    structures_box.insert(tk.END,
                                     f"D{vol}% >= {dose}Gy\n")
                    if goal.find("Tolerance").text != "0": #  DtoVol% >= Gy(-Gy)
                        tol = float(goal.find("Tolerance").text) / 100
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "min": dose - tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(tk.END,
                                         f"{structure_name}: D{vol}% >= {dose}Gy (-{tol}Gy)\n")
                    goaldict["objectives"] = objectives

                elif goaltype == "6": #  DtoVolcc >= Gy
                    vol = float(goal.find("Volume").text) / 1000 # convert to cc
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = vol

                    objectives = [{"label": "FAIL", "color": [255, 0, 0]},
                                  {"label": "PASS", "color": [18, 191, 0], "min": dose}]
                    structures_box.insert(tk.END,
                                     f"D{vol}cc >= {dose}Gy\n")
                    if goal.find("Tolerance").text != "0": #  DtoVolcc >= Gy(-Gy)
                        tol = float(goal.find("Tolerance").text) / 100
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                              "min": dose - tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(tk.END,
                                         f"{structure_name}: D{vol}cc >= {dose}Gy (-{tol}Gy)\n")
                    goaldict["objectives"] = objectives


                elif goaltype == "7": # DtoVol% <= Gy
                    vol = float(goal.find("Volume").text)
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = vol

                    objectives = [{"label": "PASS", "color": [18, 191, 0], "max": dose},
                                  {"label": "FAIL", "color": [255, 0, 0]}]
                    structures_box.insert(tk.END,
                                     f"{structure_name}: D{vol}% <= {dose}Gy\n")

                    if goal.find("Tolerance").text != "0": # DtoVol% <= Gy(+Gy)
                        tol = float(goal.find("Tolerance").text) / 100
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "max": dose + tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(tk.END,
                                         f"{structure_name}: D{vol}% <= {dose}Gy (+{tol}Gy)\n")

                    goaldict["objectives"] = objectives

                elif goaltype == "8": # DtoVolcc <= Gy
                    vol = float(goal.find("Volume").text) / 1000
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = vol

                    objectives = [{"label": "PASS", "color": [18, 191, 0], "max": dose},
                                  {"label": "FAIL", "color": [255, 0, 0]}]
                    structures_box.insert(tk.END,
                                     f"{structure_name}: D{vol}cc <= {dose}Gy\n")

                    if goal.find("Tolerance").text != "0": # DtoVolcc <= Gy(+Gy)
                        tol = float(goal.find("Tolerance").text) / 100
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                              "max": dose + tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(tk.END,
                                         f"{structure_name}: D{vol}cc <= {dose}Gy (+{tol}Gy)\n")

                    goaldict["objectives"] = objectives



                elif goaltype == "9": # VolGy >= %
                    dose = float(goal.find("Dose").text) / 100
                    vol = (float(goal.find("Volume").text))
                    goaldict["arg_1"] = dose

                    objectives = [{"label": "FAIL", "color": [255, 0, 0]},
                                  {"label": "PASS", "color": [18, 191, 0], "min": float(goal.find("Volume").text)}]
                    structures_box.insert(tk.END,
                                     f"{structure_name}: V{dose}Gy >= {vol}%\n")
                    if goal.find("Tolerance").text != "0": # VolGy >= %(-%)
                        tol = float(goal.find("Tolerance").text)
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "min": vol - tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(tk.END,
                                         f"{structure_name}: V{dose}Gy >= {vol}%(-{tol}%)\n")
                    goaldict["objectives"] = objectives


                elif goaltype == "10": # VolGy >= cc
                    vol = float(goal.find("Volume").text) / 1000
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = dose

                    objectives = [{"label": "FAIL", "color": [255, 0, 0]},
                                  {"label": "PASS", "color": [18, 191, 0], "min": vol}]
                    structures_box.insert(tk.END,
                                     f"{structure_name}: V{dose}Gy >= {vol}cc\n")
                    if goal.find("Tolerance").text != "0": # VolGy >= cc(-cc)
                        tol = float(goal.find("Tolerance").text) / 1000
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "min": vol - tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(tk.END,
                                         f"{structure_name}: V{dose}Gy >= {vol}cc(-{tol}cc)\n")
                    goaldict["objectives"] = objectives


                elif goaltype == "11": # VolGy <= %
                    vol = float(goal.find("Volume").text)
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = dose
                    objectives = [{"label": "PASS", "color": [18, 191, 0], "max": vol},
                                  {"label": "FAIL", "color": [255, 0, 0]}]
                    structures_box.insert(tk.END,
                                     f"{structure_name}: V{dose}Gy <= {vol}%\n")
                    if goal.find("Tolerance").text != "0": # VolGy <= %(+%)
                        tol = float(goal.find("Tolerance").text)
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                       "min": vol + tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(tk.END,
                                         f"{structure_name}: V{dose}Gy <= {vol}%(+{tol}%)\n")
                    goaldict["objectives"] = objectives

                elif goaltype == "12": # VolGy <= cc
                    vol = float(goal.find("Volume").text) / 1000
                    dose = float(goal.find("Dose").text) / 100
                    goaldict["arg_1"] = dose
                    objectives = [{"label": "PASS", "color": [18, 191, 0], "max": vol},
                                  {"label": "FAIL", "color": [255, 0, 0]}]
                    structures_box.insert(tk.END,
                                     f"{structure_name}: V{dose}Gy <= {vol}cc\n")
                    if goal.find("Tolerance").text != "0": # VolGy <= cc(+cc)
                        tol = float(goal.find("Tolerance").text) / 1000
                        objectives.insert(1, {"label": "WARNING", "color": [255, 216, 0],
                                              "min": vol + tol})
                        structures_box.delete("end-2l", "end-1l")
                        structures_box.insert(tk.END,
                                         f"{structure_name}: V{dose}Gy <= {vol}cc(+{tol}cc)\n")
                    goaldict["objectives"] = objectives


                # add the goal to the list of goals
                goaldict_list.append(goaldict)


        # add the list of goals to the scorecard dict
        scorecard = {"computed": goaldict_list,
                     "custom": []}

        # Write the dictionary to a JSON file
        with open(f"{output_filename}.json", "w") as json_file:
            json.dump(scorecard, json_file, indent=2)

        # remove text from boxes
        XML_box.delete(0,tk.END)
        out_box.delete(0,tk.END)
        messagebox.showinfo("Success!", message=f"Scorecard Template saved as: {output_filename}.json")



#create GUI window
window = tk.Tk()
window.title("Monaco to ProKnow Scorecard")
window.geometry("500x350")

# Set the theme with the theme_use method
ttk.Style().theme_use("clam")

# create select button
select = ttk.Button(window, text="Select XML File", command=selectXML)
select.grid(row=0, columnspan=2, pady=10)
# create text box
XML_box = ttk.Entry(window, width=30)
XML_box.grid(row=1, columnspan=2)
# create label
file_label = ttk.Label(window, text="Enter output file name:")
file_label.grid(row=2, columnspan=2, pady=10)
# Create the entry box
out_box = ttk.Entry(window, width=25)
out_box.grid(row=3, column=0, sticky="e")
# create .json label
json_label = ttk.Label(window, text=".json", anchor="w")
json_label.grid(row=3, column=1, sticky="w")
# create generate button which is disabled until the XML is selected
button = ttk.Button(window, text="Generate", state="disabled", command=lambda: convert(file_path, out_box.get()))
button.grid(row=4, columnspan=2, pady=10)
# Create the text box for logging (with scroll functionality)
structures_box = scrolledtext.ScrolledText(window, width=60, height=10, wrap=tk.WORD)
structures_box.grid(row=5, columnspan=2)

window.mainloop()