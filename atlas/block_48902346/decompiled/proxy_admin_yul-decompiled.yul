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
            * @custom:signature    Unresolved_7eff275e(address arg0, address arg1) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x7eff275e {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0))) { revert(0x80, 0x04); } else {
                                    mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                    if iszero(extcodesize(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))) { revert(0, 0); } else {
                                        mstore(0x80, 0x8f28397000000000000000000000000000000000000000000000000000000000)
                                        mstore(0x84, and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
                                        call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), 0, mload(0x40), 0x24, mload(0x40), 0)
                                        if iszero(call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), 0, mload(0x40), 0x24, mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                            returndatacopy(mload(0x40), 0, returndatasize())
                                            if call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), 0, mload(0x40), 0x24, mload(0x40), 0) {
                                                return(0, 0)
                                                if gt(mload(0x40), 0xffffffffffffffff) { revert(0, 0); } else {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x41)
                                                    mstore(0x40, mload(0x40))
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
            
            /*
            * @custom:signature    Unresolved_9623609d(address arg0, address arg1, uint256 arg2) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            */
            case 0x9623609d {
                if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                    if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                        if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if gt(calldataload(0x44), 0xffffffffffffffff) { revert(0, 0); } else {
                                if iszero(slt(add(calldataload(0x44), 0x23), calldatasize())) {
                                    if gt(calldataload(add(0x04, calldataload(0x44))), 0xffffffffffffffff) { revert(0, 0); } else {
                                        if gt(add(add(calldataload(0x44), calldataload(add(0x04, calldataload(0x44)))), 0x24), calldatasize()) {
                                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0))) { revert(mload(0x40), 0x04); } else {
                                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                                if iszero(extcodesize(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0); } else {
                                                    mstore(0x80, 0x4f1ef28600000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x84, and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
                                                    mstore(0xa4, 0x40)
                                                    mstore(0xc4, calldataload(add(0x04, calldataload(0x44))))
                                                    calldatacopy(add(mload(0x40), 0x64), add(calldataload(0x44), 0x24), calldataload(add(0x04, calldataload(0x44))))
                                                    mstore(0xe4, 0)
                                                    call(gas(), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), callvalue(), mload(0x40), add(sub(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), mload(0x40)), 0x64), mload(0x40), 0)
                                                    if iszero(call(gas(), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), callvalue(), mload(0x40), add(sub(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), mload(0x40)), 0x64), mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                        returndatacopy(mload(0x40), 0, returndatasize())
                                                        if call(gas(), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), callvalue(), mload(0x40), add(sub(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), mload(0x40)), 0x64), mload(0x40), 0) {
                                                            return(0, 0)
                                                            if gt(mload(0x40), 0xffffffffffffffff) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                mstore(0x40, mload(0x40))
                                                                if 0 { revert(0, 0); } else {
                                                                    return(0, 0)
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
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_8da5cb5b() public view returns (address)
            */
            case 0x8da5cb5b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_f2fde38b(address arg0) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xf2fde38b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(sload(0), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(mload(0x40), 0x04); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                if iszero(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                    sstore(0, or(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0))))
                                    log2(0, 0, 0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                    return(0, 0)
                                    mstore(0x80, 0x49e27cff00000000000000000000000000000000000000000000000000000000)
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_99a88ec4(address arg0, address arg1) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x99a88ec4 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0))) { revert(mload(0x40), 0x04); } else {
                                    mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                    if iszero(extcodesize(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0); } else {
                                        mstore(0x80, 0x4f1ef28600000000000000000000000000000000000000000000000000000000)
                                        mstore(0x84, and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
                                        mstore(0xa4, 0x40)
                                        mstore(0xc4, 0)
                                        call(gas(), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), 0x64, mload(0x40), 0)
                                        if iszero(call(gas(), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), 0x64, mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                            returndatacopy(mload(0x40), 0, returndatasize())
                                            if call(gas(), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), 0x64, mload(0x40), 0) {
                                                return(0, 0)
                                                if gt(mload(0x40), 0xffffffffffffffff) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x41)
                                                    mstore(0x40, mload(0x40))
                                                    if 0 { revert(0, 0); } else {
                                                        return(0, 0)
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
            }
            default { revert(0, 0) }
        }
    }
}