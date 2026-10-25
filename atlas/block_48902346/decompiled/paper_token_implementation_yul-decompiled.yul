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
            * @custom:signature    Unresolved_06fdde03() public view returns (string memory)
            */
            case 0x06fdde03 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        if iszero(and(sload(0x01), 0x01)) {
                            if eq(lt(shr(0x01, sload(0x01)), 0x20), and(sload(0x01), 0x01)) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x22)
                                mstore(0x80, shr(0x01, sload(0x01)))
                                if eq(0, and(sload(0x01), 0x01)) {
                                    if eq(0x01, and(sload(0x01), 0x01)) {
                                        mstore(0, 0x01)
                                        if lt(0, shr(0x01, sload(0x01))) {
                                            if or(lt(0xa0, 0x80), gt(0xa0, 0xffffffffffffffff)) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                mstore(0x40, 0xa0)
                                                mstore(0xa0, 0x20)
                                                mstore(0xc0, mload(0x80))
                                                if lt(0, mload(0x80)) {
                                                    mstore(0xe0, 0)
                                                    return(mload(0x40), sub(add(add(and(add(mload(0x80), 0x1f), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0), mload(0x40)), 0x40), mload(0x40)))
                                                    if or(lt(0, 0x80), gt(0, 0xffffffffffffffff)) {
                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x04, 0x41)
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
            * @custom:signature    Unresolved_12bbf044() public view returns (address)
            */
            case 0x12bbf044 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x05), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_9dd373b9(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x9dd373b9 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x03))) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x09, or(and(sload(0x09), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)))
                                log2(0, 0, 0x6397f5b135542bb3f477cb346cfab5abdec1251d08dc8f8d4efb4ffe122ea0bf, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_07546172() public view returns (address)
            */
            case 0x07546172 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_a9059cbb(address arg0, uint256 arg1) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            */
            case 0xa9059cbb {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if iszero(iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x09)))) {
                                if eq(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x09)), caller()) {
                                    if iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x09)), caller())) { revert(mload(0x40), 0x04); } else {
                                        mstore(0x80, 0xe827105e00000000000000000000000000000000000000000000000000000000)
                                        mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, caller()))
                                        mstore(0x20, 0x07)
                                        if lt(sload(sha3(0, 0x40)), calldataload(0x24)) { revert(mload(0x40), 0x04); } else {
                                            mstore(0x80, 0xf4d678b800000000000000000000000000000000000000000000000000000000)
                                            codecopy(0, 0x0d73, 0x20)
                                            mstore(0, mload(0))
                                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, caller()))
                                            mstore(0x20, 0x07)
                                            if gt(sub(sload(sha3(0, 0x40)), calldataload(0x24)), sload(sha3(0, 0x40))) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x11)
                                                sstore(sha3(0, 0x40), sub(sload(sha3(0, 0x40)), calldataload(0x24)))
                                                mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                mstore(0x20, 0x07)
                                                if gt(sload(sha3(0, 0x40)), add(sload(sha3(0, 0x40)), calldataload(0x24))) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x11)
                                                    sstore(sha3(0, 0x40), add(sload(sha3(0, 0x40)), calldataload(0x24)))
                                                    mstore(0x80, calldataload(0x24))
                                                    log3(mload(0x40), 0x20, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, caller()), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                    mstore(0x80, 0x01)
                                                    return(mload(0x40), 0x20)
                                                    if iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x09)), and(0xffffffffffffffffffffffffffffffffffffffff, caller()))) {
                                                    }
                                                    if iszero(iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x09)))) {
                                                        if iszero(iszero(iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x09))))) { revert(0, 0); } else {
                                                            mstore(0x80, 0xe827105e00000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_d311b1a9(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xd311b1a9 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x03))) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x05, or(and(sload(0x05), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)))
                                log2(0, 0, 0x6e54fcdf080b1c188bfc8f26eb9386e78b6cb5428459a86cdd74357de82a33ae, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_ee99205c() public view returns (address)
            */
            case 0xee99205c {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x09), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_23b872dd(address arg0, address arg1, uint256 arg2) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            */
            case 0x23b872dd {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(caller(), and(sload(0x05), 0xffffffffffffffffffffffffffffffffffffffff)) {
                                    mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                    mstore(0x20, 0x08)
                                    mstore(0, caller())
                                    mstore(0x20, sha3(0, 0x40))
                                    if lt(sload(sha3(0, 0x40)), calldataload(0x44)) { revert(mload(0x40), 0x04); } else {
                                        mstore(0x80, 0x13be252b00000000000000000000000000000000000000000000000000000000)
                                        if gt(sub(sload(sha3(0, 0x40)), calldataload(0x44)), sload(sha3(0, 0x40))) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x11)
                                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                            mstore(0x20, 0x08)
                                            mstore(0, caller())
                                            mstore(0x20, sha3(0, 0x40))
                                            sstore(sha3(0, 0x40), sub(sload(sha3(0, 0x40)), calldataload(0x44)))
                                            if iszero(iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x09)))) {
                                                if eq(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x09)), caller()) {
                                                    if iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x09)), caller())) { revert(mload(0x40), 0x04); } else {
                                                        mstore(0x80, 0xe827105e00000000000000000000000000000000000000000000000000000000)
                                                        mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                        mstore(0x20, 0x07)
                                                        if lt(sload(sha3(0, 0x40)), calldataload(0x44)) { revert(mload(0x40), 0x04); } else {
                                                            mstore(0x80, 0xf4d678b800000000000000000000000000000000000000000000000000000000)
                                                            codecopy(0, 0x0d73, 0x20)
                                                            mstore(0, mload(0))
                                                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                            mstore(0x20, 0x07)
                                                            if gt(sub(sload(sha3(0, 0x40)), calldataload(0x44)), sload(sha3(0, 0x40))) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x11)
                                                                sstore(sha3(0, 0x40), sub(sload(sha3(0, 0x40)), calldataload(0x44)))
                                                                mstore(0, and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                mstore(0x20, 0x07)
                                                                if gt(sload(sha3(0, 0x40)), add(sload(sha3(0, 0x40)), calldataload(0x44))) {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x11)
                                                                    sstore(sha3(0, 0x40), add(sload(sha3(0, 0x40)), calldataload(0x44)))
                                                                    mstore(0x80, calldataload(0x44))
                                                                    log3(mload(0x40), 0x20, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                    mstore(0x80, 0x01)
                                                                    return(mload(0x40), 0x20)
                                                                    if iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x09)), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))) {
                                                                    }
                                                                    if iszero(iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x09)))) {
                                                                        if iszero(iszero(iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x09))))) { revert(0, 0); } else {
                                                                            mstore(0x80, 0xe827105e00000000000000000000000000000000000000000000000000000000)
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
                }
            }
            
            /*
            * @custom:signature    Unresolved_8da5cb5b() public view returns (address)
            */
            case 0x8da5cb5b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x03), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_70a08231(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x70a08231 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x07)
                            mstore(0x80, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_18160ddd() public view returns (uint256)
            */
            case 0x18160ddd {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x06))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_313ce567() public pure returns (uint256)
            */
            case 0x313ce567 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, 0x12)
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_95d89b41() public view returns (string memory)
            */
            case 0x95d89b41 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        if iszero(and(sload(0x02), 0x01)) {
                            if eq(lt(shr(0x01, sload(0x02)), 0x20), and(sload(0x02), 0x01)) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x22)
                                mstore(0x80, shr(0x01, sload(0x02)))
                                if iszero(and(sload(0x02), 0x01)) {
                                    if eq(0x01, and(sload(0x02), 0x01)) {
                                        mstore(0, 0x02)
                                        if lt(0, shr(0x01, sload(0x02))) {
                                            if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(add(mload(0x40), 0), 0x20), mload(0x40)), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(add(mload(0x40), 0), 0x20), mload(0x40)), 0x1f))), 0xffffffffffffffff)) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(add(mload(0x40), 0), 0x20), mload(0x40)), 0x1f))))
                                                mstore(0xa0, 0x20)
                                                mstore(0xc0, mload(mload(0x40)))
                                                if lt(0, mload(mload(0x40))) {
                                                    mstore(0xe0, 0)
                                                    return(mload(0x40), sub(add(add(and(add(mload(mload(0x40)), 0x1f), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0), mload(0x40)), 0x40), mload(0x40)))
                                                    if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(0, mload(0x40)), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(0, mload(0x40)), 0x1f))), 0xffffffffffffffff)) {
                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x04, 0x41)
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
            * @custom:signature    Unresolved_40c10f19(address arg0, uint256 arg1) public view
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            */
            case 0x40c10f19 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x04))) { revert(mload(0x40), 0x04); } else {
                                mstore(0x80, 0xf8d2906c00000000000000000000000000000000000000000000000000000000)
                                codecopy(0, 0x0d73, 0x20)
                                mstore(0, mload(0))
                                if gt(sload(0x06), add(sload(0x06), calldataload(0x24))) { revert(0, 0); } else {
                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                    mstore(0x04, 0x11)
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_dd62ed3e(address arg0, address arg1) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xdd62ed3e {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if eq(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x05))) { revert(0, 0); } else {
                                    mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                    mstore(0x20, 0x08)
                                    mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))
                                    mstore(0x20, sha3(0, 0x40))
                                    mstore(0x80, sload(sha3(0, 0x40)))
                                    return(mload(0x40), 0x20)
                                    mstore(0x80, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
                                    return(mload(0x40), 0x20)
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_8f15b414(uint256 arg0, uint256 arg1, address arg2, address arg3) public payable
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["address", "uint160", "bytes20", "int160"]
            * @param                arg3 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x8f15b414 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x80) {
                        if gt(calldataload(0x04), 0xffffffffffffffff) { revert(0, 0); } else {
                            if iszero(slt(add(add(0x04, calldataload(0x04)), 0x1f), calldatasize())) {
                                if gt(calldataload(add(0x04, calldataload(0x04))), 0xffffffffffffffff) {
                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                    mstore(0x04, 0x41)
                                    if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(calldataload(add(0x04, calldataload(0x04))), 0x1f))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(calldataload(add(0x04, calldataload(0x04))), 0x1f))), 0x1f))), 0xffffffffffffffff)) {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x41)
                                        mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(calldataload(add(0x04, calldataload(0x04))), 0x1f))), 0x1f))))
                                        mstore(0x80, calldataload(add(0x04, calldataload(0x04))))
                                        if gt(add(add(add(0x04, calldataload(0x04)), calldataload(add(0x04, calldataload(0x04)))), 0x20), calldatasize()) {
                                            calldatacopy(add(mload(0x40), 0x20), add(add(0x04, calldataload(0x04)), 0x20), calldataload(add(0x04, calldataload(0x04))))
                                            mstore(0xa0, 0)
                                            if gt(calldataload(0x24), 0xffffffffffffffff) { revert(0, 0); } else {
                                                if iszero(slt(add(add(0x04, calldataload(0x24)), 0x1f), calldatasize())) {
                                                    if gt(calldataload(add(0x04, calldataload(0x24))), 0xffffffffffffffff) {
                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x04, 0x41)
                                                        if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(calldataload(add(0x04, calldataload(0x24))), 0x1f))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(calldataload(add(0x04, calldataload(0x24))), 0x1f))), 0x1f))), 0xffffffffffffffff)) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(calldataload(add(0x04, calldataload(0x24))), 0x1f))), 0x1f))))
                                                            mstore(0xa0, calldataload(add(0x04, calldataload(0x24))))
                                                            if gt(add(add(add(0x04, calldataload(0x24)), calldataload(add(0x04, calldataload(0x24)))), 0x20), calldatasize()) {
                                                                calldatacopy(add(mload(0x40), 0x20), add(add(0x04, calldataload(0x24)), 0x20), calldataload(add(0x04, calldataload(0x24))))
                                                                mstore(0xc0, 0)
                                                                if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                    if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                        if and(sload(0), 0xff) {
                                                                            if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                                                                if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                                                                    if gt(mload(mload(0x40)), 0xffffffffffffffff) {
                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                        mstore(0x04, 0x41)
                                                                                        if iszero(and(sload(0x01), 0x01)) {
                                                                                            if eq(lt(shr(0x01, sload(0x01)), 0x20), and(sload(0x01), 0x01)) {
                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                mstore(0x04, 0x22)
                                                                                                if gt(shr(0x01, sload(0x01)), 0x1f) {
                                                                                                    mstore(0, 0x01)
                                                                                                    if lt(mload(mload(0x40)), 0x20) {
                                                                                                        if lt(add(sha3(0, 0x20), shr(0x05, add(mload(mload(0x40)), 0x1f))), add(shr(0x05, add(shr(0x01, sload(0x01)), 0x1f)), sha3(0, 0x20))) {
                                                                                                            if eq(0x01, gt(mload(mload(0x40)), 0x1f)) {
                                                                                                                mstore(0, 0x01)
                                                                                                                if lt(0, and(mload(mload(0x40)), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)) {
                                                                                                                    if gt(mload(mload(0x40)), and(mload(mload(0x40)), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)) {
                                                                                                                        sstore(sha3(0, 0x20), and(not(shr(and(shl(0x03, mload(mload(0x40))), 0xf8), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)), mload(add(mload(0x40), 0x20))))
                                                                                                                        sstore(0x01, add(shl(0x01, mload(mload(0x40))), 0x01))
                                                                                                                        if gt(mload(mload(0x40)), 0xffffffffffffffff) {
                                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0x04, 0x41)
                                                                                                                            if mload(mload(0x40)) { revert(mload(0x40), 0x04); } else {
                                                                                                                            }
                                                                                                                            mstore(0xc0, 0x0dc149f000000000000000000000000000000000000000000000000000000000)
                                                                                                                            if and(sload(0), 0xff) { revert(0, 0); } else {
                                                                                                                                mstore(0xc0, 0x0dc149f000000000000000000000000000000000000000000000000000000000)
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
            }
            
            /*
            * @custom:signature    Unresolved_095ea7b3(address arg0, uint256 arg1) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            */
            case 0x095ea7b3 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, caller())
                            mstore(0x20, 0x08)
                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                            mstore(0x20, sha3(0, 0x40))
                            sstore(sha3(0, 0x40), calldataload(0x24))
                            mstore(0x80, calldataload(0x24))
                            log3(mload(0x40), 0x20, 0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925, caller(), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                            mstore(0x80, 0x01)
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_9dc29fac(address arg0, uint256 arg1) public view
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            */
            case 0x9dc29fac {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x04))) { revert(mload(0x40), 0x04); } else {
                                mstore(0x80, 0xf8d2906c00000000000000000000000000000000000000000000000000000000)
                                mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                mstore(0x20, 0x07)
                                if lt(sload(sha3(0, 0x40)), calldataload(0x24)) { revert(mload(0x40), 0x04); } else {
                                    mstore(0x80, 0xf4d678b800000000000000000000000000000000000000000000000000000000)
                                    codecopy(0, 0x0d73, 0x20)
                                    mstore(0, mload(0))
                                    mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                    mstore(0x20, 0x07)
                                    if gt(sub(sload(sha3(0, 0x40)), calldataload(0x24)), sload(sha3(0, 0x40))) { revert(0, 0); } else {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x11)
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_f2fde38b(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xf2fde38b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(sload(0x03), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x03, or(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x03))))
                                codecopy(0, 0x0d53, 0x20)
                                mstore(0, mload(0))
                                log2(0, 0, mload(0), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_fca3b5aa(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xfca3b5aa {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x03))) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x04, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x04))))
                                codecopy(0, 0x0d33, 0x20)
                                mstore(0, mload(0))
                                log2(0, 0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                            }
                        }
                    }
                }
            }
            default { revert(0, 0) }
        }
    }
}