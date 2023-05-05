# INFURA API, WEB3.PY, ETHERSCAN API  - Get Contract Info (ABI, Name, Functions) and All Hashes for Each Contract Function

OVERVIEW
- Useful for extracting information about a list (or single) of contracts including contract name, contract functions, transaction counts,         hashes, etc. for each of the functions associated with the contract
- Script will accept a CSV file of any number of contracts and using Infura API, Web3.py, Etherscan API (for ABI), return the contract
  information to a new CSV export file
   
NOTES
1. API keys are required for both Etherscan and Infura APIs
2. Run times may be long for contracts with many transactions (in the millions) as the Infura API is called for each
   contract function which limits the results to a block range of ~100,000 before errors
