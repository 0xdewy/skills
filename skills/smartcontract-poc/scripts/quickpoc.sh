#!/bin/bash

#===== VARIABLES ======

ZERO_ADDRESS=0x0000000000000000000000000000000000000000

# ===== FUNCTIONS ======

printUsage () {
   echo "Usage: $0 <address> [<folder>]"
   echo "       $0 -f <file> [<folder>]"
}

checkCommandExists () {
   if ! command -v $1 > /dev/null ; then
      echo "Command $1 not found, please install it before using this tool"
      exit 1
   fi
}

resolveLogic () {
   local addr=$1
   local slot
   local attempts=3
   local ok=0

   for i in $(seq 1 $attempts); do
      slot=$(timeout 15 cast storage "$addr" 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc 2>&1)
      if [ $? -eq 0 ]; then ok=1; break; fi
      echo "warn: cast storage attempt $i/$attempts failed for $addr, retrying..." >&2
      [ $i -lt $attempts ] && sleep 2
   done

   if [ $ok -eq 0 ]; then
      echo "error: cast storage failed for $addr after $attempts attempts" >&2
      exit 1
   fi

   local proxy_impl
   proxy_impl=$(cast --abi-decode "sig()(address)" "$slot")
   if [ "$proxy_impl" = "$ZERO_ADDRESS" ]; then
      echo "$addr"
   else
      echo "$proxy_impl"
   fi
}

fetchName () {
   local logic=$1
   local name
   name=$(curl -s "https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address=${logic}&apikey=${ETHERSCAN_API_KEY}" \
     | jq -r '.result[0].ContractName')
   echo "$name"
}

# ====== CHECKS ======

checkCommandExists jq
checkCommandExists forge
checkCommandExists cast
checkCommandExists curl

if [ -z "$ETHERSCAN_API_KEY" ]; then
   echo "Please set ETHERSCAN_API_KEY variable"
   exit 1
fi

if [ -z "$ETH_RPC_URL" ]; then
   echo "Please set ETH_RPC_URL variable"
   exit 1
fi

export ETHERSCAN_API_KEY ETH_RPC_URL

# ====== ARG PARSING ======

addresses=()
folder=""

if [ "$1" = "-f" ]; then
   if [ -z "$2" ]; then
      printUsage
      exit 1
   fi
   input_file="$2"
   folder="$3"
   if [ ! -f "$input_file" ]; then
      echo "error: file not found: $input_file"
      exit 1
   fi
   while IFS= read -r line || [ -n "$line" ]; do
      [[ -z "$line" || "$line" == \#* ]] && continue
      addresses+=("$line")
   done < "$input_file"
else
   if [ "${1:0:2}" != "0x" ]; then
      printUsage
      exit 1
   fi
   addresses=("$1")
   [ -n "$2" ] && folder="$2"
fi

if [ ${#addresses[@]} -eq 0 ]; then
   echo "error: no addresses provided"
   exit 1
fi

# ====== SETUP POC =====

# Derive folder name from first contract if not given
if [ -z "$folder" ]; then
   logic=$(resolveLogic "${addresses[0]}")
   folder=$(fetchName "$logic")
   if [ -z "$folder" ] || [ "$folder" = "null" ]; then
      echo "error: could not fetch contract name for ${addresses[0]}"
      exit 1
   fi
fi

if [ -d "$folder" ]; then
   echo "error: folder $folder already exists"
   exit 1
fi

forge init "$folder" || exit 1
cd "$folder"
rm -rf src script
rm -f test/Counter.t.sol

forge remappings > remappings.txt

for addr in "${addresses[@]}"; do
   logic=$(resolveLogic "$addr") || exit 1
   data_contract="$addr"

   name=$(fetchName "$logic") || { echo "error: could not fetch contract name for $addr"; exit 1; }
   if [ -z "$name" ] || [ "$name" = "null" ]; then
      echo "error: could not fetch contract name for $addr"
      exit 1
   fi

   cast_ok=0
   for i in $(seq 1 3); do
      cast source -d src --etherscan-api-key "$ETHERSCAN_API_KEY" \
        --explorer-api-url "https://api.etherscan.io/v2/api?chainid=1" "$logic" && cast_ok=1 && break
      echo "warn: cast source attempt $i/3 failed for $name, retrying in 5s..." >&2
      sleep 5
   done
   [ $cast_ok -eq 0 ] && { echo "error: cast source failed for $name after 3 attempts"; exit 1; }

   sleep 1

   for lib_path in $(ls -d src/${name}/*/ 2>/dev/null); do
      library=$(basename "$lib_path")
      echo "src/${name}/:${library}/=src/${name}/${library}/" >> remappings.txt
   done

   # detect pragma from first .sol file found in the contract's source
   pragma=$(grep -r -m1 "pragma solidity" src/${name}/ 2>/dev/null | grep -oP "pragma solidity [^;]+" | head -1)
   [ -z "$pragma" ] && pragma="pragma solidity ^0.8.0"

   testfile="test/${name}POC.t.sol"
   cat > "$testfile" << EOF
// SPDX-License-Identifier: MIT
${pragma};

import "forge-std/Test.sol";
EOF

   for file in $(find src/${name} \( -path "src/${name}/contracts/*.sol" -o -name 'Contract.sol' \) -type f); do
      echo "import \"../$file\";" >> "$testfile"
   done

   varname="${name,}"
   [ "$varname" = "$name" ] && varname="_${name}"

   cat >> "$testfile" << EOF

contract ${name}POC is Test {
  ${name} ${varname} = ${name}($data_contract);

  function test${name}POC() public {
      vm.createSelectFork('${ETH_RPC_URL}');
      assert(address(${varname}) == $data_contract);
  }
}
EOF
done

# ===== MISC =====

echo "cd $folder" | wl-copy 2>/dev/null || true
