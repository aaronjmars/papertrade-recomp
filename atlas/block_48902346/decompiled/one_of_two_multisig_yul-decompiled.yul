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
            * @custom:signature    Unresolved_1a5f66c3() public view returns (address)
            */
            case 0x1a5f66c3 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x01)))
                        return(0x80, 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_9ace38c2(uint256 arg0) public view returns (bytes memory)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x9ace38c2 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        mstore(0, calldataload(0x04))
                        mstore(0x20, 0x05)
                        if iszero(and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                            if eq(lt(shr(0x01, sload(add(sha3(0, 0x40), 0x02))), 0x20), and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x22)
                                mstore(0x80, shr(0x01, sload(add(sha3(0, 0x40), 0x02))))
                                if eq(0, and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                    if eq(0x01, and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                        mstore(0, add(sha3(0, 0x40), 0x02))
                                        if lt(0, shr(0x01, sload(add(sha3(0, 0x40), 0x02)))) {
                                            if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(add(mload(0x40), 0), 0x20), mload(0x40)), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(add(mload(0x40), 0), 0x20), mload(0x40)), 0x1f))), 0xffffffffffffffff)) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(add(mload(0x40), 0), 0x20), mload(0x40)), 0x1f))))
                                                mstore(0xa0, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff))
                                                mstore(0xc0, sload(add(sha3(0, 0x40), 0x01)))
                                                mstore(0xe0, 0xc0)
                                                mstore(0x0160, mload(mload(0x40)))
                                                if lt(0, mload(mload(0x40))) {
                                                    mstore(0x0180, 0)
                                                    mstore(0x0100, and(sload(add(sha3(0, 0x40), 0x03)), 0xffffffffffffffffffffffffffffffffffffffff))
                                                    mstore(0x0120, sload(add(sha3(0, 0x40), 0x04)))
                                                    if iszero(lt(and(sload(add(sha3(0, 0x40), 0x05)), 0xff), 0x03)) {
                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x04, 0x21)
                                                        mstore(0x0140, and(sload(add(sha3(0, 0x40), 0x05)), 0xff))
                                                        return(mload(0x40), sub(add(add(and(add(mload(mload(0x40)), 0x1f), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0), add(mload(0x40), 0xc0)), 0x20), mload(0x40)))
                                                        if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(0, mload(0x40)), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(0, mload(0x40)), 0x1f))), 0xffffffffffffffff)) { revert(0, 0); } else {
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
            }
            
            /*
            * @custom:signature    Unresolved_b77bf600() public view returns (uint256)
            */
            case 0xb77bf600 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x04))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_735631ad(uint256 arg0) public payable
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x735631ad {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, caller()), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0)))) {
                            if iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, caller()), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x01)))) {
                                if iszero(eq(and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, caller()))) { revert(mload(0x40), 0x04); } else {
                                    mstore(0x80, 0xa1b035c800000000000000000000000000000000000000000000000000000000)
                                    if iszero(lt(calldataload(0x04), sload(0x04))) {
                                        mstore(0, calldataload(0x04))
                                        mstore(0x20, 0x05)
                                        if sub(and(sload(add(sha3(0, 0x40), 0x03)), 0xffffffffffffffffffffffffffffffffffffffff), caller()) { revert(mload(0x40), 0x04); } else {
                                            mstore(0x80, 0xc544688400000000000000000000000000000000000000000000000000000000)
                                            if iszero(lt(and(sload(add(0x05, sha3(0, 0x40))), 0xff), 0x03)) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x21)
                                                if and(sload(add(0x05, sha3(0, 0x40))), 0xff) { revert(0, 0); } else {
                                                    mstore(0x80, 0x82235d5300000000000000000000000000000000000000000000000000000000)
                                                    sstore(add(0x05, sha3(0, 0x40)), or(0x02, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00, sload(add(0x05, sha3(0, 0x40))))))
                                                    log2(0, 0, 0x4c4e829c9b8c87162e976ab955be6db24dace1afaa0ebe4308b6c273a92f5875, calldataload(0x04))
                                                    mstore(0x80, 0x500a07ce00000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_82e717f7() public pure returns (uint256)
            */
            case 0x82e717f7 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, 0x02)
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_d98f851a() public view returns (address)
            */
            case 0xd98f851a {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_900cf0cf() public view returns (uint256)
            */
            case 0x900cf0cf {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x03))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_c6427474(address arg0, uint256 arg1, uint256 arg2) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            */
            case 0xc6427474 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if gt(calldataload(0x44), 0xffffffffffffffff) { revert(0, 0); } else {
                                if iszero(slt(add(calldataload(0x44), 0x23), calldatasize())) {
                                    if gt(calldataload(add(calldataload(0x44), 0x04)), 0xffffffffffffffff) { revert(0, 0); } else {
                                        if gt(add(add(calldataload(0x44), calldataload(add(0x04, calldataload(0x44)))), 0x24), calldatasize()) {
                                            if iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, caller()), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0)))) {
                                                if iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, caller()), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x01)))) {
                                                    if iszero(eq(and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, caller()))) { revert(mload(0x40), 0x04); } else {
                                                        mstore(0x80, 0xa1b035c800000000000000000000000000000000000000000000000000000000)
                                                        if eq(sload(0x04), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x11)
                                                            sstore(0x04, add(sload(0x04), 0x01))
                                                            if or(lt(add(mload(0x40), 0xc0), mload(0x40)), gt(add(mload(0x40), 0xc0), 0xffffffffffffffff)) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                mstore(0x40, add(mload(0x40), 0xc0))
                                                                mstore(0x80, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                mstore(0xa0, calldataload(0x24))
                                                                if gt(calldataload(add(0x04, calldataload(0x44))), 0xffffffffffffffff) {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x41)
                                                                    if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))), 0xffffffffffffffff)) {
                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                        mstore(0x04, 0x41)
                                                                        mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))))
                                                                        mstore(0x0140, calldataload(add(0x04, calldataload(0x44))))
                                                                        if gt(add(add(calldataload(0x44), 0x24), calldataload(add(0x04, calldataload(0x44)))), calldatasize()) {
                                                                            calldatacopy(add(mload(0x40), 0x20), add(calldataload(0x44), 0x24), calldataload(add(0x04, calldataload(0x44))))
                                                                            mstore(0x0160, 0)
                                                                            mstore(0xc0, mload(0x40))
                                                                            mstore(0xe0, caller())
                                                                            mstore(0x0100, sload(0x03))
                                                                            mstore(0x0120, 0)
                                                                            mstore(0, sload(0x04))
                                                                            mstore(0x20, 0x05)
                                                                            sstore(sha3(0, 0x40), or(and(0xffffffffffffffffffffffffffffffffffffffff, mload(mload(0x40))), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(sha3(0, 0x40)))))
                                                                            sstore(add(sha3(0, 0x40), 0x01), mload(add(mload(0x40), 0x20)))
                                                                            if gt(mload(mload(add(0x40, mload(0x40)))), 0xffffffffffffffff) {
                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                mstore(0x04, 0x41)
                                                                                if iszero(and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                                                                    if eq(lt(shr(0x01, sload(add(sha3(0, 0x40), 0x02))), 0x20), and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                        mstore(0x04, 0x22)
                                                                                        if gt(shr(0x01, sload(add(sha3(0, 0x40), 0x02))), 0x1f) {
                                                                                            mstore(0, add(sha3(0, 0x40), 0x02))
                                                                                            if lt(mload(mload(add(0x40, mload(0x40)))), 0x20) {
                                                                                                if lt(add(sha3(0, 0x20), shr(0x05, add(mload(mload(add(0x40, mload(0x40)))), 0x1f))), add(sha3(0, 0x20), shr(0x05, add(shr(0x01, sload(add(sha3(0, 0x40), 0x02))), 0x1f)))) {
                                                                                                    if eq(0x01, gt(mload(mload(add(0x40, mload(0x40)))), 0x1f)) {
                                                                                                        mstore(0, add(sha3(0, 0x40), 0x02))
                                                                                                        if lt(0, and(mload(mload(add(0x40, mload(0x40)))), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)) {
                                                                                                            if lt(and(mload(mload(add(0x40, mload(0x40)))), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0), mload(mload(add(0x40, mload(0x40))))) {
                                                                                                                sstore(sha3(0, 0x20), and(not(shr(and(shl(0x03, mload(mload(add(0x40, mload(0x40))))), 0xf8), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)), mload(add(mload(add(0x40, mload(0x40))), 0x20))))
                                                                                                                sstore(add(sha3(0, 0x40), 0x02), add(shl(0x01, mload(mload(add(0x40, mload(0x40))))), 0x01))
                                                                                                                sstore(add(sha3(0, 0x40), 0x03), or(and(sload(add(sha3(0, 0x40), 0x03)), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(mload(add(mload(0x40), 0x60)), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                                                                                sstore(add(sha3(0, 0x40), 0x04), mload(add(mload(0x40), 0x80)))
                                                                                                                if iszero(lt(mload(add(mload(0x40), 0xa0)), 0x03)) {
                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                    mstore(0x04, 0x21)
                                                                                                                    sstore(add(sha3(0, 0x40), 0x05), or(and(mload(add(mload(0x40), 0xa0)), 0xff), and(sload(add(sha3(0, 0x40), 0x05)), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00)))
                                                                                                                    if gt(calldataload(add(0x04, calldataload(0x44))), 0xffffffffffffffff) {
                                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                        mstore(0x04, 0x41)
                                                                                                                        if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))), 0xffffffffffffffff)) {
                                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0x04, 0x41)
                                                                                                                            mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldataload(add(0x04, calldataload(0x44)))))), 0x1f))))
                                                                                                                            mstore(0x0160, calldataload(add(0x04, calldataload(0x44))))
                                                                                                                            if gt(add(add(calldataload(0x44), 0x24), calldataload(add(0x04, calldataload(0x44)))), calldatasize()) {
                                                                                                                                calldatacopy(add(mload(0x40), 0x20), add(calldataload(0x44), 0x24), calldataload(add(0x04, calldataload(0x44))))
                                                                                                                                mstore(0x0180, 0)
                                                                                                                                mstore(0x01a0, chainid())
                                                                                                                                mstore(0x01c0, address())
                                                                                                                                mstore(0x01e0, sload(0x04))
                                                                                                                                mstore(0x0200, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                                                mstore(0x0220, calldataload(0x24))
                                                                                                                                mstore(0x0240, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                                                                                mstore(0x0260, sload(0x03))
                                                                                                                                mstore(0x0180, 0xe0)
                                                                                                                                if or(gt(add(mload(0x40), 0x0100), 0xffffffffffffffff), lt(add(mload(0x40), 0x0100), mload(0x40))) { revert(0, 0); } else {
                                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                    mstore(0x04, 0x41)
                                                                                                                                    mstore(0x40, add(mload(0x40), 0x0100))
                                                                                                                                    mstore(0x0280, calldataload(0x24))
                                                                                                                                    mstore(0x02a0, 0x60)
                                                                                                                                    mstore(0x02e0, calldataload(add(0x04, calldataload(0x44))))
                                                                                                                                    calldatacopy(add(mload(0x40), 0x80), add(calldataload(0x44), 0x24), calldataload(add(0x04, calldataload(0x44))))
                                                                                                                                    mstore(0x0300, 0)
                                                                                                                                    mstore(0x02c0, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                                                                                    log4(mload(0x40), add(sub(add(mload(0x40), and(add(calldataload(add(0x04, calldataload(0x44))), 0x1f), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)), mload(0x40)), 0x80), 0xbe411f0729ceed7585127466bac46d523f0ef18ba210980602e861c7a8fe4a7f, sload(0x04), caller(), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                                                    mstore(0x0280, sload(0x04))
                                                                                                                                    return(mload(0x40), 0x20)
                                                                                                                                    if mload(mload(add(0x40, mload(0x40)))) { revert(0, 0); } else {
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
                }
            }
            
            /*
            * @custom:signature    Unresolved_64d62769() public view returns (address)
            */
            case 0x64d62769 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_7b1106de(uint256 arg0, uint256 arg1) public payable
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            */
            case 0x7b1106de {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x40) {
                        if iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, caller()), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0)))) {
                            if iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, caller()), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x01)))) {
                                if iszero(eq(and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, caller()))) { revert(mload(0x40), 0x04); } else {
                                    mstore(0x80, 0xa1b035c800000000000000000000000000000000000000000000000000000000)
                                    if iszero(lt(calldataload(0x04), sload(0x04))) {
                                        mstore(0, calldataload(0x04))
                                        mstore(0x20, 0x05)
                                        if iszero(lt(and(sload(add(sha3(0, 0x40), 0x05)), 0xff), 0x03)) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x21)
                                            if and(sload(add(sha3(0, 0x40), 0x05)), 0xff) { revert(mload(0x40), 0x04); } else {
                                                mstore(0x80, 0x82235d5300000000000000000000000000000000000000000000000000000000)
                                                if sub(sload(add(sha3(0, 0x40), 0x04)), sload(0x03)) { revert(mload(0x40), 0x04); } else {
                                                    mstore(0x80, 0xe157707300000000000000000000000000000000000000000000000000000000)
                                                    if eq(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(add(sha3(0, 0x40), 0x03)))) {
                                                        if iszero(and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                                            if eq(lt(shr(0x01, sload(add(sha3(0, 0x40), 0x02))), 0x20), and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x22)
                                                                mstore(0x80, shr(0x01, sload(add(sha3(0, 0x40), 0x02))))
                                                                if eq(0, and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                                                    if eq(0x01, and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                                                        mstore(0, add(sha3(0, 0x40), 0x02))
                                                                        if lt(0, shr(0x01, sload(add(sha3(0, 0x40), 0x02)))) {
                                                                            if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(add(mload(0x40), 0), 0x20), mload(0x40)), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(add(mload(0x40), 0), 0x20), mload(0x40)), 0x1f))), 0xffffffffffffffff)) {
                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                mstore(0x04, 0x41)
                                                                                mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(add(mload(0x40), 0), 0x20), mload(0x40)), 0x1f))))
                                                                                mstore(0xc0, chainid())
                                                                                mstore(0xe0, address())
                                                                                mstore(0x0100, calldataload(0x04))
                                                                                mstore(0x0120, and(0xffffffffffffffffffffffffffffffffffffffff, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                                                mstore(0x0140, sload(add(sha3(0, 0x40), 0x01)))
                                                                                mstore(0x0160, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                                mstore(0x0180, sload(add(sha3(0, 0x40), 0x04)))
                                                                                mstore(0xa0, 0xe0)
                                                                                if or(gt(add(mload(0x40), 0x0100), 0xffffffffffffffff), lt(add(mload(0x40), 0x0100), mload(0x40))) {
                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                    mstore(0x04, 0x41)
                                                                                    mstore(0x40, add(mload(0x40), 0x0100))
                                                                                    if sub(sha3(add(mload(0x40), 0x20), mload(mload(0x40))), calldataload(0x24)) {
                                                                                        sstore(add(sha3(0, 0x40), 0x05), or(and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00, sload(add(sha3(0, 0x40), 0x05))), 0x01))
                                                                                        call(gas(), and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), sload(add(sha3(0, 0x40), 0x01)), add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)
                                                                                        if iszero(returndatasize()) {
                                                                                            if iszero(call(gas(), and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), sload(add(sha3(0, 0x40), 0x01)), add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) {
                                                                                                mstore(0x01a0, 0x15fcd67500000000000000000000000000000000000000000000000000000000)
                                                                                                mstore(0x01a4, 0x20)
                                                                                                mstore(0x01c4, mload(0x60))
                                                                                                if lt(0, mload(0x60)) { revert(mload(0x40), sub(add(add(and(add(mload(0x60), 0x1f), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0), add(mload(0x40), 0x24)), 0x20), mload(0x40))); } else {
                                                                                                    mstore(0x01e4, 0)
                                                                                                    if gt(returndatasize(), 0xffffffffffffffff) { revert(mload(0x40), 0x04); } else {
                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                        mstore(0x04, 0x41)
                                                                                                        mstore(0x01a0, 0x4e11f90600000000000000000000000000000000000000000000000000000000)
                                                                                                        if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(0, mload(0x40)), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(0, mload(0x40)), 0x1f))), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                            mstore(0x04, 0x41)
                                                                                                            mstore(0x80, 0x137b455900000000000000000000000000000000000000000000000000000000)
                                                                                                            mstore(0x80, 0x500a07ce00000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_7df73e27(address arg0) public view returns (bool)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x7df73e27 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0)))) {
                                if iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x01)))) { revert(0, 0); } else {
                                    mstore(0x80, iszero(iszero(eq(and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04))))))
                                    return(mload(0x40), 0x20)
                                    mstore(0x80, iszero(iszero(eq(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x01))))))
                                    return(mload(0x40), 0x20)
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_79301c0f(address arg0, address arg1, address arg2) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x79301c0f {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                    if sub(caller(), address()) { revert(mload(0x40), 0x04); } else {
                                        mstore(0x80, 0x29c3b7ee00000000000000000000000000000000000000000000000000000000)
                                        if gt(sload(0x03), add(sload(0x03), 0x01)) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x11)
                                            sstore(0x03, add(sload(0x03), 0x01))
                                            if iszero(iszero(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))) {
                                                if iszero(iszero(and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))) {
                                                    if iszero(and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff)) {
                                                        if iszero(eq(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))) {
                                                            if iszero(eq(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff))) {
                                                                if eq(and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff)) {
                                                                    if iszero(eq(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), address())) {
                                                                        if iszero(eq(and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff), address())) {
                                                                            if eq(and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff), address()) { revert(0, 0); } else {
                                                                                sstore(0, or(and(sload(0), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                                                sstore(0x01, or(and(sload(0x01), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                                                sstore(0x02, or(and(sload(0x02), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                                                mstore(0x80, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                mstore(0xa0, and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                mstore(0xc0, and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                mstore(0xe0, add(sload(0x03), 0x01))
                                                                                log1(mload(0x40), 0x80, 0xddfe9ff988d8830e7b19e61773b4a39f43d1d98b57f2aef535a4960c0291b0fd)
                                                                                mstore(0x80, 0x815e1d6400000000000000000000000000000000000000000000000000000000)
                                                                                mstore(0x80, 0x815e1d6400000000000000000000000000000000000000000000000000000000)
                                                                                mstore(0x80, 0x815e1d6400000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_27865bb3(uint256 arg0) public view returns (uint256)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x27865bb3 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if iszero(lt(calldataload(0x04), sload(0x04))) {
                            mstore(0, calldataload(0x04))
                            mstore(0x20, 0x05)
                            if iszero(and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                if eq(lt(shr(0x01, sload(add(sha3(0, 0x40), 0x02))), 0x20), and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                    mstore(0x04, 0x22)
                                    mstore(0x80, shr(0x01, sload(add(sha3(0, 0x40), 0x02))))
                                    if eq(0, and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                        if eq(0x01, and(sload(add(sha3(0, 0x40), 0x02)), 0x01)) {
                                            mstore(0, add(sha3(0, 0x40), 0x02))
                                            if lt(0, shr(0x01, sload(add(sha3(0, 0x40), 0x02)))) {
                                                if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(add(mload(0x40), 0), 0x20), mload(0x40)), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(add(mload(0x40), 0), 0x20), mload(0x40)), 0x1f))), 0xffffffffffffffff)) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x41)
                                                    mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(add(mload(0x40), 0), 0x20), mload(0x40)), 0x1f))))
                                                    mstore(0xc0, chainid())
                                                    mstore(0xe0, address())
                                                    mstore(0x0100, calldataload(0x04))
                                                    mstore(0x0120, and(0xffffffffffffffffffffffffffffffffffffffff, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                    mstore(0x0140, sload(add(sha3(0, 0x40), 0x01)))
                                                    mstore(0x0160, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                    mstore(0x0180, sload(add(sha3(0, 0x40), 0x04)))
                                                    mstore(0xa0, 0xe0)
                                                    if or(gt(add(mload(0x40), 0x0100), 0xffffffffffffffff), lt(add(mload(0x40), 0x0100), mload(0x40))) {
                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x04, 0x41)
                                                        mstore(0x40, add(mload(0x40), 0x0100))
                                                        mstore(0x01a0, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                        return(mload(0x40), 0x20)
                                                        if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(0, mload(0x40)), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(0, mload(0x40)), 0x1f))), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            mstore(0x80, 0x500a07ce00000000000000000000000000000000000000000000000000000000)
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