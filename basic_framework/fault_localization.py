import os
import utils


def get_loc_file(dataset_name: str, bug_id, perfect):
    dirname = utils.ROOT_PATH
    if perfect:
        loc_file = os.path.join( "datasets", dataset_name.lower(),"fault_location", "groundtruth", bug_id.split("-")[0].lower(),
                                bug_id.split("-")[1])
    else:
        loc_file = os.path.join("datasets", dataset_name.lower(),"fault_location", "ochiai", bug_id.split("-")[0].lower(),
                                bug_id.split("-")[1])
    loc_file = os.path.join(dirname, loc_file)
    if os.path.isfile(loc_file):
        return os.path.abspath(loc_file)
    else:
        # print(loc_file)
        return ""


def fault_locate(dataset_name, bug_id, perfect=True):
    loc_file = get_loc_file(dataset_name, bug_id, perfect)
    return loc_file
