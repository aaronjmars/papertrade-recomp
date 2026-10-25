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
            * @custom:signature    Unresolved_2bc9ed54() public pure returns (uint256)
            */
            case 0x2bc9ed54 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        codecopy(0, 0x0ddf, 0x20)
                        mstore(0, mload(0))
                        mstore(0x80, mload(0))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_97dc97cb() public view returns (address)
            */
            case 0x97dc97cb {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x03), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_17a1678f(address arg0, uint64 arg1, address arg2) public pure
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint64", "bytes8", "int64"]
            * @param                arg2 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x17a1678f {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(and(calldataload(0x24), 0xffffffffffffffff), calldataload(0x24)) { revert(0, 0); } else {
                                if sub(and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff), calldataload(0x44)) { revert(0, 0); } else {
                                    mstore(0x80, 0xd2dd853100000000000000000000000000000000000000000000000000000000)
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_0b4c3a82() public pure returns (uint256)
            */
            case 0x0b4c3a82 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, 0xac4ddb8d63e9d7a862c5d61ce47517623a448262414a7eef6797102104b31214)
                        return(0x80, 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_d45167d0(uint256 arg0, bool arg1, uint256 arg2, uint256 arg3) public payable returns (uint256)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            */
            case 0xd45167d0 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x80) {
                        if sub(calldataload(0x24), and(calldataload(0x24), 0xff)) { revert(0, 0); } else {
                            mstore(0xa0, 0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f)
                            codecopy(0, 0x0e5f, 0x20)
                            mstore(0, mload(0))
                            mstore(0xc0, mload(0))
                            codecopy(0, 0x0dff, 0x20)
                            mstore(0, mload(0))
                            mstore(0xe0, mload(0))
                            mstore(0x0100, chainid())
                            mstore(0x0120, and(0xffffffffffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x03))))
                            mstore(0x80, 0xa0)
                            if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x41)
                                mstore(0x40, add(mload(0x40), 0xc0))
                                mstore(0x0160, 0x1901000000000000000000000000000000000000000000000000000000000000)
                                mstore(0x0162, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                mstore(0x0182, calldataload(0x04))
                                mstore(0x0140, 0x42)
                                if or(gt(add(mload(0x40), 0x80), 0xffffffffffffffff), lt(add(mload(0x40), 0x80), mload(0x40))) {
                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                    mstore(0x04, 0x41)
                                    mstore(0x40, add(mload(0x40), 0x80))
                                    if iszero(eq(and(0xff, calldataload(0x24)), 0x1b)) {
                                        if iszero(eq(and(0xff, calldataload(0x24)), 0x1b)) {
                                            if gt(calldataload(0x64), 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0) {
                                                mstore(0x01c0, 0)
                                                return(mload(0x40), 0x20)
                                                mstore(0x01c0, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                mstore(0x01e0, and(0xff, calldataload(0x24)))
                                                mstore(0x0200, calldataload(0x44))
                                                mstore(0x0220, calldataload(0x64))
                                                mstore(0, 0)
                                                staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)
                                                if iszero(staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)) { revert(0, 0); } else {
                                                    returndatacopy(mload(0x40), 0, returndatasize())
                                                    mstore(0x01c0, and(mload(0), 0xffffffffffffffffffffffffffffffffffffffff))
                                                    return(mload(0x40), 0x20)
                                                    mstore(0x01c0, 0)
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
            
            /*
            * @custom:signature    Unresolved_96ade1f9(address arg0, address arg1) public view returns (bytes memory)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x96ade1f9 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                mstore(0x20, 0x04)
                                mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))
                                mstore(0x20, sha3(0, 0x40))
                                mstore(0x80, and(sload(sha3(0, 0x40)), 0xffffffffffffffff))
                                mstore(0xa0, and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x40, sload(sha3(0, 0x40)))))
                                return(mload(0x40), 0x40)
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_cab7e8eb(address arg0, bool arg1) public view returns (bool)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["bool", "uint8", "bytes1", "int8"]
            */
            case 0xcab7e8eb {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                            mstore(0x20, 0x06)
                            mstore(0, shr(0x08, calldataload(0x24)))
                            mstore(0x20, sha3(0, 0x40))
                            mstore(0x80, iszero(iszero(and(sload(sha3(0, 0x40)), shl(and(calldataload(0x24), 0xff), 0x01)))))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_5f76a1d6(address arg0, address arg1, uint64 arg2, address arg3, bool arg4, uint64 arg5, bool arg6, uint256 arg7, uint256 arg8) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["uint64", "bytes8", "int64"]
            * @param                arg3 ["address", "uint160", "bytes20", "int160"]
            * @param                arg4 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg5 ["uint64", "bytes8", "int64"]
            * @param                arg6 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg7 ["uint256", "bytes32", "int256"]
            * @param                arg8 ["uint256", "bytes32", "int256"]
            */
            case 0x5f76a1d6 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x0120) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffff)) { revert(0, 0); } else {
                                    if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                        if sub(calldataload(0xa4), and(calldataload(0xa4), 0xffffffffffffffff)) { revert(0, 0); } else {
                                            if sub(calldataload(0xc4), and(calldataload(0xc4), 0xff)) { revert(0, 0); } else {
                                                mstore(0, caller())
                                                mstore(0x20, 0x07)
                                                if iszero(and(sload(sha3(0, 0x40)), 0xff)) {
                                                    if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))) {
                                                        if gt(timestamp(), and(calldataload(0xa4), 0xffffffffffffffff)) {
                                                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                            mstore(0x20, 0x06)
                                                            mstore(0, shr(0x08, calldataload(0x84)))
                                                            mstore(0x20, sha3(0, 0x40))
                                                            if and(sload(sha3(0, 0x40)), shl(and(calldataload(0x84), 0xff), 0x01)) { revert(mload(0x40), 0x04); } else {
                                                                mstore(0x80, 0x756688fe00000000000000000000000000000000000000000000000000000000)
                                                                mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                mstore(0x20, 0x06)
                                                                mstore(0, shr(0x08, calldataload(0x84)))
                                                                mstore(0x20, sha3(0, 0x40))
                                                                sstore(sha3(0, 0x40), or(sload(sha3(0, 0x40)), shl(and(calldataload(0x84), 0xff), 0x01)))
                                                                mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                mstore(0x20, 0x05)
                                                                if iszero(lt(calldataload(0x84), sload(sha3(0, 0x40)))) {
                                                                    codecopy(0, 0x0ddf, 0x20)
                                                                    mstore(0, mload(0))
                                                                    mstore(0xa0, mload(0))
                                                                    mstore(0xc0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                    mstore(0xe0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))
                                                                    mstore(0x0100, and(calldataload(0x44), 0xffffffffffffffff))
                                                                    mstore(0x0120, and(calldataload(0x64), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                    mstore(0x0140, calldataload(0x84))
                                                                    mstore(0x0160, and(calldataload(0xa4), 0xffffffffffffffff))
                                                                    mstore(0x80, 0xe0)
                                                                    if or(gt(add(mload(0x40), 0x0100), 0xffffffffffffffff), lt(add(mload(0x40), 0x0100), mload(0x40))) {
                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                        mstore(0x04, 0x41)
                                                                        mstore(0x40, add(mload(0x40), 0x0100))
                                                                        mstore(0x01a0, 0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f)
                                                                        codecopy(0, 0x0e5f, 0x20)
                                                                        mstore(0, mload(0))
                                                                        mstore(0x01c0, mload(0))
                                                                        codecopy(0, 0x0dff, 0x20)
                                                                        mstore(0, mload(0))
                                                                        mstore(0x01e0, mload(0))
                                                                        mstore(0x0200, chainid())
                                                                        mstore(0x0220, and(0xffffffffffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x03))))
                                                                        mstore(0x0180, 0xa0)
                                                                        if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0x04, 0x41)
                                                                            mstore(0x40, add(mload(0x40), 0xc0))
                                                                            mstore(0x0260, 0x1901000000000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0x0262, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                            mstore(0x0282, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                            mstore(0x0240, 0x42)
                                                                            if or(gt(add(mload(0x40), 0x80), 0xffffffffffffffff), lt(add(mload(0x40), 0x80), mload(0x40))) {
                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                mstore(0x04, 0x41)
                                                                                mstore(0x40, add(mload(0x40), 0x80))
                                                                                if iszero(eq(and(0xff, calldataload(0xc4)), 0x1b)) {
                                                                                    if iszero(eq(and(0xff, calldataload(0xc4)), 0x1b)) {
                                                                                        if gt(calldataload(0x0104), 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0) {
                                                                                            if iszero(iszero(0)) {
                                                                                                if iszero(eq(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(mload(0x40), 0x04); } else {
                                                                                                    mstore(0x02c0, 0x8baa579f00000000000000000000000000000000000000000000000000000000)
                                                                                                    if or(gt(add(mload(0x40), 0x40), 0xffffffffffffffff), lt(add(mload(0x40), 0x40), mload(0x40))) {
                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                        mstore(0x04, 0x41)
                                                                                                        mstore(0x40, add(mload(0x40), 0x40))
                                                                                                        mstore(0x02c0, and(calldataload(0x44), 0xffffffffffffffff))
                                                                                                        mstore(0x02e0, and(calldataload(0x64), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                                        mstore(0x20, 0x04)
                                                                                                        mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))
                                                                                                        mstore(0x20, sha3(0, 0x40))
                                                                                                        sstore(sha3(0, 0x40), or(or(and(0xffffffff00000000000000000000000000000000000000000000000000000000, sload(sha3(0, 0x40))), and(mload(mload(0x40)), 0xffffffffffffffff)), and(shl(0x40, mload(add(mload(0x40), 0x20))), 0xffffffffffffffffffffffffffffffffffffffff0000000000000000)))
                                                                                                        mstore(0x0300, and(calldataload(0x44), 0xffffffffffffffff))
                                                                                                        log3(mload(0x40), 0x20, 0x3cec0566535d67d6c92668517af0bf8a66cdc91d622dbb830fcc08e1bcf5d1df, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))
                                                                                                        if iszero(0) { revert(mload(0x40), 0x04); } else {
                                                                                                            mstore(0x02c0, 0x8baa579f00000000000000000000000000000000000000000000000000000000)
                                                                                                            mstore(0x02c0, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                                                            mstore(0x02e0, and(0xff, calldataload(0xc4)))
                                                                                                            mstore(0x0300, calldataload(0xe4))
                                                                                                            mstore(0x0320, calldataload(0x0104))
                                                                                                            mstore(0, 0)
                                                                                                            staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)
                                                                                                            if iszero(staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                                                                returndatacopy(mload(0x40), 0, returndatasize())
                                                                                                                if gt(calldataload(0x84), add(calldataload(0x84), 0x01)) { revert(0, 0); } else {
                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                    mstore(0x04, 0x11)
                                                                                                                    mstore(0x80, 0xf87d927100000000000000000000000000000000000000000000000000000000)
                                                                                                                    mstore(0x80, 0x276f9a6500000000000000000000000000000000000000000000000000000000)
                                                                                                                    mstore(0x80, 0x93b78c8800000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_8da5cb5b() public view returns (address)
            */
            case 0x8da5cb5b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_78e890ba() public view returns (uint256)
            */
            case 0x78e890ba {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0xa0, 0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f)
                        codecopy(0, 0x0e5f, 0x20)
                        mstore(0, mload(0))
                        mstore(0xc0, mload(0))
                        codecopy(0, 0x0dff, 0x20)
                        mstore(0, mload(0))
                        mstore(0xe0, mload(0))
                        mstore(0x0100, chainid())
                        mstore(0x0120, and(0xffffffffffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x03))))
                        mstore(0x80, 0xa0)
                        if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                            mstore(0x04, 0x41)
                            mstore(0x40, add(mload(0x40), 0xc0))
                            mstore(0x0140, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_84f4fc6a(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x84f4fc6a {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, caller())
                            mstore(0x20, 0x04)
                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                            mstore(0x20, sha3(0, 0x40))
                            sstore(sha3(0, 0x40), 0)
                            log3(0, 0, 0x744157ccffbd293a2e8644928cd7d23d650f869b88f72d7bfea8041b76ca6bec, caller(), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_7f608253(address arg0, uint256 arg1, bool arg2, uint256 arg3, uint256 arg4) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            */
            case 0x7f608253 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xa0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x44), and(calldataload(0x44), 0xff)) { revert(0, 0); } else {
                                mstore(0xa0, 0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f)
                                codecopy(0, 0x0e5f, 0x20)
                                mstore(0, mload(0))
                                mstore(0xc0, mload(0))
                                codecopy(0, 0x0dff, 0x20)
                                mstore(0, mload(0))
                                mstore(0xe0, mload(0))
                                mstore(0x0100, chainid())
                                mstore(0x0120, and(0xffffffffffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x03))))
                                mstore(0x80, 0xa0)
                                if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                    mstore(0x04, 0x41)
                                    mstore(0x40, add(mload(0x40), 0xc0))
                                    mstore(0x0160, 0x1901000000000000000000000000000000000000000000000000000000000000)
                                    mstore(0x0162, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                    mstore(0x0182, calldataload(0x24))
                                    mstore(0x0140, 0x42)
                                    if or(gt(add(mload(0x40), 0x80), 0xffffffffffffffff), lt(add(mload(0x40), 0x80), mload(0x40))) {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x41)
                                        mstore(0x40, add(mload(0x40), 0x80))
                                        if iszero(eq(and(0xff, calldataload(0x44)), 0x1b)) {
                                            if iszero(eq(and(0xff, calldataload(0x44)), 0x1b)) {
                                                if gt(calldataload(0x84), 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0) {
                                                    mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                    mstore(0x20, 0x04)
                                                    mstore(0, 0)
                                                    mstore(0x20, sha3(0, 0x40))
                                                    if iszero(and(0xffffffffffffffff, sload(sha3(0, 0x40)))) {
                                                        if gt(timestamp(), and(0xffffffffffffffff, sload(sha3(0, 0x40)))) { revert(mload(0x40), 0x04); } else {
                                                            mstore(0x01c0, 0)
                                                            return(mload(0x40), 0x20)
                                                            mstore(0x01c0, 0xda0700a200000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x01c0, 0xc5045f2200000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x01c0, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                            mstore(0x01e0, and(0xff, calldataload(0x44)))
                                                            mstore(0x0200, calldataload(0x64))
                                                            mstore(0x0220, calldataload(0x84))
                                                            mstore(0, 0)
                                                            staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)
                                                            if iszero(staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)) { revert(0, 0); } else {
                                                                returndatacopy(mload(0x40), 0, returndatasize())
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
            * @custom:signature    Unresolved_208e24fc() public pure returns (uint256)
            */
            case 0x208e24fc {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, 0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13)
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_747b8a1c(address arg0, uint256 arg1, uint256 arg2) public pure
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            */
            case 0x747b8a1c {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xa0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if gt(calldataload(0x24), 0xffffffffffffffff) { revert(0, 0); } else {
                                if iszero(slt(add(add(0x04, calldataload(0x24)), 0x1f), calldatasize())) {
                                    if gt(calldataload(add(0x04, calldataload(0x24))), 0xffffffffffffffff) {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x41)
                                        if or(lt(add(mload(0x40), and(add(0x3f, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(calldataload(add(0x04, calldataload(0x24))), 0x1f))), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)), mload(0x40)), gt(add(mload(0x40), and(add(0x3f, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(calldataload(add(0x04, calldataload(0x24))), 0x1f))), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)), 0xffffffffffffffff)) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x41)
                                            mstore(0x40, add(mload(0x40), and(add(0x3f, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(calldataload(add(0x04, calldataload(0x24))), 0x1f))), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0)))
                                            mstore(0x80, calldataload(add(0x04, calldataload(0x24))))
                                            if gt(add(add(add(0x04, calldataload(0x24)), calldataload(add(0x04, calldataload(0x24)))), 0x20), calldatasize()) {
                                                calldatacopy(add(mload(0x40), 0x20), add(add(0x04, calldataload(0x24)), 0x20), calldataload(add(0x04, calldataload(0x24))))
                                                mstore(0xa0, 0)
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
            
            /*
            * @custom:signature    Unresolved_c1e6613d(address arg0, address arg1) public view returns (address)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xc1e6613d {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                mstore(0x20, 0x04)
                                mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))
                                mstore(0x20, sha3(0, 0x40))
                                mstore(0x80, and(shr(0x40, sload(sha3(0, 0x40))), 0xffffffffffffffffffffffffffffffffffffffff))
                                return(mload(0x40), 0x20)
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_cf8fbec9(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xcf8fbec9 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02))) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x03, or(and(sload(0x03), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)))
                                codecopy(0, 0x0e3f, 0x20)
                                mstore(0, mload(0))
                                log2(0, 0, mload(0), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_5197a0d3(address arg0, uint256 arg1) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            */
            case 0x5197a0d3 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), iszero(iszero(calldataload(0x24)))) { revert(0, 0); } else {
                                if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02))) { revert(0, 0); } else {
                                    mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                    mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                    mstore(0x20, 0x07)
                                    sstore(sha3(0, 0x40), or(and(iszero(iszero(calldataload(0x24))), 0xff), and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00)))
                                    mstore(0x80, iszero(iszero(calldataload(0x24))))
                                    log2(mload(0x40), 0x20, 0xf09fcf47c21ca51acd6fd24e30b537dc39f0e5e021541cf1e4fa7f1013d60b99, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_f2f59776(address arg0, uint256 arg1) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            */
            case 0xf2f59776 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x06)
                            mstore(0, calldataload(0x24))
                            mstore(0x20, sha3(0, 0x40))
                            mstore(0x80, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_7ecebe00(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x7ecebe00 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x05)
                            mstore(0x80, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_3644e515() public view returns (uint256)
            */
            case 0x3644e515 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x01))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_7f6e9d4b(address arg0) public view returns (bool)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x7f6e9d4b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x07)
                            mstore(0x80, iszero(iszero(and(sload(sha3(0, 0x40)), 0xff))))
                            return(mload(0x40), 0x20)
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
                            if sub(caller(), and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x02, or(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x02))))
                                codecopy(0, 0x0e1f, 0x20)
                                mstore(0, mload(0))
                                log2(0, 0, mload(0), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_6525a680() public pure returns (uint256)
            */
            case 0x6525a680 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, 0xfce2fb41f9ff0457a0f012e62cfd6a7cff4e8439ae20008ab6979c740ba5a983)
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_b002b9fa(address arg0, bool arg1, uint64 arg2) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg2 ["uint64", "bytes8", "int64"]
            */
            case 0xb002b9fa {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffff)) { revert(0, 0); } else {
                                if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x03))) { revert(mload(0x40), 0x04); } else {
                                    mstore(0x80, 0x5c427cd900000000000000000000000000000000000000000000000000000000)
                                    if gt(timestamp(), and(0xffffffffffffffff, calldataload(0x44))) {
                                        mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                        mstore(0x20, 0x06)
                                        mstore(0, shr(0x08, calldataload(0x24)))
                                        mstore(0x20, sha3(0, 0x40))
                                        if and(sload(sha3(0, 0x40)), shl(and(calldataload(0x24), 0xff), 0x01)) { revert(mload(0x40), 0x04); } else {
                                            mstore(0x80, 0x756688fe00000000000000000000000000000000000000000000000000000000)
                                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                            mstore(0x20, 0x06)
                                            mstore(0, shr(0x08, calldataload(0x24)))
                                            mstore(0x20, sha3(0, 0x40))
                                            sstore(sha3(0, 0x40), or(sload(sha3(0, 0x40)), shl(and(calldataload(0x24), 0xff), 0x01)))
                                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                            mstore(0x20, 0x05)
                                            if iszero(lt(calldataload(0x24), sload(sha3(0, 0x40)))) {
                                                if gt(calldataload(0x24), add(calldataload(0x24), 0x01)) { revert(0, 0); } else {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x11)
                                                    mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                    mstore(0x20, 0x05)
                                                    sstore(sha3(0, 0x40), add(calldataload(0x24), 0x01))
                                                    mstore(0x80, 0xf87d927100000000000000000000000000000000000000000000000000000000)
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