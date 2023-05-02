# GET CONTRACT INFO AND HASH COUNT PER CONTRACT FUNCTION USING WEB3.PY AND INFURA (V6)
# d0ughnutz
# 2023

"""

OVERVIEW
1. Useful for extracting information about a list (or single) of contracts including contract name, contract functions,
   and transaction counts for each of the functions associated with the contract
2. Script will accept a CSV file of any number of contracts and using Web3.py and Infura, return the contract
   information including name and functions and a count of the hashes associated with each function to a CSV file

DIRECTIONS
1. Setup source CSV file with list of contracts
2. Set variables in 'VARIABLE LIST' below - directory, api keys

NOTES
1. API keys are required for both Etherscan and Infura APIs
2. Run times may be long for contracts with many transactions (in the millions) as the Infura API is called for each
   contract function which limits the results to a block range of ~1,000,000 before errors

"""

from web3 import Web3
import requests
import pandas as pd

# VARIABLE LIST - UPDATE AS NEEDED
blockchain = 'Ethereum'
directory = 'C:/Users/user/folder'  # update
contract_file = f'{directory}/contracts.csv'
apikey_etherscan = ''  # update
apikey_infura = ''  # update

# SEA SHELLS
addr_list = []
events_dict = {}
events_list = []
con_fun = []
all_hash = []
all_con = {}


# [GET] CONTRACTS FROM CSV, SAVE TO LIST
def get_csv():
    with open(contract_file) as file:
        for c in file:
            contract = c.strip('\n').lower()
            addr_list.append(contract)
        print(f'[{len(addr_list)}] contracts obtained from csv file')
        print('Moving to next function [get_abi]')
        print('+++')
        get_contract_info()


