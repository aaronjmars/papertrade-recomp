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
            * @custom:signature    Unresolved_ca02ff91(uint256 arg0, address arg1, uint256 arg2, uint256 arg3) public payable returns (bytes memory)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            */
            case 0xca02ff91 {
                if eq(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388, address()) { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x80) {
                        if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if iszero(and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) {
                                if iszero(iszero(calldataload(0x64))) {
                                    if gt(calldataload(0x64), 0x40) {
                                        if calldataload(0x44) {
                                            if iszero(calldataload(0x44)) {
                                                mstore(0, calldataload(0x44))
                                                mstore(0x20, calldataload(0x04))
                                                if eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))) {
                                                    if iszero(eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))) {
                                                        mstore(0x80, 0)
                                                        mstore(0xa0, 0)
                                                        mstore(0xc0, 0)
                                                        return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                        if gt(calldataload(0x44), add(calldataload(0x44), 0x01)) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x11)
                                                            if lt(add(calldataload(0x44), 0x01), sload(add(calldataload(0x04), 0x02))) {
                                                                if iszero(lt(0, 0x40)) {
                                                                    if iszero(0) {
                                                                        codecopy(0, 0x1629, 0x20)
                                                                        mstore(0, mload(0))
                                                                        mstore(0x80, 0)
                                                                        mstore(0xa0, 0)
                                                                        log4(mload(0x40), 0x40, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)), calldataload(0x44), calldataload(0x44))
                                                                        mstore(0x80, 0)
                                                                        mstore(0xa0, 0)
                                                                        mstore(0xc0, calldataload(0x44))
                                                                        return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                                        mstore(0x80, 0)
                                                                        mstore(0xa0, 0)
                                                                        mstore(0xc0, 0)
                                                                        return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                                        mstore(0, add(calldataload(0x44), 0x01))
                                                                        mstore(0x20, calldataload(0x04))
                                                                        if iszero(sload(add(sha3(0, 0x40), 0x01))) {
                                                                            if sub(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))) {
                                                                                sstore(add(sha3(0, 0x40), 0x01), add(sload(add(sha3(0, 0x40), 0x01)), sload(add(sha3(0, 0x40), 0x01))))
                                                                                sstore(add(sha3(0, 0x40), 0x01), 0)
                                                                                mstore(0, add(calldataload(0x44), 0x01))
                                                                                mstore(0x20, calldataload(0x04))
                                                                                if eq(0, iszero(iszero(shr(0xd0, sload(sha3(0, 0x40)))))) {
                                                                                    mstore(0, shr(0xd0, sload(sha3(0, 0x40))))
                                                                                    mstore(0x20, calldataload(0x04))
                                                                                    sstore(sha3(0, 0x40), or(and(0xffffffffffff0000000000000000000000000000000000000000, shl(0xa0, and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff))), and(0xffffffffffff000000000000ffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                                                    if iszero(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff)) {
                                                                                    }
                                                                                    if iszero(lt(add(calldataload(0x44), 0x01), sload(add(calldataload(0x04), 0x02)))) {
                                                                                    }
                                                                                    if iszero(sload(add(sha3(0, 0x40), 0x01))) {
                                                                                        mstore(0x80, 0)
                                                                                        mstore(0xa0, 0)
                                                                                        mstore(0xc0, 0)
                                                                                        return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                                                        mstore(0x80, 0)
                                                                                        mstore(0xa0, 0)
                                                                                        mstore(0xc0, 0)
                                                                                        return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                                                        if calldataload(0x44) {
                                                                                        }
                                                                                    }
                                                                                    if iszero(calldataload(0x64)) { revert(0, 0); } else {
                                                                                    }
                                                                                    mstore(0x80, 0)
                                                                                    mstore(0xa0, 0)
                                                                                    mstore(0xc0, 0)
                                                                                    return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
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
            * @custom:signature    Unresolved_ef1a27a9(uint256 arg0, address arg1, address arg2, uint256 arg3, uint256 arg4, uint256 arg5, uint256 arg6, uint256 arg7) public view
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["address", "uint128", "bytes16", "int128"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            * @param                arg5 ["uint256", "bytes32", "int256"]
            * @param                arg6 ["uint256", "bytes32", "int256"]
            * @param                arg7 ["uint256", "bytes32", "int256"]
            */
            case 0xef1a27a9 {
                if eq(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388, address()) { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x0100) {
                        if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x84), iszero(iszero(calldataload(0x84)))) { revert(0, 0); } else {
                                    if eq(0, sgt(calldataload(0x64), 0)) {
                                        if iszero(or(eq(div(mul(calldataload(0x64), calldataload(0xa4)), calldataload(0x64)), calldataload(0xa4)), iszero(calldataload(0x64)))) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x11)
                                            if iszero(calldataload(0x84)) {
                                                if gt(and(0xffffffffffffffffffffffffffffffff, calldataload(0x44)), add(and(0xffffffffffffffffffffffffffffffff, calldataload(0x44)), calldataload(0x64))) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x11)
                                                    if sgt(calldataload(0x64), 0) {
                                                        if gt(sub(add(and(0xffffffffffffffffffffffffffffffff, calldataload(0x44)), calldataload(0x64)), div(mul(calldataload(0x64), calldataload(0xa4)), 0x0de0b6b3a7640000)), add(and(0xffffffffffffffffffffffffffffffff, calldataload(0x44)), calldataload(0x64))) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x11)
                                                            if iszero(sload(add(calldataload(0x04), 0x03))) {
                                                                if iszero(sload(add(calldataload(0x04), 0x03))) {
                                                                    if iszero(sload(add(calldataload(0x04), 0x03))) {
                                                                        if iszero(lt(calldataload(0xe4), sub(add(and(0xffffffffffffffffffffffffffffffff, calldataload(0x44)), calldataload(0x64)), div(mul(calldataload(0x64), calldataload(0xa4)), 0x0de0b6b3a7640000)))) {
                                                                        }
                                                                        if iszero(sload(add(calldataload(0x04), 0x03))) {
                                                                            if iszero(sload(add(calldataload(0x04), 0x03))) {
                                                                                if iszero(sload(add(calldataload(0x04), 0x03))) {
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                            if eq(calldataload(0x64), 0x8000000000000000000000000000000000000000000000000000000000000000) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x11)
                                                                if iszero(lt(sub(0, calldataload(0x64)), and(0xffffffffffffffffffffffffffffffff, calldataload(0x44)))) { revert(0, 0); } else {
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
            * @custom:signature    Unresolved_3f4e3626(uint256 arg0, address arg1, uint256 arg2) public payable
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            */
            case 0x3f4e3626 {
                if eq(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388, address()) { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, add(calldataload(0x04), 0x06))
                            mstore(0x20, add(calldataload(0x04), 0x04))
                            if iszero(iszero(calldataload(0x44))) {
                                if iszero(iszero(iszero(sload(sha3(0, 0x40))))) {
                                    mstore(0, sload(sha3(0, 0x40)))
                                    mstore(0x20, calldataload(0x04))
                                    if eq(0, iszero(gt(sload(add(sha3(0, 0x40), 0x01)), calldataload(0x44)))) {
                                        if gt(sub(sload(add(sha3(0, 0x40), 0x01)), calldataload(0x44)), sload(add(sha3(0, 0x40), 0x01))) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x11)
                                            sstore(add(sha3(0, 0x40), 0x01), 0)
                                            mstore(0, sload(sha3(0, 0x40)))
                                            mstore(0x20, calldataload(0x04))
                                            if eq(0, iszero(iszero(shr(0xd0, sload(sha3(0, 0x40)))))) {
                                                mstore(0, shr(0xd0, sload(sha3(0, 0x40))))
                                                mstore(0x20, calldataload(0x04))
                                                sstore(sha3(0, 0x40), or(and(0xffffffffffff0000000000000000000000000000000000000000, shl(0xa0, and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff))), and(0xffffffffffff000000000000ffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                if iszero(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff)) {
                                                }
                                                sstore(add(calldataload(0x04), 0x03), sload(add(calldataload(0x04), 0x03)))
                                                mstore(0, and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
                                                mstore(0x20, add(calldataload(0x04), 0x04))
                                                sstore(sha3(0, 0x40), sload(sha3(0, 0x40)))
                                                if iszero(sload(add(calldataload(0x04), 0x03))) { revert(0, 0); } else {
                                                    mstore(0x80, calldataload(0x44))
                                                    log2(mload(0x40), 0x20, 0x4c672bd1e7444966ce521bc0f053d4f359f1fad9cfe6a43011c00baac6278e4d, and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
                                                    sstore(add(calldataload(0x04), 0x01), sload(add(calldataload(0x04), 0x02)))
                                                    mstore(0x80, calldataload(0x44))
                                                    log2(mload(0x40), 0x20, 0x4c672bd1e7444966ce521bc0f053d4f359f1fad9cfe6a43011c00baac6278e4d, and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
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
            * @custom:signature    Unresolved_18958ce2(uint256 arg0, address arg1, uint256 arg2) public payable
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            */
            case 0x18958ce2 {
                if eq(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388, address()) { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if iszero(calldataload(0x44)) {
                                sstore(add(calldataload(0x04), 0x02), add(sload(add(calldataload(0x04), 0x02)), 0x01))
                                if gt(sload(add(calldataload(0x04), 0x02)), 0xffffffffffff) { revert(mload(0x40), 0x04); } else {
                                    mstore(0x80, 0xea097be600000000000000000000000000000000000000000000000000000000)
                                    mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))
                                    mstore(0x20, add(calldataload(0x04), 0x06))
                                    if or(lt(add(mload(0x40), 0x80), mload(0x40)), gt(add(mload(0x40), 0x80), 0xffffffffffffffff)) {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x41)
                                        mstore(0x40, add(mload(0x40), 0x80))
                                        mstore(0x80, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))
                                        mstore(0xa0, 0)
                                        mstore(0xc0, and(sload(sha3(0, 0x40)), 0xffffffffffff))
                                        mstore(0xe0, calldataload(0x44))
                                        mstore(0, sload(add(calldataload(0x04), 0x02)))
                                        mstore(0x20, calldataload(0x04))
                                        sstore(sha3(0, 0x40), or(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(mload(mload(0x40)), 0xffffffffffffffffffffffffffffffffffffffff)))
                                        sstore(sha3(0, 0x40), or(and(0xffffffffffff0000000000000000000000000000000000000000, shl(0xa0, and(mload(add(mload(0x40), 0x20)), 0xffffffffffff))), and(0xffffffffffff000000000000ffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                        sstore(sha3(0, 0x40), or(and(0xffffffffffff0000000000000000000000000000000000000000000000000000, shl(0xd0, and(mload(add(mload(0x40), 0x40)), 0xffffffffffff))), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                        sstore(add(sha3(0, 0x40), 0x01), mload(add(mload(0x40), 0x60)))
                                        if iszero(sload(add(calldataload(0x04), 0x01))) {
                                            if iszero(sload(sha3(0, 0x40))) {
                                                mstore(0, sload(sha3(0, 0x40)))
                                                mstore(0x20, calldataload(0x04))
                                                sstore(sha3(0, 0x40), or(and(0xffffffffffff0000000000000000000000000000000000000000, shl(0xa0, and(sload(add(calldataload(0x04), 0x02)), 0xffffffffffff))), and(0xffffffffffff000000000000ffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))
                                                mstore(0x20, add(calldataload(0x04), 0x06))
                                                sstore(sha3(0, 0x40), sload(add(calldataload(0x04), 0x02)))
                                                if gt(sload(add(calldataload(0x04), 0x03)), add(sload(add(calldataload(0x04), 0x03)), calldataload(0x44))) { revert(0, 0); } else {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x11)
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
            * @custom:signature    Unresolved_32db40c9(uint256 arg0, address arg1, uint256 arg2, uint256 arg3, uint256 arg4) public payable returns (bytes memory)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            */
            case 0x32db40c9 {
                if eq(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388, address()) { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xa0) {
                        if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if iszero(iszero(and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))) {
                                if iszero(iszero(calldataload(0x44))) {
                                    if iszero(iszero(gt(calldataload(0x64), calldataload(0x44)))) {
                                        if iszero(lt(calldataload(0x64), sload(add(calldataload(0x04), 0x02)))) {
                                            if iszero(iszero(calldataload(0x84))) {
                                                if gt(calldataload(0x84), 0x40) {
                                                    if gt(sub(calldataload(0x64), calldataload(0x44)), calldataload(0x64)) {
                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x04, 0x11)
                                                        if gt(sub(calldataload(0x64), calldataload(0x44)), 0x40) { revert(mload(0x40), 0x04); } else {
                                                            mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
                                                            mstore(0, calldataload(0x44))
                                                            mstore(0x20, calldataload(0x04))
                                                            if eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))) {
                                                                if iszero(eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))) { revert(mload(0x40), 0x04); } else {
                                                                    mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
                                                                    if gt(calldataload(0x44), add(calldataload(0x44), 0x01)) {
                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                        mstore(0x04, 0x11)
                                                                        if iszero(gt(add(calldataload(0x44), 0x01), calldataload(0x64))) {
                                                                            mstore(0, add(calldataload(0x44), 0x01))
                                                                            mstore(0x20, calldataload(0x04))
                                                                            if sload(add(sha3(0, 0x40), 0x01)) {
                                                                                if sub(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))) { revert(mload(0x40), 0x04); } else {
                                                                                    mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
                                                                                    sstore(add(sha3(0, 0x40), 0x01), add(sload(add(sha3(0, 0x40), 0x01)), sload(add(sha3(0, 0x40), 0x01))))
                                                                                    sstore(add(sha3(0, 0x40), 0x01), 0)
                                                                                    mstore(0, add(calldataload(0x44), 0x01))
                                                                                    mstore(0x20, calldataload(0x04))
                                                                                    if eq(0, iszero(iszero(shr(0xd0, sload(sha3(0, 0x40)))))) {
                                                                                        mstore(0, shr(0xd0, sload(sha3(0, 0x40))))
                                                                                        mstore(0x20, calldataload(0x04))
                                                                                        sstore(sha3(0, 0x40), or(and(0xffffffffffff0000000000000000000000000000000000000000, shl(0xa0, and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff))), and(0xffffffffffff000000000000ffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                                                        if iszero(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff)) {
                                                                                        }
                                                                                        if 0 {
                                                                                            codecopy(0, 0x1629, 0x20)
                                                                                            mstore(0, mload(0))
                                                                                            mstore(0x80, 0)
                                                                                            mstore(0xa0, 0)
                                                                                            log4(mload(0x40), 0x40, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)), calldataload(0x44), calldataload(0x44))
                                                                                            mstore(0x80, 0)
                                                                                            mstore(0xa0, 0)
                                                                                            mstore(0xc0, calldataload(0x44))
                                                                                            return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                                                            mstore(0x80, 0)
                                                                                            mstore(0xa0, 0)
                                                                                            mstore(0xc0, 0)
                                                                                            return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                                                            if iszero(sload(add(sha3(0, 0x40), 0x01))) { revert(mload(0x40), 0x04); } else {
                                                                                                mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
                                                                                                if gt(sub(calldataload(0x64), calldataload(0x44)), calldataload(0x64)) {
                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                    mstore(0x04, 0x11)
                                                                                                    if iszero(calldataload(0x84)) { revert(0, 0); } else {
                                                                                                    }
                                                                                                    mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_79810ffe(uint256 arg0, uint256 arg1, uint256 arg2, uint256 arg3, uint256 arg4) public payable returns (bytes memory)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            */
            case 0x79810ffe {
                if eq(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388, address()) { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xa0) {
                        if lt(sload(add(calldataload(0x04), 0x01)), sload(add(calldataload(0x04), 0x02))) {
                            if iszero(iszero(calldataload(0x44))) {
                                if iszero(lt(0, calldataload(0x24))) {
                                    mstore(0, sload(add(calldataload(0x04), 0x01)))
                                    mstore(0x20, calldataload(0x04))
                                    if iszero(sload(add(sha3(0, 0x40), 0x01))) {
                                        if lt(calldataload(0x44), sload(add(sha3(0, 0x40), 0x01))) {
                                            codecopy(0, 0x1609, 0x20)
                                            mstore(0, mload(0))
                                            if gt(sub(sload(add(sha3(0, 0x40), 0x01)), calldataload(0x44)), sload(add(sha3(0, 0x40), 0x01))) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x11)
                                                sstore(add(sha3(0, 0x40), 0x01), sub(sload(add(sha3(0, 0x40), 0x01)), calldataload(0x44)))
                                                mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40))))
                                                mstore(0x20, calldataload(0x64))
                                                if gt(sload(sha3(0, 0x40)), add(sload(sha3(0, 0x40)), calldataload(0x44))) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x11)
                                                    sstore(add(sha3(0, 0x40), 0x01), 0)
                                                    mstore(0, sload(add(calldataload(0x04), 0x01)))
                                                    mstore(0x20, calldataload(0x04))
                                                    if eq(0, iszero(iszero(shr(0xd0, sload(sha3(0, 0x40)))))) {
                                                        mstore(0, shr(0xd0, sload(sha3(0, 0x40))))
                                                        mstore(0x20, calldataload(0x04))
                                                        sstore(sha3(0, 0x40), or(and(0xffffffffffff0000000000000000000000000000000000000000, shl(0xa0, and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff))), and(0xffffffffffff000000000000ffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                        if iszero(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff)) {
                                                        }
                                                        if eq(0, iszero(sload(add(calldataload(0x04), 0x03)))) { revert(0, 0); } else {
                                                            sstore(add(calldataload(0x04), 0x01), sload(add(calldataload(0x04), 0x01)))
                                                            sstore(add(calldataload(0x04), 0x03), sload(add(calldataload(0x04), 0x03)))
                                                            mstore(0x80, 0)
                                                            mstore(0xa0, calldataload(0x84))
                                                            return(mload(0x40), 0x40)
                                                            sstore(add(calldataload(0x04), 0x01), sload(add(calldataload(0x04), 0x02)))
                                                            sstore(add(calldataload(0x04), 0x03), sload(add(calldataload(0x04), 0x03)))
                                                            mstore(0x80, 0)
                                                            mstore(0xa0, calldataload(0x84))
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
                }
            }
            
            /*
            * @custom:signature    Unresolved_2448a553(uint256 arg0, address arg1, uint256 arg2, uint256 arg3, uint256 arg4) public payable returns (bytes memory)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            */
            case 0x2448a553 {
                if eq(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388, address()) { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xa0) {
                        if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if iszero(iszero(and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))) {
                                if iszero(calldataload(0x84)) {
                                    if iszero(iszero(calldataload(0x64))) {
                                        if gt(calldataload(0x64), 0x40) {
                                            if calldataload(0x44) {
                                                if iszero(calldataload(0x44)) {
                                                    mstore(0, calldataload(0x44))
                                                    mstore(0x20, calldataload(0x04))
                                                    if eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))) {
                                                        if iszero(iszero(eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))))) {
                                                            if iszero(eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))) {
                                                                mstore(0x80, 0)
                                                                mstore(0xa0, 0)
                                                                mstore(0xc0, 0)
                                                                return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                                if iszero(iszero(calldataload(0x44))) {
                                                                    if iszero(lt(0, 0x40)) {
                                                                        if iszero(iszero(0)) {
                                                                            if iszero(iszero(0)) {
                                                                                if iszero(0) {
                                                                                    if lt(0, 0) {
                                                                                        mstore(0, calldataload(0x44))
                                                                                        mstore(0x20, calldataload(0x04))
                                                                                        sstore(add(sha3(0, 0x40), 0x01), 0)
                                                                                        mstore(0, calldataload(0x44))
                                                                                        mstore(0x20, calldataload(0x04))
                                                                                        if eq(0, iszero(iszero(shr(0xd0, sload(sha3(0, 0x40)))))) {
                                                                                            mstore(0, shr(0xd0, sload(sha3(0, 0x40))))
                                                                                            mstore(0x20, calldataload(0x04))
                                                                                            sstore(sha3(0, 0x40), or(and(0xffffffffffff0000000000000000000000000000000000000000, shl(0xa0, and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff))), and(0xffffffffffff000000000000ffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                                                            if iszero(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff)) {
                                                                                            }
                                                                                            mstore(0, 0)
                                                                                            mstore(0x20, calldataload(0x04))
                                                                                            if gt(sload(add(sha3(0, 0x40), 0x01)), add(sload(add(sha3(0, 0x40), 0x01)), 0)) {
                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                mstore(0x04, 0x11)
                                                                                                sstore(add(sha3(0, 0x40), 0x01), add(sload(add(sha3(0, 0x40), 0x01)), 0))
                                                                                                codecopy(0, 0x1629, 0x20)
                                                                                                mstore(0, mload(0))
                                                                                                mstore(0x80, 0)
                                                                                                mstore(0xa0, 0)
                                                                                                log4(mload(0x40), 0x40, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)), calldataload(0x44), 0)
                                                                                                mstore(0x80, 0)
                                                                                                mstore(0xa0, 0)
                                                                                                mstore(0xc0, 0)
                                                                                                return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                                                                mstore(0x80, 0)
                                                                                                mstore(0xa0, 0)
                                                                                                mstore(0xc0, 0)
                                                                                                return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                                                                mstore(0, calldataload(0x44))
                                                                                                mstore(0x20, calldataload(0x04))
                                                                                                if eq(and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff), and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff)) {
                                                                                                    if iszero(iszero(eq(and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff), and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff)))) {
                                                                                                        if iszero(eq(and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff), and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff))) {
                                                                                                            if iszero(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff)) {
                                                                                                                mstore(0, and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff))
                                                                                                                if eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))) {
                                                                                                                    if iszero(eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))) {
                                                                                                                        if gt(sload(add(sha3(0, 0x40), 0x01)), add(sload(add(sha3(0, 0x40), 0x01)), add(0, sload(add(sha3(0, 0x40), 0x01))))) {
                                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0x04, 0x11)
                                                                                                                            if iszero(lt(add(sload(add(sha3(0, 0x40), 0x01)), add(0, sload(add(sha3(0, 0x40), 0x01)))), calldataload(0x84))) {
                                                                                                                            }
                                                                                                                            if iszero(sload(add(sha3(0, 0x40), 0x01))) {
                                                                                                                            }
                                                                                                                            if iszero(lt(sload(add(sha3(0, 0x40), 0x01)), calldataload(0x84))) {
                                                                                                                            }
                                                                                                                            if iszero(iszero(sload(add(sha3(0, 0x40), 0x01)))) {
                                                                                                                            }
                                                                                                                            if iszero(iszero(iszero(calldataload(0x44)))) {
                                                                                                                            }
                                                                                                                            if iszero(lt(sload(add(0x01, sha3(0, 0x40))), calldataload(0x84))) {
                                                                                                                                mstore(0x80, 0)
                                                                                                                                mstore(0xa0, 0)
                                                                                                                                mstore(0xc0, 0)
                                                                                                                                return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                                                                                                if iszero(iszero(sload(add(sha3(0, 0x40), 0x01)))) {
                                                                                                                                }
                                                                                                                                mstore(0x80, 0)
                                                                                                                                mstore(0xa0, 0)
                                                                                                                                mstore(0xc0, 0)
                                                                                                                                return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                                                                                                if calldataload(0x44) {
                                                                                                                                }
                                                                                                                            }
                                                                                                                            if iszero(calldataload(0x64)) { revert(0, 0); } else {
                                                                                                                            }
                                                                                                                            mstore(0x80, 0)
                                                                                                                            mstore(0xa0, 0)
                                                                                                                            mstore(0xc0, 0)
                                                                                                                            return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
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
            * @custom:signature    Unresolved_82296364(uint64 arg0, uint64 arg1, address arg2, uint32 arg3, uint256 arg4) public pure
            * @param                arg0 ["uint64", "bytes8", "int64"]
            * @param                arg1 ["uint64", "bytes8", "int64"]
            * @param                arg2 ["address", "uint128", "bytes16", "int128"]
            * @param                arg3 ["uint32", "bytes4", "int32"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            */
            case 0x82296364 {
                if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x0120) {
                    if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffff)) { revert(0, 0); } else {
                        if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffff)) { revert(0, 0); } else {
                                    if sub(calldataload(0x84), iszero(iszero(calldataload(0x84)))) { revert(0, 0); } else {
                                        if eq(0, calldataload(0x84)) {
                                            if gt(add(and(0xffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffff, div(and(calldataload(0x04), 0xffffffffffffffff), 0xc350))), 0xffffffffffffffff) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x11)
                                                if iszero(gt(and(0xffffffffffffffff, calldataload(0x24)), and(0xffffffffffffffff, add(and(0xffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffff, div(and(calldataload(0x04), 0xffffffffffffffff), 0xc350)))))) {
                                                    if gt(sub(and(0xffffffffffffffff, calldataload(0x24)), and(0xffffffffffffffff, div(and(calldataload(0x04), 0xffffffffffffffff), 0xc350))), 0xffffffffffffffff) {
                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x04, 0x11)
                                                        if iszero(calldataload(0x84)) {
                                                            if or(and(slt(sub(and(sub(and(0xffffffffffffffff, calldataload(0x24)), and(0xffffffffffffffff, div(and(calldataload(0x04), 0xffffffffffffffff), 0xc350))), 0xffffffffffffffff), and(calldataload(0x04), 0xffffffffffffffff)), and(sub(and(0xffffffffffffffff, calldataload(0x24)), and(0xffffffffffffffff, div(and(calldataload(0x04), 0xffffffffffffffff), 0xc350))), 0xffffffffffffffff)), sgt(0, and(calldataload(0x04), 0xffffffffffffffff))), and(sgt(sub(and(sub(and(0xffffffffffffffff, calldataload(0x24)), and(0xffffffffffffffff, div(and(calldataload(0x04), 0xffffffffffffffff), 0xc350))), 0xffffffffffffffff), and(calldataload(0x04), 0xffffffffffffffff)), and(sub(and(0xffffffffffffffff, calldataload(0x24)), and(0xffffffffffffffff, div(and(calldataload(0x04), 0xffffffffffffffff), 0xc350))), 0xffffffffffffffff)), iszero(sgt(0, and(calldataload(0x04), 0xffffffffffffffff))))) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x11)
                                                                if and(eq(and(calldataload(0x64), 0xffffffff), 0x8000000000000000000000000000000000000000000000000000000000000000), slt(and(0xffffffffffffffffffffffffffffffff, calldataload(0x44)), 0)) {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x11)
                                                                    if iszero(or(iszero(and(0xffffffffffffffffffffffffffffffff, calldataload(0x44))), eq(sdiv(mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x44)), and(calldataload(0x64), 0xffffffff)), and(0xffffffffffffffffffffffffffffffff, calldataload(0x44))), and(calldataload(0x64), 0xffffffff)))) {
                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                        mstore(0x04, 0x11)
                                                                        if gt(and(0xffffffffffffffff, calldataload(0x24)), and(calldataload(0x04), 0xffffffffffffffff)) {
                                                                            if iszero(calldataload(0x84)) {
                                                                            }
                                                                            if iszero(calldataload(0x84)) {
                                                                            }
                                                                        }
                                                                        if gt(add(and(0xffffffffffffffff, calldataload(0x24)), and(0xffffffffffffffff, div(and(calldataload(0x04), 0xffffffffffffffff), 0xc350))), 0xffffffffffffffff) {
                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0x04, 0x11)
                                                                            if iszero(lt(and(add(and(0xffffffffffffffff, calldataload(0x24)), and(0xffffffffffffffff, div(and(calldataload(0x04), 0xffffffffffffffff), 0xc350))), 0xffffffffffffffff), and(calldataload(0x04), 0xffffffffffffffff))) {
                                                                                if lt(and(calldataload(0x24), 0xffffffffffffffff), and(calldataload(0x04), 0xffffffffffffffff)) { revert(0, 0); } else {
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
            * @custom:signature    Unresolved_3cf4208d(uint256 arg0, address arg1, uint256 arg2, uint256 arg3, uint256 arg4, uint256 arg5) public payable returns (bytes memory)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            * @param                arg5 ["uint256", "bytes32", "int256"]
            */
            case 0x3cf4208d {
                if eq(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388, address()) { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xc0) {
                        if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if iszero(iszero(and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))) {
                                if iszero(iszero(calldataload(0xa4))) {
                                    if iszero(iszero(calldataload(0x44))) {
                                        if iszero(calldataload(0x64)) {
                                            if eq(calldataload(0x44), calldataload(0x64)) {
                                                if iszero(iszero(calldataload(0x84))) {
                                                    if gt(calldataload(0x84), 0x40) {
                                                        if iszero(eq(calldataload(0x44), calldataload(0x64))) {
                                                            if iszero(lt(0, 0x40)) {
                                                                if eq(calldataload(0x44), calldataload(0x64)) {
                                                                    if iszero(iszero(eq(calldataload(0x44), calldataload(0x64)))) {
                                                                        if iszero(eq(calldataload(0x44), calldataload(0x64))) { revert(mload(0x40), 0x04); } else {
                                                                            mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0, calldataload(0x64))
                                                                            mstore(0x20, calldataload(0x04))
                                                                            if eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) {
                                                                                if iszero(eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(mload(0x40), 0x04); } else {
                                                                                    mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
                                                                                    if lt(0, 0) {
                                                                                        mstore(0, calldataload(0x44))
                                                                                        mstore(0x20, calldataload(0x04))
                                                                                        codecopy(0, 0x1649, 0x20)
                                                                                        mstore(0, mload(0))
                                                                                        sstore(add(sha3(0, 0x40), 0x01), 0)
                                                                                        mstore(0, calldataload(0x44))
                                                                                        mstore(0x20, calldataload(0x04))
                                                                                        if eq(0, iszero(iszero(shr(0xd0, sload(sha3(0, 0x40)))))) {
                                                                                            mstore(0, shr(0xd0, sload(sha3(0, 0x40))))
                                                                                            mstore(0x20, calldataload(0x04))
                                                                                            sstore(sha3(0, 0x40), or(and(0xffffffffffff0000000000000000000000000000000000000000, shl(0xa0, and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff))), and(0xffffffffffff000000000000ffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                                                            if iszero(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff)) {
                                                                                            }
                                                                                            mstore(0, calldataload(0x64))
                                                                                            mstore(0x20, calldataload(0x04))
                                                                                            if gt(sload(add(sha3(0, 0x40), 0x01)), add(sload(add(sha3(0, 0x40), 0x01)), 0)) {
                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                mstore(0x04, 0x11)
                                                                                                sstore(add(sha3(0, 0x40), 0x01), add(sload(add(sha3(0, 0x40), 0x01)), 0))
                                                                                                codecopy(0, 0x1629, 0x20)
                                                                                                mstore(0, mload(0))
                                                                                                mstore(0x80, 0)
                                                                                                mstore(0xa0, 0)
                                                                                                log4(mload(0x40), 0x40, mload(0), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff), calldataload(0x44), calldataload(0x64))
                                                                                                mstore(0x80, 0)
                                                                                                mstore(0xa0, 0)
                                                                                                mstore(0xc0, calldataload(0x64))
                                                                                                return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                                                                                if iszero(sload(add(sha3(0, 0x40), 0x01))) { revert(mload(0x40), 0x04); } else {
                                                                                                    mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
                                                                                                    if iszero(0) { revert(mload(0x40), 0x04); } else {
                                                                                                        mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
                                                                                                        if iszero(iszero(0)) {
                                                                                                        }
                                                                                                        mstore(0, calldataload(0x44))
                                                                                                        mstore(0x20, calldataload(0x04))
                                                                                                        if eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) {
                                                                                                            if iszero(iszero(eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)))) {
                                                                                                                if iszero(eq(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(mload(0x40), 0x04); } else {
                                                                                                                    mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
                                                                                                                    if iszero(and(0xffffffffffff, shr(0xa0, sload(sha3(0, 0x40))))) { revert(mload(0x40), 0x04); } else {
                                                                                                                        mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
                                                                                                                        if iszero(lt(sload(add(sha3(0, 0x40), 0x01)), calldataload(0xa4))) { revert(mload(0x40), 0x04); } else {
                                                                                                                            mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
                                                                                                                            if iszero(iszero(sload(add(sha3(0, 0x40), 0x01)))) {
                                                                                                                            }
                                                                                                                            if iszero(iszero(eq(calldataload(0x44), calldataload(0x64)))) {
                                                                                                                            }
                                                                                                                        }
                                                                                                                        if iszero(calldataload(0x84)) { revert(0, 0); } else {
                                                                                                                        }
                                                                                                                        mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
                                                                                                                        mstore(0x80, 0x5b6d2b7a00000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_b67f3dd7(uint256 arg0, uint64 arg1, uint64 arg2, uint256 arg3, uint256 arg4, uint256 arg5, uint256 arg6) public pure returns (uint256)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["uint64", "bytes8", "int64"]
            * @param                arg2 ["uint64", "bytes8", "int64"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            * @param                arg5 ["uint256", "bytes32", "int256"]
            * @param                arg6 ["uint256", "bytes32", "int256"]
            */
            case 0xb67f3dd7 {
                if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xe0) {
                    if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffff)) { revert(0, 0); } else {
                        if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffff)) { revert(0, 0); } else {
                            if iszero(lt(and(calldataload(0x24), 0xffffffffffffffff), and(calldataload(0x44), 0xffffffffffffffff))) {
                                if gt(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff) {
                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                    mstore(0x04, 0x11)
                                    if iszero(and(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff)) {
                                        if sub(0x0de0b6b3a7640000, div(mul(and(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff), 0x0de0b6b3a7640000), and(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff))) {
                                            if iszero(and(calldataload(0x24), 0xffffffffffffffff)) {
                                                if iszero(or(eq(div(mul(div(mul(and(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff), 0x0de0b6b3a7640000), and(calldataload(0x24), 0xffffffffffffffff)), calldataload(0x84)), div(mul(and(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff), 0x0de0b6b3a7640000), and(calldataload(0x24), 0xffffffffffffffff))), calldataload(0x84)), iszero(div(mul(and(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff), 0x0de0b6b3a7640000), and(calldataload(0x24), 0xffffffffffffffff))))) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x11)
                                                    if iszero(div(mul(div(mul(and(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff), 0x0de0b6b3a7640000), and(calldataload(0x24), 0xffffffffffffffff)), calldataload(0x84)), 0x0de0b6b3a7640000)) {
                                                        if iszero(div(mul(div(mul(and(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff), 0x0de0b6b3a7640000), and(calldataload(0x24), 0xffffffffffffffff)), calldataload(0x84)), 0x0de0b6b3a7640000)) {
                                                            if sub(div(mul(0x0f4240, div(mul(and(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff), 0x0de0b6b3a7640000), and(calldataload(0x24), 0xffffffffffffffff))), 0x0f4240), div(mul(and(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff), 0x0de0b6b3a7640000), and(calldataload(0x24), 0xffffffffffffffff))) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x11)
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x12)
                                                                if sub(div(mul(0x0f4240, div(mul(and(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff), 0x0de0b6b3a7640000), and(calldataload(0x24), 0xffffffffffffffff))), 0x0f4240), div(mul(and(sub(and(0xffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffff, calldataload(0x24))), 0xffffffffffffffff), 0x0de0b6b3a7640000), and(calldataload(0x24), 0xffffffffffffffff))) { revert(0, 0); } else {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x11)
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x12)
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x11)
                                                                    mstore(0x80, 0)
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
            default { revert(0, 0) }
        }
    }
}