# Foundry Reference (forge / cast / anvil / chisel)

Source: https://github.com/foundry-rs/foundry | https://getfoundry.sh

Install: `curl -L https://foundry.paradigm.xyz | bash && foundryup`

---

## forge

### Build

```bash
forge build
forge build --via-ir                    # compile via Yul IR (enables more optimizer passes)
forge build --optimize --optimizer-runs 1000000  # deployment optimization
forge build --optimizer-runs 1          # size optimization (minimizes bytecode)
forge build --evm-version cancun        # target EVM version
forge build --sizes                     # show contract sizes
```

### Test

```bash
forge test                              # run all tests
forge test -vvvv                        # maximum verbosity (all traces + logs)
forge test --match-test testFoo         # run specific test
forge test --match-contract MyTest      # run tests in specific contract
forge test --match-path test/Foo.t.sol  # run file
forge test --fork-url $RPC              # fork mainnet
forge test --fork-url $RPC --fork-block-number 20000000
forge test --gas-report                 # gas usage per function
forge test --gas-limit 30000000         # override block gas limit
forge test --fuzz-runs 10000            # fuzz iterations (default 256)
forge test --invariant-runs 500         # invariant test runs
forge coverage                          # coverage report (lcov)
forge coverage --report lcov && genhtml lcov.info -o coverage/
```

### Inspect contract artifacts

```bash
forge inspect MyContract abi
forge inspect MyContract bytecode           # creation bytecode
forge inspect MyContract deployedBytecode   # runtime bytecode
forge inspect MyContract storageLayout      # storage slot layout
forge inspect MyContract methodIdentifiers  # function selector → name
forge inspect MyContract gasEstimates
forge inspect MyContract devdoc
forge inspect MyContract userdoc
forge inspect MyContract assembly           # Yul IR output
```

### Script (deploy / interact)

```bash
forge script script/Deploy.s.sol --rpc-url $RPC --broadcast
forge script script/Deploy.s.sol --rpc-url $RPC --broadcast --verify
forge script script/Deploy.s.sol --rpc-url $RPC --broadcast --slow  # wait for inclusion
forge script script/Deploy.s.sol --sig "run(address)" 0xabc...  # call specific function
forge script --resume    # resume an interrupted broadcast
```

### Create (simple deploy without script)

```bash
forge create src/MyContract.sol:MyContract \
  --rpc-url $RPC \
  --private-key $PK \
  --constructor-args arg1 arg2 \
  --verify
```

### Debug (interactive step debugger)

```bash
forge debug src/MyContract.sol:MyContract --sig "myFunc(uint256)" 42
forge debug --debug <txhash> --rpc-url $RPC   # replay tx in debugger
# Debugger keys: s=step, n=step over, c=continue, q=quit, g=jump to PC
```

### foundry.toml key settings

```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
via_ir = true
optimizer = true
optimizer_runs = 200
evm_version = "cancun"
fuzz = { runs = 1000 }
invariant = { runs = 256, depth = 128 }
gas_reports = ["*"]
rpc_endpoints = { mainnet = "${MAINNET_RPC}" }
```

---

## Cheatcodes (forge-std / vm interface)

All cheatcodes are methods on `vm` (from `Test.sol`):

### State manipulation

```solidity
vm.prank(address);           // next call is from address
vm.startPrank(address);      // all calls until stopPrank() from address
vm.stopPrank();
vm.deal(address, 1 ether);   // set ETH balance
vm.store(addr, slot, val);   // write storage slot directly
vm.load(addr, slot);         // read storage slot (bytes32)
vm.etch(addr, bytecode);     // replace contract bytecode at address
vm.roll(blockNumber);        // set block.number
vm.warp(timestamp);          // set block.timestamp
vm.fee(baseFee);             // set block.basefee
vm.chainId(id);              // set chain ID
vm.coinbase(addr);           // set block.coinbase
```

### Assertions

```solidity
vm.expectRevert();                     // next call must revert
vm.expectRevert(bytes4 selector);      // must revert with custom error
vm.expectRevert("message");            // must revert with require message
vm.expectEmit(true, true, true, true); // check next event (indexed1,2,3, data)
emit MyEvent(args);                    // declaration of expected event
vm.expectCall(addr, calldata);         // assert a call is made
vm.expectCall(addr, value, calldata);
```

### Fork management

```solidity
uint256 mainnetFork = vm.createFork(vm.envString("RPC"));
uint256 optimismFork = vm.createFork(vm.envString("OP_RPC"));
vm.selectFork(mainnetFork);       // switch active fork
vm.rollFork(20000000);             // roll fork to specific block
vm.makePersistent(address);       // keep account state across fork switches
```

### Mocking

```solidity
vm.mockCall(addr, abi.encodeCall(IERC20.balanceOf, (user)), abi.encode(1000e18));
vm.clearMockedCalls();
```

### Signing / cryptography

```solidity
(uint8 v, bytes32 r, bytes32 s) = vm.sign(privateKey, digest);
address addr = vm.addr(privateKey);  // derive address from private key
bytes32 hash = vm.parseBytes32("0xabc...");
```

### Misc