# [LOOP] THROUGH EACH CONTRACT IN LIST AND GET ABI, ABI FUNCTIONS, AND ABI FUNCTION EVENT COUNTS
def get_contract_info():
    counter = 0
    try:
        for co in addr_list:
            # [GET] CONTRACT ABI FROM ETHERSCAN
            print(f'[{counter}] Getting ABI for contract [{co}]')

            # [FORMAT] ADDRESS IF ANY EXTRA CHARACTERS
            if len(co) == 43:
                con = co[1:66]
            else:
                con = co
            abi_url = f'https://api.etherscan.io/api?module=contract&action=getabi&address={con}&' \
                      f'apikey={apikey_etherscan}'
            response = requests.get(abi_url).json()
            abi = response['result']

            # [SKIP] IF DID NOT GET ABI
            if abi is None:
                print(f'[{counter}] ERROR: Did not get ABI')
                print('Moving to next contract')
                all_con_item = {counter: [con, 'Did not get ABI', 'NA', 'NA']}
                all_con.update(all_con_item)

            # [SKIP] IF ERROR FOR SOURCE CODE NOT VERIFIED
            elif abi == 'Contract source code not verified':
                print(f'[{counter}] ERROR: No ABI as contract source code not verified')
                print('Moving to next contract')
                all_con_item = {counter: [con, 'No ABI as contract source code not verified', 'NA', 'NA']}
                all_con.update(all_con_item)

            else:
                # [CONNECT] TO INFURA
                web3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{apikey_infura}'))
                contract = web3.to_checksum_address(con)
                contract = web3.eth.contract(address=contract, abi=abi)
                latest = web3.eth.block_number
                print(f'[{counter}] SUCCESS: Contract info obtained from Etherscan and Infura')

                # [GET] CONTRACT NAME
                try:
                    name = contract.functions.name().call()
                except:
                    name = False

                # [SKIP] IF NO CONTRACT NAME, SKIP AS LIKELY PROXY OR ANONYMOUS
                if name is False:
                    print(f'[{counter}] ABI [{abi[0:200]}]')
                    print(f'[{counter}] Contract not readable')
                    print('Moving to next contract')
                    all_con_item = {counter: [con, 'Contract not readable', 'NA', 'NA']}
                    all_con.update(all_con_item)

                else:
                    # [GET] FUNCTIONS AND FORMAT TO REMOVE SPECIAL CHARACTERS
                    abi_fun = contract.all_functions()
                    abi_fun_list = [abi_fun]
                    functions = []
                    for items in abi_fun_list:
                        for fun in items:
                            fun_string = str(fun)
                            fun_trim = fun_string[10:-1]
                            if fun_trim[0] == '_':
                                fun_trim1 = fun_trim[1].upper() + fun_trim[2:fun_trim.rfind('(')]
                            else:
                                fun_trim1 = fun_trim[0].upper() + fun_trim[1:fun_trim.rfind('(')]
                            functions.append(fun_trim1)

                    # [PRINT] CONTRACT SUMMARY
                    print(f'[{counter}] NAME [{name}]')
                    print(f'[{counter}] ABI [{abi[0:200]}]')
                    print(f'[{counter}] FUNCTIONS [{functions}]')

                    # [GET] FUNCTION EVENTS, ADD CORRESPONDING HASHES TO 'FUN_EVENTS_LIST', COUNT TOTAL FUN EVENTS
                    print(f'[{counter}] Starting analysis of [{len(functions)}] contract functions:')
                    con_hashes_temp = {}  # temporary holder of hashes used for final dict

                    for fun in functions:
                        fun_events_temp = []
                        page = 0
                        functions = True
                        step_counter = 100000  # limits block range due to Infura transaction thresholds
                        end_block = latest
                        start_block = latest - step_counter

                        try:
                            while functions is True:
                                try:
                                    print(f'[{counter}] [{fun}] Checking page [{page}] with block range from '
                                          f'[{start_block} - {end_block}]')
                                    fun_events = contract.events.__getattribute__(fun). \
                                        create_filter(fromBlock=start_block, toBlock=end_block).get_all_entries()
                                    fun_events_temp.append(fun_events)
                                    if len(fun_events) == 0:
                                        print(f'[{counter}] Last page reached')
                                        print('+++')
                                        functions = False
                                    end_block = start_block
                                    start_block = end_block - step_counter

                                # IF ERROR, LIKELY TOO MANY RESULTS SO REDUCE BLOCK RANGE
                                except Exception as err:
                                    if 'object has no attribute' in str(err):
                                        print(f'[{counter}] [{fun}] Not found in "ContractEvents" object ')
                                        functions = False
                                    else:
                                        start_block = end_block - 2500
                                        print(f'[{counter}] [{fun}] Page [{page}] returned too many results. Trying '
                                              f'again with smaller block range [{start_block} - {end_block}]')
                                        fun_events = contract.events.__getattribute__(fun). \
                                            createFilter(fromBlock=start_block, toBlock=end_block).get_all_entries()
                                        fun_events_temp.append(fun_events)
                                        if len(fun_events) == 0:
                                            print(f'[{counter}] Last page reached')
                                            functions = False
                                        end_block = start_block
                                        start_block = end_block - 2500

                                page += 1

                        # [ERROR] CATCHES ALL FUNCTIONS THAT DO NOT HAVE ANY TRANSACTIONS
                        except Exception as err:
                            # print(f'[{counter}] FUN [{fun}] has no transactions. Moving to next function')
                            pass

                        # 1. FIND HASH IN EACH 'FUN_EVENTS_LIST' ITEM. ADD HASH, FUNCTION, CONTRACT TO 'ALL_HASH' LIST
                        # 2. ADD FUNCTION TO 'ALL_HASH_TEMP'
                        fun_count = 0
                        for funk in fun_events_temp:
                            for funky in funk:
                                funky_string = str(funky)
                                tx_hash_loc = funky_string.find('transactionHash')
                                tx_hash = funky_string[tx_hash_loc + 28: tx_hash_loc + 94]

                                # [OPTIONAL]
                                # [DICT] 'ALL_HASH' - EVERY HASH, FUNCTION, CONTRACT
                                fun_record = [tx_hash, fun, con]
                                all_hash.append(fun_record)  # optional if wanting

                                # [DICT] 'ALL_HASH' DICT - IF HASH NOT PRESENT, ADD CONTRACT, FUNCTION
                                tx_hash_shell = {tx_hash: []}
                                if tx_hash not in con_hashes_temp.keys():
                                    con_hashes_temp.update(tx_hash_shell)
                                con_hashes_temp[tx_hash].append(fun)
                                fun_count += 1

                        # [DICT] 'ALL_HASH' - ADD CONTRACT, NAME, FUNCTION, FUNCTION EVENT COUNT
                        if fun_count > 0:
                            con_item = [con, name, fun, fun_count]
                            con_fun.append(con_item)
                            all_con_item = {(str(counter) + '.' + fun): [con, name, fun, fun_count]}
                            all_con.update(all_con_item)
                            print(f'[{counter}] [{fun}] total events [{fun_count}]')

                    print(f'[{counter}] Contract total hashes [{len(con_hashes_temp.keys())}]')
                    print('Moving to next contract')

            counter += 1
            print('+++')

    except Exception as err:
        print(f'[ERROR] {err}')

    save_csv(counter)


# [SAVE] RESULTS TO CSV
def save_csv(counter):
    print(f'Moving to next function [save_csv]')
    print('+++')

    # [OPTIONAL]
    # [DATA] CREATE DF OF EVERY HASH (FOR EACH FUNCTION) AND SAVE TO CSV
    # print(f'Creating [all.hashes] df and saving to CSV')
    # all_hash_df = pd.DataFrame(all_hash, columns=['hash', 'function', 'contract'])
    # all_hash_df.to_csv(f'{directory}/all.hashes_{counter}.csv')

    # [DATA] CREATE DF FOR EVENTS_DICT AND SAVE TO CSV
    print(f'Creating [all.contracts.summary] df and saving to CSV')
    all_con_df = pd.DataFrame.from_dict(
        {k: v for k, v in all_con.items()}, orient='index', columns=['contract', 'name', 'fun', 'fun_count']). \
        rename_axis('id')
    all_con_df.to_csv(f'{directory}/all.contracts.summary_{counter}.csv')

    print(f'SUCCESS. Created and saved file at [{directory}]')
    print('+++')

    print('FIN')


# [INIT]
if __name__ == '__main__':
    get_csv()
