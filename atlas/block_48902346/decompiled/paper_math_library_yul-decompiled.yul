/// @title            Decompiled Contract
/// @author           Jonathan Becker <jonathan@jbecker.dev>
/// @custom:version   heimdall-rs v0.9.2
///
/// @notice           This contract was decompiled using the heimdall-rs decompiler.
///                     It was generated directly by tracing the EVM opcodes from this contract.
///                     As a result, it may not compile or even be valid yul code.
///                     Despite this, it should be obvious what each function does. Overall
///                     logic should have been preserved throughout decompiling.
///
/// @custom:github    You can find the open-source decompiler here:
///                       https://heimdall.rs

object "DecompiledContract" {
    object "runtime" {
        code {
            
            function selector() -> s {
                s := div(calldataload(0), 0x100000000000000000000000000000000000000000000000000000000)
            }
            
            function castToAddress(x) -> a {
                a := and(x, 0xffffffffffffffffffffffffffffffffffffffff)
            }
            
            switch selector()
            
            /*
            * @custom:signature    Unresolved_7aac24ba(uint256 arg0, uint256 arg1, uint256 arg2, uint256 arg3, uint256 arg4, uint256 arg5) public pure returns (bytes memory)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            * @param                arg5 ["uint256", "bytes32", "int256"]
            */
            case 0x7aac24ba {
                if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xc0) {
                    if iszero(calldataload(0x44)) {
                        if or(and(iszero(slt(calldataload(0x04), 0)), slt(add(calldataload(0x04), calldataload(0x44)), calldataload(0x44))), and(slt(calldataload(0x04), 0), iszero(slt(add(calldataload(0x04), calldataload(0x44)), calldataload(0x44))))) {
                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                            mstore(0x04, 0x11)
                            if slt(calldataload(0x04), calldataload(0x64)) {
                                if iszero(slt(add(calldataload(0x04), calldataload(0x44)), calldataload(0x64))) {
                                    if or(and(slt(sub(add(calldataload(0x04), calldataload(0x44)), calldataload(0x04)), add(calldataload(0x04), calldataload(0x44))), sgt(0, calldataload(0x04))), and(sgt(sub(add(calldataload(0x04), calldataload(0x44)), calldataload(0x04)), add(calldataload(0x04), calldataload(0x44))), iszero(sgt(0, calldataload(0x04))))) {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x11)
                                        if iszero(or(eq(div(mul(sub(add(calldataload(0x04), calldataload(0x44)), calldataload(0x04)), calldataload(0x84)), sub(add(calldataload(0x04), calldataload(0x44)), calldataload(0x04))), calldataload(0x84)), iszero(sub(add(calldataload(0x04), calldataload(0x44)), calldataload(0x04))))) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x11)
                                            if gt(0, add(0, div(mul(sub(add(calldataload(0x04), calldataload(0x44)), calldataload(0x04)), calldataload(0x84)), 0x0de0b6b3a7640000))) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x11)
                                                if sgt(add(calldataload(0x04), calldataload(0x44)), calldataload(0x64)) {
                                                    if eq(0, sgt(calldataload(0x04), calldataload(0x64))) { revert(0, 0); } else {
                                                    }
                                                    mstore(0x80, add(0, div(mul(sub(add(calldataload(0x04), calldataload(0x44)), calldataload(0x04)), calldataload(0x84)), 0x0de0b6b3a7640000)))
                                                    mstore(0xa0, 0)
                                                    return(mload(0x40), 0x40)
                                                    mstore(0x80, 0)
                                                    mstore(0xa0, 0)
                                                    return(mload(0x40), 0x40)
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            default { revert(0, 0) }
        }
    }
}