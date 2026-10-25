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
            * @custom:signature    Unresolved_c63c4e9b() public view returns (uint256)
            */
            case 0xc63c4e9b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x01))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_2ab0f529(uint256 arg0) public view returns (uint256)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x2ab0f529 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) { revert(0, 0); } else {
                        mstore(0, calldataload(0x04))
                        mstore(0x20, 0x02)
                        mstore(0x80, eq(sload(sha3(0, 0x40)), 0x01))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_6cb6a1f7(uint256 arg0) public view returns (uint256)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x6cb6a1f7 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) { revert(0, 0); } else {
                        mstore(0, calldataload(0x04))
                        mstore(0x20, 0x02)
                        mstore(0x80, sload(sha3(0, 0x40)))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_88aa4c12(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            */
            case 0x88aa4c12 {
                if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x80) {
                    if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                        if gt(calldataload(0x44), 0xffffffffffffffff) { revert(0, 0); } else {
                            if iszero(slt(add(calldataload(0x44), 0x23), calldatasize())) {
                                if gt(calldataload(add(0x04, calldataload(0x44))), 0xffffffffffffffff) { revert(0, 0); } else {
                                    if gt(add(add(calldataload(0x44), calldataload(add(0x04, calldataload(0x44)))), 0x24), calldatasize()) {
                                        if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0))) { revert(mload(0x40), 0x04); } else {
                                            mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                            if gt(calldataload(add(0x04, calldataload(0x44))), 0xffffffffffffffff) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))), 0xffffffffffffffff)) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x41)
                                                    mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))))
                                                    mstore(0x80, calldataload(add(0x04, calldataload(0x44))))
                                                    if gt(add(add(0x24, calldataload(0x44)), calldataload(add(0x04, calldataload(0x44)))), calldatasize()) {
                                                        calldatacopy(add(mload(0x40), 0x20), add(0x24, calldataload(0x44)), calldataload(add(0x04, calldataload(0x44))))
                                                        mstore(0xa0, 0)
                                                        mstore(0xc0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                        mstore(0xe0, calldataload(0x24))
                                                        mstore(0x0100, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                        mstore(0x0120, calldataload(0x64))
                                                        mstore(0xa0, 0x80)
                                                        if or(gt(add(mload(0x40), 0xa0), 0xffffffffffffffff), lt(add(mload(0x40), 0xa0), mload(0x40))) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            mstore(0x40, add(mload(0x40), 0xa0))
                                                            mstore(0, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                            mstore(0x20, 0x02)
                                                            if iszero(sload(sha3(0, 0x40))) {
                                                                if eq(sload(sha3(0, 0x40)), 0x01) { revert(mload(0x40), 0x04); } else {
                                                                    mstore(0x0140, 0x18d96a8000000000000000000000000000000000000000000000000000000000)
                                                                    if lt(timestamp(), sload(sha3(0, 0x40))) { revert(mload(0x40), 0x04); } else {
                                                                        mstore(0x0140, 0xf800799b00000000000000000000000000000000000000000000000000000000)
                                                                        if sub(callvalue(), calldataload(0x24)) { revert(mload(0x40), 0x04); } else {
                                                                            mstore(0x0140, 0xaa7feadc00000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                            mstore(0x20, 0x02)
                                                                            sstore(sha3(0, 0x40), 0x01)
                                                                            calldatacopy(mload(0x40), add(0x24, calldataload(0x44)), calldataload(add(0x04, calldataload(0x44))))
                                                                            mstore(0x0140, 0)
                                                                            call(gas(), calldataload(0x04), calldataload(0x24), mload(0x40), sub(add(mload(0x40), calldataload(add(0x04, calldataload(0x44)))), mload(0x40)), 0, 0)
                                                                            if iszero(returndatasize()) {
                                                                                if iszero(call(gas(), calldataload(0x04), calldataload(0x24), mload(0x40), sub(add(mload(0x40), calldataload(add(0x04, calldataload(0x44)))), mload(0x40)), 0, 0)) {
                                                                                    mstore(0x0140, 0x15fcd67500000000000000000000000000000000000000000000000000000000)
                                                                                    mstore(0x0144, 0x20)
                                                                                    mstore(0x0164, mload(0x60))
                                                                                    if lt(0, mload(0x60)) { revert(0, 0); } else {
                                                                                        mstore(0x0184, 0)
                                                                                        mstore(0x0140, 0x27c0d61000000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_584b153e(uint256 arg0) public view returns (bool)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x584b153e {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        mstore(0, calldataload(0x04))
                        mstore(0x20, 0x02)
                        if gt(sload(sha3(0, 0x40)), 0x01) { revert(0, 0); } else {
                            mstore(0x80, iszero(iszero(lt(timestamp(), sload(sha3(0, 0x40))))))
                            return(mload(0x40), 0x20)
                            mstore(0x80, iszero(iszero(gt(sload(sha3(0, 0x40)), 0x01))))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_13bc9f20(uint256 arg0) public view returns (bool)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x13bc9f20 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        mstore(0, calldataload(0x04))
                        mstore(0x20, 0x02)
                        if gt(sload(sha3(0, 0x40)), 0x01) { revert(0, 0); } else {
                            mstore(0x80, iszero(iszero(iszero(lt(timestamp(), sload(sha3(0, 0x40)))))))
                            return(mload(0x40), 0x20)
                            mstore(0x80, iszero(iszero(gt(sload(sha3(0, 0x40)), 0x01))))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_8a99d586(uint256 arg0) public payable
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x8a99d586 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(caller(), address()) { revert(0, 0); } else {
                            mstore(0x80, 0x29c3b7ee00000000000000000000000000000000000000000000000000000000)
                            sstore(0x01, calldataload(0x04))
                            mstore(0x80, calldataload(0x04))
                            log1(mload(0x40), 0x20, 0x25cd0ae91e995bc58ea33869249d0bcf40f2b2c8331ec976c96096bf7d27f464)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_a6cc2c8c(uint256 arg0, uint256 arg1, uint256 arg2) public pure
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            */
            case 0xa6cc2c8c {
                if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x80) {
                    if gt(calldataload(0x04), 0xffffffffffffffff) { revert(0, 0); } else {
                        if iszero(slt(add(add(0x04, calldataload(0x04)), 0x1f), calldatasize())) {
                            if gt(calldataload(add(0x04, calldataload(0x04))), 0xffffffffffffffff) { revert(0, 0); } else {
                                if gt(add(add(shl(0x05, calldataload(add(0x04, calldataload(0x04)))), add(0x04, calldataload(0x04))), 0x20), calldatasize()) {
                                    if gt(calldataload(0x24), 0xffffffffffffffff) { revert(0, 0); } else {
                                        if iszero(slt(add(add(0x04, calldataload(0x24)), 0x1f), calldatasize())) {
                                            if gt(calldataload(add(0x04, calldataload(0x24))), 0xffffffffffffffff) { revert(0, 0); } else {
                                                if gt(add(add(shl(0x05, calldataload(add(0x04, calldataload(0x24)))), add(0x04, calldataload(0x24))), 0x20), calldatasize()) {
                                                    if gt(calldataload(0x44), 0xffffffffffffffff) { revert(0, 0); } else {
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
                        mstore(0x80, and(sload(0), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_c4d252f5(uint256 arg0) public payable
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0xc4d252f5 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0))) { revert(mload(0x40), 0x04); } else {
                            mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                            mstore(0, calldataload(0x04))
                            mstore(0x20, 0x02)
                            if iszero(sload(sha3(0, 0x40))) {
                                if eq(0x01, sload(sha3(0, 0x40))) { revert(0, 0); } else {
                                    mstore(0x80, 0x18d96a8000000000000000000000000000000000000000000000000000000000)
                                    mstore(0, calldataload(0x04))
                                    mstore(0x20, 0x02)
                                    sstore(sha3(0, 0x40), 0)
                                    log2(0, 0, 0xcf0f63b97f3387253cbc0bde884f975df77e39184dc3280c2c81be495f58eef4, calldataload(0x04))
                                    mstore(0x80, 0x27c0d61000000000000000000000000000000000000000000000000000000000)
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_8b07f62b(uint256 arg0, uint256 arg1, uint256 arg2) public pure
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            */
            case 0x8b07f62b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x80) {
                        if gt(calldataload(0x04), 0xffffffffffffffff) { revert(0, 0); } else {
                            if iszero(slt(add(add(0x04, calldataload(0x04)), 0x1f), calldatasize())) {
                                if gt(calldataload(add(0x04, calldataload(0x04))), 0xffffffffffffffff) { revert(0, 0); } else {
                                    if gt(add(add(shl(0x05, calldataload(add(0x04, calldataload(0x04)))), add(0x04, calldataload(0x04))), 0x20), calldatasize()) {
                                        if gt(calldataload(0x24), 0xffffffffffffffff) { revert(0, 0); } else {
                                            if iszero(slt(add(add(0x04, calldataload(0x24)), 0x1f), calldatasize())) {
                                                if gt(calldataload(add(0x04, calldataload(0x24))), 0xffffffffffffffff) { revert(0, 0); } else {
                                                    if gt(add(add(shl(0x05, calldataload(add(0x04, calldataload(0x24)))), add(0x04, calldataload(0x24))), 0x20), calldatasize()) {
                                                        if gt(calldataload(0x44), 0xffffffffffffffff) { revert(0, 0); } else {
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
            * @custom:signature    Unresolved_ec2a5b45(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public pure returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            */
            case 0xec2a5b45 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x80) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if gt(calldataload(0x44), 0xffffffffffffffff) { revert(0, 0); } else {
                                if iszero(slt(add(calldataload(0x44), 0x23), calldatasize())) {
                                    if gt(calldataload(add(0x04, calldataload(0x44))), 0xffffffffffffffff) { revert(0, 0); } else {
                                        if gt(add(add(calldataload(0x44), calldataload(add(0x04, calldataload(0x44)))), 0x24), calldatasize()) {
                                            if gt(calldataload(add(0x04, calldataload(0x44))), 0xffffffffffffffff) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))), 0xffffffffffffffff)) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x41)
                                                    mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))))
                                                    mstore(0x80, calldataload(add(0x04, calldataload(0x44))))
                                                    if gt(add(add(0x24, calldataload(0x44)), calldataload(add(0x04, calldataload(0x44)))), calldatasize()) {
                                                        calldatacopy(add(mload(0x40), 0x20), add(0x24, calldataload(0x44)), calldataload(add(0x04, calldataload(0x44))))
                                                        mstore(0xa0, 0)
                                                        mstore(0xc0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                        mstore(0xe0, calldataload(0x24))
                                                        mstore(0x0100, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                        mstore(0x0120, calldataload(0x64))
                                                        mstore(0xa0, 0x80)
                                                        if or(gt(add(mload(0x40), 0xa0), 0xffffffffffffffff), lt(add(mload(0x40), 0xa0), mload(0x40))) { revert(0, 0); } else {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            mstore(0x40, add(mload(0x40), 0xa0))
                                                            mstore(0x0140, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                            return(mload(0x40), 0x20)
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
            * @custom:signature    Unresolved_04d2cd0e(uint256 arg0, uint256 arg1, uint256 arg2) public pure
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            */
            case 0x04d2cd0e {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x80) {
                        if gt(calldataload(0x04), 0xffffffffffffffff) { revert(0, 0); } else {
                            if iszero(slt(add(add(0x04, calldataload(0x04)), 0x1f), calldatasize())) {
                                if gt(calldataload(add(0x04, calldataload(0x04))), 0xffffffffffffffff) { revert(0, 0); } else {
                                    if gt(add(add(shl(0x05, calldataload(add(0x04, calldataload(0x04)))), add(0x04, calldataload(0x04))), 0x20), calldatasize()) {
                                        if gt(calldataload(0x24), 0xffffffffffffffff) { revert(0, 0); } else {
                                            if iszero(slt(add(add(0x04, calldataload(0x24)), 0x1f), calldatasize())) {
                                                if gt(calldataload(add(0x04, calldataload(0x24))), 0xffffffffffffffff) { revert(0, 0); } else {
                                                    if gt(add(add(shl(0x05, calldataload(add(0x04, calldataload(0x24)))), add(0x04, calldataload(0x24))), 0x20), calldatasize()) {
                                                        if gt(calldataload(0x44), 0xffffffffffffffff) { revert(0, 0); } else {
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
            * @custom:signature    Unresolved_b0e58bc9(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            */
            case 0xb0e58bc9 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x80) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if gt(calldataload(0x44), 0xffffffffffffffff) { revert(0, 0); } else {
                                if iszero(slt(add(calldataload(0x44), 0x23), calldatasize())) {
                                    if gt(calldataload(add(0x04, calldataload(0x44))), 0xffffffffffffffff) { revert(0, 0); } else {
                                        if gt(add(add(calldataload(0x44), calldataload(add(0x04, calldataload(0x44)))), 0x24), calldatasize()) {
                                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0))) { revert(mload(0x40), 0x04); } else {
                                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                                if gt(calldataload(add(0x04, calldataload(0x44))), 0xffffffffffffffff) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x41)
                                                    if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))), 0xffffffffffffffff)) {
                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x04, 0x41)
                                                        mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))))
                                                        mstore(0x80, calldataload(add(0x04, calldataload(0x44))))
                                                        if gt(add(add(0x24, calldataload(0x44)), calldataload(add(0x04, calldataload(0x44)))), calldatasize()) {
                                                            calldatacopy(add(mload(0x40), 0x20), add(0x24, calldataload(0x44)), calldataload(add(0x04, calldataload(0x44))))
                                                            mstore(0xa0, 0)
                                                            mstore(0xc0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                            mstore(0xe0, calldataload(0x24))
                                                            mstore(0x0100, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                            mstore(0x0120, calldataload(0x64))
                                                            mstore(0xa0, 0x80)
                                                            if or(gt(add(mload(0x40), 0xa0), 0xffffffffffffffff), lt(add(mload(0x40), 0xa0), mload(0x40))) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                mstore(0x40, add(mload(0x40), 0xa0))
                                                                mstore(0, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                mstore(0x20, 0x02)
                                                                if sload(sha3(0, 0x40)) { revert(mload(0x40), 0x04); } else {
                                                                    mstore(0x0140, 0x9b38247600000000000000000000000000000000000000000000000000000000)
                                                                    if gt(timestamp(), add(timestamp(), sload(0x01))) { revert(0, 0); } else {
                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                        mstore(0x04, 0x11)
                                                                        mstore(0, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                        mstore(0x20, 0x02)
                                                                        sstore(sha3(0, 0x40), add(timestamp(), sload(0x01)))
                                                                        mstore(0, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                        mstore(0x20, 0x02)
                                                                        mstore(0x0140, calldataload(0x24))
                                                                        mstore(0x0160, 0x80)
                                                                        mstore(0x01c0, calldataload(add(0x04, calldataload(0x44))))
                                                                        calldatacopy(add(add(mload(0x40), 0x80), 0x20), add(0x24, calldataload(0x44)), calldataload(add(0x04, calldataload(0x44))))
                                                                        mstore(0x01e0, 0)
                                                                        mstore(0x0180, calldataload(0x64))
                                                                        mstore(0x01a0, sload(sha3(0, 0x40)))
                                                                        log3(mload(0x40), sub(add(add(and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44))))), add(mload(0x40), 0x80)), 0x20), mload(0x40)), 0x78f3bc93d9f0e2beb7fc8fe3192b142c5e70b8813403674aff3f81fc83af5b39, sha3(add(mload(0x40), 0x20), mload(mload(0x40))), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                        mstore(0x0140, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                        return(mload(0x40), 0x20)
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
            default { revert(0, 0) }
        }
    }
}