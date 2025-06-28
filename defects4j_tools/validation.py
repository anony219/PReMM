from defects4j_tools.defects4j import compile_files, test_project
from utils import check_file_list, modify_files, recover_files, generate_patch_diff


# repaired_codes:[{"file_path":xxx, "repaired_snippets":[{"line_begin":xx, "line_end": xx, "repaired_code":"xx"}...]},...]
def validate_repaired_code(database_name, bug_id, working_dir, classes_path, repaired_codes: list):
    file_list = [repaired_code["file_path"] for repaired_code in repaired_codes]
    if not check_file_list(working_dir, file_list):
        print("The repaired codes are in wrong file!")
        return False
    modify_files(working_dir, repaired_codes)
    compile_flag = True
    try:
        compile_results = compile_files(database_name, working_dir, classes_path, file_list)
        for compile_result in compile_results:
            if compile_result["compiled_result"] is False:
                compile_flag = False
                break
        if not compile_flag:
            recover_files(working_dir, file_list)
            compile_files(database_name, working_dir, classes_path, file_list)
            print(f"The generated repaired codes are compiled error with the following info {str(compile_results)}. "
                  f"Please regenerate the repaired code.")
            return False
        test_result = test_project(database_name, bug_id, working_dir)
        if len(test_result) == 0:
            # recover_files(working_dir, file_list)
            # compile_files(database_name, working_dir, classes_path, file_list)
            generate_patch_diff(bug_id, working_dir, file_list)
            print("The repaired codes passed all the test cases!")
            return True
        else:
            recover_files(working_dir, file_list)
            compile_files(database_name, working_dir, classes_path, file_list)
            print(f"The repaired codes did not pass all the test cases with the following info {str(test_result)}. "
                  f"Please regenerate the repaired code.")
            return False
    except Exception as e:
        recover_files(working_dir, file_list)
        compile_files(database_name, working_dir, classes_path, file_list)
        print(f"When validate the repaired codes, there encountered an exception with the following info {str(e)}.")
        return True
