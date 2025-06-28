import argparse
import utils
from basic_framework.repair_graph import get_repair_agent
from repair_defects4j import run_repair_defects4j

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, default="output")
    parser.add_argument("--lang", type=str, default="java")
    parser.add_argument("--dataset", type=str, default="defects4j", help="Dataset to use, current support: defects4j, defects4jv2")
    parser.add_argument("--model", type=str, default="Tongyi")
    parser.add_argument("--bug_id", type=str, default="Chart-1")
    parser.add_argument("--few_shot", type=int, default=0)
    parser.add_argument("--chain_length", type=int, default=1)
    parser.add_argument("--total_tries", type=int, default=3)
    parser.add_argument("--max_token", type=int, default=8192)
    parser.add_argument("-f", "--faulty_methods_clustering", help="flag that enable faulty methods clustering.",
                        action="store_true", default=False)
    parser.add_argument("-c", "--context_extraction", help="flag that enable context extraction.",
                        action="store_true", default=False)
    parser.add_argument("-d", "--dual_agent_based_patch_generation", help="flag that dual-agent-based patch generation.",
                        action="store_true", default=False)
    parser.add_argument("-i", "--invocation_prompt", help="flag that enable invocation chain prompt.",
                        action="store_true", default=False)
    parser.add_argument("-s", "--similar_codes_prompt", help="flag that enable similar codes prompt.",
                        action="store_true", default=False)
    parser.add_argument("-k", "--key_token_prompt", help="flag that enable key token prompt.",
                        action="store_true", default=False)
    parser.add_argument("-t", "--test_cases_prompt", help="flag that enable test cases prompt.",
                        action="store_true", default=False)

    args = parser.parse_args()
    utils.MAX_ITERATIONS = args.chain_length
    utils.Enable_FMC = args.faulty_methods_clustering
    utils.Enable_CX = args.context_extraction
    utils.Enable_DualAgent = args.dual_agent_based_patch_generation
    utils.repair_agent = get_repair_agent()
    if utils.MAX_ITERATIONS > 1:
        utils.Test_Case_Prompt = True
    if utils.Enable_CX:
        utils.Invocation_Chain_Prompt = True
        utils.Similar_Codes_Prompt = True
        utils.key_token_prompt = True
    utils.Repair_Result = False
    utils.Repair_Iterative_Count = 0
    utils.Prompt_Tokens = 0
    utils.Completion_Tokens = 0
    utils.Total_Prompt_Token = 0
    utils.Total_Completion_Token = 0
    version_name = utils.get_version_name()
    if args.dataset.startswith("defects4j"):
        run_repair_defects4j(args.total_tries,version_name, args.dataset, f"{args.bug_id}")
