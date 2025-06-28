import os


def get_loc_file(dataset_name: str, bug_id, perfect):
    dirname = os.path.dirname(__file__)
    if perfect:
        loc_file = os.path.join("fault_location", dataset_name.lower(), "groundtruth", bug_id.split("-")[0].lower(),
                                bug_id.split("-")[1])
    else:
        loc_file = os.path.join("fault_location", dataset_name.lower(), "ochiai", bug_id.split("-")[0].lower(),
                                bug_id.split("-")[1])
    loc_file = os.path.join(dirname, loc_file)
    if os.path.isfile(loc_file):
        return os.path.abspath(loc_file)
    else:
        # print(loc_file)
        return ""


def fault_locate(dataset_name, bug_id):
    loc_file = get_loc_file(dataset_name, bug_id, "perfect")
    return loc_file