```solidity
vm.label(address, "FriendlyName");    // label for traces
vm.snapshot(); / vm.revertTo(id);     // state snapshots
vm.getDeployedCode("Contract.sol:Contract");  // runtime bytecode
string memory json = vm.readFile("fixtures/data.json");
vm.writeFile("outputs/result.json", json);
```

---

## cast

### Reading chain state

```bash
cast call <addr> "balanceOf(address)" <user> --rpc-url $RPC
cast call <addr> "getAmountsOut(uint,address[])" 1e18 "[0xA,0xB]" --rpc-url $RPC

cast storage <addr> 0 --rpc-url $RPC          # slot 0
cast storage <addr> $(cast index address <key> 1) --rpc-url $RPC  # mapping slot

cast code <addr> --rpc-url $RPC               # runtime bytecode
cast code <addr> --rpc-url $RPC | wc -c       # bytecode size

cast balance <addr> --rpc-url $RPC
cast nonce <addr> --rpc-url $RPC
cast tx <txhash> --rpc-url $RPC
cast receipt <txhash> --rpc-url $RPC
cast block latest --rpc-url $RPC
cast block 20000000 --rpc-url $RPC
```

### Sending transactions

```bash
cast send <addr> "transfer(address,uint256)" <to> 1e18 \
  --rpc-url $RPC --private-key $PK
cast send <addr> --value 1ether --rpc-url $RPC --private-key $PK
```

### ABI encoding / decoding

```bash
# Encode calldata (WITH selector):
cast calldata "transfer(address,uint256)" 0xabc... 1000000

# Decode calldata:
cast decode-calldata "transfer(address,uint256)" 0xa9059cbb...

# Decode event log:
cast decode-event "Transfer(address,address,uint256)" \
  0x000...   # topics+data hex

# ABI encode (NO selector):
cast abi-encode "foo(uint256,address)" 42 0xabc...

# ABI decode raw output:
cast abi-decode "foo()(uint256,bool)" 0x...  # note empty input sig for return

# Compute storage slot for mapping:
cast index <key-type> <key> <slot>
cast index address 0xUser 1    # mapping(address => ...) at slot 1
cast index uint256 42 2        # mapping(uint256 => ...) at slot 2
```

### Selectors and signatures

```bash
cast sig "transfer(address,uint256)"          # → 0xa9059cbb
cast 4byte 0xa9059cbb                         # → "transfer(address,uint256)"
cast selectors <bytecode>                     # extract all selectors from bytecode
cast 4byte-decode <calldata>                  # decode calldata using 4byte db
cast sig-event "Transfer(address,address,uint256)"  # event topic hash
```

### Trace and replay

```bash
cast run <txhash> --rpc-url $RPC              # replay with opcode trace
cast run <txhash> --rpc-url $RPC --debug      # interactive debugger
cast run <txhash> --rpc-url $RPC --label <addr>:<name>  # label addresses
cast access-list <addr> "func()" args --rpc-url $RPC    # generate EIP-2930 access list
```

### Unit conversion

```bash
cast to-wei 1.5 ether        # → 1500000000000000000
cast from-wei 1500000000000000000 ether  # → 1.5
cast to-unit 1500000000 gwei # convert between units
cast to-hex 255              # → 0xff
cast to-dec 0xff             # → 255
cast to-bytes32 0x1234       # left-pad to 32 bytes
cast keccak "hello"          # keccak256 hash
cast hash-message "hello"    # EIP-191 personal_sign hash
cast from-rlp <hex>          # decode RLP
```

### Wallet

```bash
cast wallet new             # generate new keypair
cast wallet address --private-key $PK
cast wallet sign --private-key $PK "message"
cast wallet verify --address <addr> "message" <sig>
```

---

## anvil (local node)

```bash
anvil                                       # start with 10 pre-funded accounts
anvil --fork-url $RPC                       # fork mainnet at latest block
anvil --fork-url $RPC --fork-block-number 20000000
anvil --chain-id 1337
anvil --block-time 2                        # auto-mine every 2 seconds
anvil --no-mining                           # manual mine only
anvil --port 8546
anvil --accounts 20 --balance 10000         # 20 accounts each with 10000 ETH
```

**Custom RPC methods (via cast or curl):**

```bash
# Impersonate any account (no private key needed)
cast rpc anvil_impersonateAccount <addr>
cast send --from <addr> --unlocked <target> "func()" --rpc-url localhost:8545

# Set balance
cast rpc anvil_setBalance <addr> <wei-hex>

# Set storage
cast rpc anvil_setStorageAt <addr> <slot-hex> <value-hex>

# Set code
cast rpc anvil_setCode <addr> <bytecode-hex>

# Mine a block
cast rpc anvil_mine 5          # mine 5 blocks

# Snapshot / revert
cast rpc evm_snapshot
cast rpc evm_revert <snapshot-id>

# Set next block timestamp
cast rpc evm_setNextBlockTimestamp <unix-timestamp>
```

---

## chisel (Solidity REPL)

```bash
chisel                       # start interactive REPL
chisel --fork-url $RPC       # start with mainnet fork

# Inside chisel:
# Type Solidity expressions directly:
> uint256 x = 2 ** 256 - 1
> keccak256(abi.encode(x))
> !source                    # show all session code
> !clear                     # clear session
> !fork <rpc-url>            # fork a network mid-session
```
