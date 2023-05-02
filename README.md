# INFURA & WEB3.PY - Get Contract Info (ABI, Name, Functions) and All Hashes for Each Contract Function

OVERVIEW
- Useful for extracting information about a list (or single) of contracts including contract name, contract functions,
   and transaction counts for each of the functions associated with the contract
- Script will accept a CSV file of any number of contracts and using Web3.py and Infura, return the contract
   information including name and functions and a count of the hashes associated with each function to a CSV file
   
NOTES
1. API keys are required for both Etherscan and Infura APIs
2. Run times may be long for contracts with many transactions (in the millions) as the Infura API is called for each
   contract function which limits the results to a block range of ~1,000,000 before errors
