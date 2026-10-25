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
            * @custom:signature    Unresolved_837fa3fd(address arg0) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x837fa3fd {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(0, 0); } else {
                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x1d, or(and(0xffffffffffffffffffffffffffffffffffffffff00, shl(0x08, calldataload(0x04))), and(0xffffffffffffffffffffff0000000000000000000000000000000000000000ff, sload(0x1d))))
                                log2(0, 0, 0x4d57218e59793e6845c36a961c3af7acfce8c54b13a697da231466fc265fdb61, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                return(0, 0)
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_3a21be03(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x3a21be03 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x15)
                            mstore(0xc0, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_53ac4b66() public view returns (uint256)
            */
            case 0x53ac4b66 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, sload(0x12))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_5ca4c0ea(uint32 arg0, address arg1, uint96 arg2, uint96 arg3, uint64 arg4) public payable returns (uint256)
            * @param                arg0 ["uint32", "bytes4", "int32"]
            * @param                arg1 ["address", "uint128", "bytes16", "int128"]
            * @param                arg2 ["uint96", "bytes12", "int96"]
            * @param                arg3 ["uint96", "bytes12", "int96"]
            * @param                arg4 ["uint64", "bytes8", "int64"]
            */
            case 0x5ca4c0ea {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xa0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffffffffffff)) { revert(0, 0); } else {
                                    if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffffffffffffffffffff)) { revert(0, 0); } else {
                                        if sub(calldataload(0x84), and(calldataload(0x84), 0xffffffffffffffff)) { revert(0, 0); } else {
                                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(mload(0x40), 0x04); } else {
                                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                                if iszero(lt(and(calldataload(0x04), 0xffffffff), and(sload(0x08), 0xffffffff))) {
                                                    if iszero(iszero(and(0xffffffffffffffffffffffffffffffff, calldataload(0x24)))) {
                                                        if iszero(iszero(and(calldataload(0x64), 0xffffffffffffffffffffffff))) {
                                                            if iszero(lt(and(calldataload(0x84), 0xffffffffffffffff), 0x0de0b6b3a7640000)) { revert(mload(0x40), 0x04); } else {
                                                                mstore(0xc0, 0xb0cb274d00000000000000000000000000000000000000000000000000000000)
                                                                mstore(0, and(calldataload(0x04), 0xffffffff))
                                                                mstore(0x20, 0x07)
                                                                sstore(add(sha3(0, 0x40), 0x02), or(and(sload(add(sha3(0, 0x40), 0x02)), 0xffffffffffffffffffffffffffffffff00000000000000000000000000000000), and(0xffffffffffffffffffffffffffffffff, calldataload(0x24))))
                                                                sstore(sha3(0, 0x40), or(and(0xffffffffffffffffffffffff000000000000000000000000, shl(0x60, calldataload(0x44))), and(0xffffffffffffffff000000000000000000000000ffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                                sstore(sha3(0, 0x40), or(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff000000000000000000000000), and(calldataload(0x64), 0xffffffffffffffffffffffff)))
                                                                sstore(add(sha3(0, 0x40), 0x01), or(and(0xffffffffffffffff0000000000000000000000000000000000000000000000, shl(0xb8, calldataload(0x84))), and(0xff0000000000000000ffffffffffffffffffffffffffffffffffffffffffffff, sload(add(sha3(0, 0x40), 0x01)))))
                                                                mstore(0xc0, and(0xffffffffffffffffffffffffffffffff, calldataload(0x24)))
                                                                mstore(0xe0, and(calldataload(0x44), 0xffffffffffffffffffffffff))
                                                                mstore(0x0100, and(calldataload(0x64), 0xffffffffffffffffffffffff))
                                                                mstore(0x0120, and(calldataload(0x84), 0xffffffffffffffff))
                                                                log2(mload(0x40), 0x80, 0x76a319771459e5329ebc7830ef30b80fc54d20327f8b4946a9539e53c46018c9, and(calldataload(0x04), 0xffffffff))
                                                                return(0, 0)
                                                                if iszero(and(calldataload(0x64), 0xffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                    mstore(0, and(calldataload(0x04), 0xffffffff))
                                                                    mstore(0x20, 0x07)
                                                                    sstore(add(sha3(0, 0x40), 0x02), or(and(sload(add(sha3(0, 0x40), 0x02)), 0xffffffffffffffffffffffffffffffff00000000000000000000000000000000), and(0xffffffffffffffffffffffffffffffff, calldataload(0x24))))
                                                                    sstore(sha3(0, 0x40), or(and(0xffffffffffffffffffffffff000000000000000000000000, shl(0x60, calldataload(0x44))), and(0xffffffffffffffff000000000000000000000000ffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                                    sstore(sha3(0, 0x40), or(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff000000000000000000000000), and(calldataload(0x64), 0xffffffffffffffffffffffff)))
                                                                    sstore(add(sha3(0, 0x40), 0x01), or(and(0xffffffffffffffff0000000000000000000000000000000000000000000000, shl(0xb8, calldataload(0x84))), and(0xff0000000000000000ffffffffffffffffffffffffffffffffffffffffffffff, sload(add(sha3(0, 0x40), 0x01)))))
                                                                    mstore(0xc0, and(0xffffffffffffffffffffffffffffffff, calldataload(0x24)))
                                                                    mstore(0xe0, and(calldataload(0x44), 0xffffffffffffffffffffffff))
                                                                    mstore(0x0100, and(calldataload(0x64), 0xffffffffffffffffffffffff))
                                                                    mstore(0x0120, and(calldataload(0x84), 0xffffffffffffffff))
                                                                    log2(mload(0x40), 0x80, 0x76a319771459e5329ebc7830ef30b80fc54d20327f8b4946a9539e53c46018c9, and(calldataload(0x04), 0xffffffff))
                                                                    return(0, 0)
                                                                    mstore(0xc0, 0xb0cb274d00000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0xc0, 0x67207a8800000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_e538b280(uint256 arg0, uint256 arg1, uint256 arg2) public payable returns (uint256)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            */
            case 0xe538b280 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(mload(0x40), 0x04); } else {
                            mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                            if iszero(gt(calldataload(0x04), 0x06f05b59d3b20000)) {
                                if iszero(gt(calldataload(0x04), 0x06f05b59d3b20000)) {
                                    if gt(calldataload(0x04), 0x06f05b59d3b20000) { revert(0, 0); } else {
                                        mstore(0xc0, 0xcd4e616700000000000000000000000000000000000000000000000000000000)
                                        sstore(0x17, calldataload(0x04))
                                        sstore(0x18, calldataload(0x24))
                                        sstore(0x19, calldataload(0x44))
                                        mstore(0xc0, calldataload(0x04))
                                        mstore(0xe0, calldataload(0x24))
                                        mstore(0x0100, calldataload(0x44))
                                        log1(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)), 0xe4af0531d4ba8c578b5076b042e4505372fb4f4986aea8ebf77f4ff1585e3e75)
                                        return(0, 0)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_b3060d36(uint256 arg0) public view returns (address)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0xb3060d36 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) { revert(0, 0); } else {
                        mstore(0, calldataload(0x04))
                        mstore(0x20, 0x0a)
                        mstore(0xc0, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_f728fc98(uint256 arg0) public view returns (uint256)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0xf728fc98 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) { revert(0, 0); } else {
                        mstore(0, calldataload(0x04))
                        mstore(0x20, 0x0d)
                        mstore(0xc0, sload(sha3(0, 0x40)))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_70f75ff5(uint256 arg0) public view returns (uint256)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x70f75ff5 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if iszero(or(eq(div(mul(calldataload(0x04), sload(0x05)), calldataload(0x04)), sload(0x05)), iszero(calldataload(0x04)))) { revert(0, 0); } else {
                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                            mstore(0x04, 0x11)
                            mstore(0xc0, mul(calldataload(0x04), sload(0x05)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_2d2451d1(uint32 arg0) public payable returns (uint256)
            * @param                arg0 ["uint32", "bytes4", "int32"]
            */
            case 0x2d2451d1 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            if iszero(eq(caller(), and(shr(0x10, sload(0)), 0xffffffffffffffffffffffffffffffffffffffff))) {
                                if iszero(eq(caller(), and(sload(0x01), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(mload(0x40), 0x04); } else {
                                    mstore(0xc0, 0x49199fb600000000000000000000000000000000000000000000000000000000)
                                    if iszero(lt(and(calldataload(0x04), 0xffffffff), and(sload(0x08), 0xffffffff))) {
                                        mstore(0, and(calldataload(0x04), 0xffffffff))
                                        mstore(0x20, 0x23)
                                        if and(sload(sha3(0, 0x40)), 0xff) { revert(mload(0x40), 0x04); } else {
                                            mstore(0xc0, 0x0d24081500000000000000000000000000000000000000000000000000000000)
                                            mstore(0, and(calldataload(0x04), 0xffffffff))
                                            mstore(0x20, 0x07)
                                            mstore(0xc0, 0xfb46648100000000000000000000000000000000000000000000000000000000)
                                            mstore(0xc4, and(shr(0xc0, sload(sha3(0, 0x40))), 0xffffffff))
                                            staticcall(gas(), and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x24, mload(0x40), 0x40)
                                            if iszero(staticcall(gas(), and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x24, mload(0x40), 0x40)) { revert(mload(0x40), returndatasize()); } else {
                                                returndatacopy(mload(0x40), 0, returndatasize())
                                                if staticcall(gas(), and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x24, mload(0x40), 0x40) {
                                                    sstore(sha3(0, 0x40), or(0x01, or(and(0xffffffffffffffff0000000000000000000000000000000000, shl(0x88, timestamp())), or(or(and(sload(sha3(0, 0x40)), 0xffffffffffffff00000000000000000000000000000000000000000000000000), 0), 0))))
                                                    mstore(0xc0, 0)
                                                    mstore(0xe0, 0)
                                                    mstore(0x0100, and(0xffffffffffffffff, timestamp()))
                                                    codecopy(0, 0x5935, 0x20)
                                                    mstore(0, mload(0))
                                                    log2(mload(0x40), 0x60, mload(0), and(calldataload(0x04), 0xffffffff))
                                                    return(0, 0)
                                                    if gt(0x40, returndatasize()) {
                                                        if or(lt(add(mload(0x40), 0x40), mload(0x40)), gt(add(mload(0x40), 0x40), 0xffffffffffffffff)) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            mstore(0x40, add(mload(0x40), 0x40))
                                                            if slt(sub(add(mload(0x40), 0x40), mload(0x40)), 0x40) { revert(0, 0); } else {
                                                                codecopy(0, 0x5935, 0x20)
                                                                mstore(0, mload(0))
                                                                if sub(mload(mload(0x40)), and(mload(mload(0x40)), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                                    mstore(0xc0, 0x67207a8800000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_48bde20c(address arg0) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x48bde20c {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(0, 0); } else {
                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x01, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x01))))
                                log2(0, 0, 0x6b3ffd50ed0810416007b5dbbae587b9d8801c50bf8065cda8eb82011bed314e, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                return(0, 0)
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_a69a2ad1() public view returns (address)
            */
            case 0xa69a2ad1 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x16), 0xffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_ae69b95b(uint256 arg0) public payable returns (uint256)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0xae69b95b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), iszero(iszero(calldataload(0x04)))) { revert(0, 0); } else {
                            if iszero(eq(caller(), and(shr(0x10, sload(0)), 0xffffffffffffffffffffffffffffffffffffffff))) {
                                if eq(caller(), and(sload(0x01), 0xffffffffffffffffffffffffffffffffffffffff)) {
                                    if iszero(eq(caller(), and(sload(0x01), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(mload(0x40), 0x04); } else {
                                        mstore(0xc0, 0x49199fb600000000000000000000000000000000000000000000000000000000)
                                        sstore(0x1d, or(and(iszero(iszero(calldataload(0x04))), 0xff), and(sload(0x1d), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00)))
                                        mstore(0xc0, iszero(iszero(calldataload(0x04))))
                                        log1(mload(0x40), 0x20, 0xa4abec9259618fb7d014c89824b2887f61e3ab2b382d4a48a42dfde43cec5d6e)
                                        return(0, 0)
                                        if iszero(calldataload(0x04)) { revert(0, 0); } else {
                                            sstore(0x1d, or(and(iszero(iszero(calldataload(0x04))), 0xff), and(sload(0x1d), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00)))
                                            mstore(0xc0, iszero(iszero(calldataload(0x04))))
                                            log1(mload(0x40), 0x20, 0xa4abec9259618fb7d014c89824b2887f61e3ab2b382d4a48a42dfde43cec5d6e)
                                            return(0, 0)
                                            mstore(0xc0, 0x49199fb600000000000000000000000000000000000000000000000000000000)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_cd2d3811(address arg0) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xcd2d3811 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(mload(0x40), 0x04); } else {
                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                if iszero(iszero(and(sload(0x1f), 0xffffffffffffffffffffffffffffffffffffffff))) {
                                    if iszero(eq(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), and(sload(0x1f), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0); } else {
                                        mstore(0xc0, 0x612a352200000000000000000000000000000000000000000000000000000000)
                                        sstore(0x1f, or(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x1f))))
                                        log2(0, 0, 0xbcd09d92c26e8078d8be2b8380bb7d1ab324d0a9ae6743e158ad8d7f734a84ba, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                        return(0, 0)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_32faa570(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x32faa570 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x22)
                            mstore(0xc0, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_7b9f5264() public payable returns (uint256)
            */
            case 0x7b9f5264 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1f))) {
                            if iszero(and(sload(0x1a), 0xffffffffffffffffffffffffffffffff)) {
                                sstore(0x1a, and(0xffffffffffffffffffffffffffffffff00000000000000000000000000000000, sload(0x1a)))
                                if sload(0x12) {
                                    if iszero(lt(0, and(sload(0x1a), 0xffffffffffffffffffffffffffffffff))) {
                                        if 0 {
                                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1f))))
                                            mstore(0x20, 0x09)
                                            if gt(sload(sha3(0, 0x40)), add(sload(sha3(0, 0x40)), 0)) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x11)
                                                sstore(sha3(0, 0x40), add(sload(sha3(0, 0x40)), 0))
                                                if gt(add(and(0xffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffff, sload(0x16))), 0), 0xffffffffffffffffffffffffffffffff) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x11)
                                                    sstore(0x16, or(and(add(and(0xffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffff, sload(0x16))), 0), 0xffffffffffffffffffffffffffffffff), and(sload(0x16), 0xffffffffffffffffffffffffffffffff00000000000000000000000000000000)))
                                                    if lt(0, and(sload(0x1a), 0xffffffffffffffffffffffffffffffff)) {
                                                        if iszero(extcodesize(0xac8ba1307815f74bd13d4d039c96f7b97e81aa49)) { revert(0, 0); } else {
                                                            mstore(0xc0, 0x18958ce200000000000000000000000000000000000000000000000000000000)
                                                            mstore(0xc4, 0x0f)
                                                            mstore(0xe4, and(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1f)), 0xffffffffffffffffffffffffffffffffffffffff))
                                                            mstore(0x0104, sub(and(sload(0x1a), 0xffffffffffffffffffffffffffffffff), 0))
                                                            delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0x64, mload(0x40), 0)
                                                            if iszero(delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0x64, mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                                returndatacopy(mload(0x40), 0, returndatasize())
                                                                if delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0x64, mload(0x40), 0) {
                                                                    mstore(0xc0, and(sload(0x1a), 0xffffffffffffffffffffffffffffffff))
                                                                    log2(mload(0x40), 0x20, 0x128758146ec8c0baf9d649d8fd380afd833d72d1fba6ffb3cf2b0d9043645351, and(0xffffffffffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1f))))
                                                                    if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x06))) {
                                                                        mstore(0xc0, 0xae74570300000000000000000000000000000000000000000000000000000000)
                                                                        staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x06)), mload(0x40), 0x04, mload(0x40), 0x20)
                                                                        if iszero(staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x06)), mload(0x40), 0x04, mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                            returndatacopy(mload(0x40), 0, returndatasize())
                                                                            if staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x06)), mload(0x40), 0x04, mload(0x40), 0x20) {
                                                                                if iszero(0) {
                                                                                    if iszero(extcodesize(and(sload(0x06), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0); } else {
                                                                                        mstore(0xc0, 0xc218c67600000000000000000000000000000000000000000000000000000000)
                                                                                        mstore(0xc4, 0)
                                                                                        call(gas(), and(sload(0x06), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), 0x24, mload(0x40), 0)
                                                                                        if iszero(call(gas(), and(sload(0x06), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), 0x24, mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                                                            returndatacopy(mload(0x40), 0, returndatasize())
                                                                                            if call(gas(), and(sload(0x06), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), 0x24, mload(0x40), 0) {
                                                                                                if gt(mload(0x40), 0xffffffffffffffff) {
                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                    mstore(0x04, 0x41)
                                                                                                    return(0, 0)
                                                                                                    if gt(0x20, returndatasize()) {
                                                                                                        if or(lt(add(mload(0x40), 0x20), mload(0x40)), gt(add(mload(0x40), 0x20), 0xffffffffffffffff)) {
                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                            mstore(0x04, 0x41)
                                                                                                            mstore(0x40, add(mload(0x40), 0x20))
                                                                                                            if slt(sub(add(mload(0x40), 0x20), mload(0x40)), 0x20) { revert(0, 0); } else {
                                                                                                                if iszero(mload(mload(0x40))) {
                                                                                                                    return(0, 0)
                                                                                                                    if iszero(extcodesize(and(sload(0x06), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0); } else {
                                                                                                                        mstore(0xe0, 0xc218c67600000000000000000000000000000000000000000000000000000000)
                                                                                                                        mstore(0xe4, mload(mload(0x40)))
                                                                                                                        call(gas(), and(sload(0x06), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), 0x24, mload(0x40), 0)
                                                                                                                        if iszero(call(gas(), and(sload(0x06), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), 0x24, mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                                                                                            returndatacopy(mload(0x40), 0, returndatasize())
                                                                                                                            if call(gas(), and(sload(0x06), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), 0x24, mload(0x40), 0) {
                                                                                                                            }
                                                                                                                        }
                                                                                                                        if gt(mload(0x40), 0xffffffffffffffff) {
                                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0x04, 0x41)
                                                                                                                            if gt(and(sload(0x16), 0xffffffffffffffffffffffffffffffff), add(and(sload(0x16), 0xffffffffffffffffffffffffffffffff), shr(0x80, sload(0x16)))) { revert(mload(0x40), 0x04); } else {
                                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                mstore(0x04, 0x11)
                                                                                                                                mstore(0xc0, 0x64cd178800000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_6d142da1(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x6d142da1 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e))) {
                                mstore(0xc0, 0xc1a9a50800000000000000000000000000000000000000000000000000000000)
                                mstore(0xc4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20)
                                if iszero(staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                    returndatacopy(mload(0x40), 0, returndatasize())
                                    if staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20) {
                                        if iszero(0) {
                                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                            mstore(0x20, 0x21)
                                            if iszero(iszero(iszero(sload(sha3(0, 0x40))))) {
                                                if iszero(gt(number(), and(0xffffffff, and(shr(0x80, sload(sha3(0, 0x40))), 0xffffffff)))) { revert(mload(0x40), 0x04); } else {
                                                    mstore(0xc0, 0xd26ffacb00000000000000000000000000000000000000000000000000000000)
                                                    mstore(0xe0, 0)
                                                    mstore(0x0100, 0)
                                                    mstore(0xc0, 0x40)
                                                    if or(lt(add(mload(0x40), 0x60), mload(0x40)), gt(add(mload(0x40), 0x60), 0xffffffffffffffff)) {
                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x04, 0x41)
                                                        mstore(0x40, add(mload(0x40), 0x60))
                                                        staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)
                                                        if iszero(returndatasize()) {
                                                            if iszero(iszero(staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0))) {
                                                                if iszero(staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x04); } else {
                                                                    mstore(0x0120, 0x0a9e018000000000000000000000000000000000000000000000000000000000)
                                                                    if slt(sub(add(0x60, mload(0x60)), 0x60), 0x60) {
                                                                        if sub(mload(0x80), and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                                            if lt(mload(0x60), 0x60) { revert(mload(0x40), 0x04); } else {
                                                                                mstore(0x0120, 0x0a9e018000000000000000000000000000000000000000000000000000000000)
                                                                                if gt(returndatasize(), 0xffffffffffffffff) {
                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                    mstore(0x04, 0x41)
                                                                                    if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), 0xffffffffffffffff)) {
                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                        mstore(0x04, 0x41)
                                                                                        mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))))
                                                                                        mstore(0x0120, returndatasize())
                                                                                        returndatacopy(add(mload(0x40), 0x20), 0, returndatasize())
                                                                                        if iszero(iszero(staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0))) {
                                                                                            if iszero(staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x04); } else {
                                                                                                mstore(0x0160, 0x0a9e018000000000000000000000000000000000000000000000000000000000)
                                                                                                mstore(0xc0, 0x0984a61700000000000000000000000000000000000000000000000000000000)
                                                                                                mstore(0xc0, 0x0576e00500000000000000000000000000000000000000000000000000000000)
                                                                                                if gt(0x20, returndatasize()) { revert(0, 0); } else {
                                                                                                }
                                                                                                mstore(0xc0, 0x967d697b00000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_fb9f1009(uint32 arg0) public pure
            * @param                arg0 ["uint32", "bytes4", "int32"]
            */
            case 0xfb9f1009 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            mstore(0xc0, 0xd9d193d300000000000000000000000000000000000000000000000000000000)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_599dc539(uint256 arg0) public view
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x599dc539 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if gt(calldataload(0x04), 0xffffffffffffffff) { revert(0, 0); } else {
                            if iszero(slt(add(add(0x04, calldataload(0x04)), 0x1f), calldatasize())) {
                                if gt(calldataload(add(0x04, calldataload(0x04))), 0xffffffffffffffff) { revert(0, 0); } else {
                                    if gt(add(add(shl(0x05, calldataload(add(0x04, calldataload(0x04)))), add(0x04, calldataload(0x04))), 0x20), calldatasize()) {
                                        if gt(and(sload(0x08), 0xffffffff), 0xffffffffffffffff) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x41)
                                            if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, shl(0x05, and(sload(0x08), 0xffffffff))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, shl(0x05, and(sload(0x08), 0xffffffff))), 0x1f))), 0xffffffffffffffff)) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, shl(0x05, and(sload(0x08), 0xffffffff))), 0x1f))))
                                                mstore(0xc0, and(sload(0x08), 0xffffffff))
                                                if gt(and(sload(0x08), 0xffffffff), 0xffffffffffffffff) { revert(0, 0); } else {
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

            /*
            * @custom:signature    Unresolved_c88bbcf3(uint96 arg0, uint96 arg1, uint32 arg2, uint32 arg3, address arg4, uint64 arg5, uint64 arg6, address arg7, uint64 arg8) public payable
            * @param                arg0 ["uint96", "bytes12", "int96"]
            * @param                arg1 ["uint96", "bytes12", "int96"]
            * @param                arg2 ["uint32", "bytes4", "int32"]
            * @param                arg3 ["uint32", "bytes4", "int32"]
            * @param                arg4 ["address", "uint120", "bytes15", "int120"]
            * @param                arg5 ["uint64", "bytes8", "int64"]
            * @param                arg6 ["uint64", "bytes8", "int64"]
            * @param                arg7 ["address", "uint128", "bytes16", "int128"]
            * @param                arg8 ["uint64", "bytes8", "int64"]
            */
            case 0xc88bbcf3 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x0120) {
                        if sgt(0x0100, add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize())) {
                            if sub(calldataload(0x0104), and(0xffffffffffffffff, calldataload(0x0104))) { revert(0, 0); } else {
                                if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(mload(0x40), 0x04); } else {
                                    mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                    if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffff)) { revert(0, 0); } else {
                                        if iszero(and(calldataload(0x64), 0xffffffff)) {
                                            if sub(calldataload(0xa4), and(calldataload(0xa4), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                if iszero(lt(and(calldataload(0xa4), 0xffffffffffffffff), 0x0de0b6b3a7640000)) { revert(mload(0x40), 0x04); } else {
                                                    mstore(0xc0, 0xb0cb274d00000000000000000000000000000000000000000000000000000000)
                                                    if sub(calldataload(0xc4), and(calldataload(0xc4), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                        if iszero(lt(and(calldataload(0xc4), 0xffffffffffffffff), 0x0de0b6b3a7640000)) { revert(mload(0x40), 0x04); } else {
                                                            mstore(0xc0, 0xb0cb274d00000000000000000000000000000000000000000000000000000000)
                                                            if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                if iszero(and(calldataload(0x04), 0xffffffffffffffffffffffff)) {
                                                                    if sub(calldataload(0xe4), and(calldataload(0xe4), 0xffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                        if iszero(and(calldataload(0xe4), 0xffffffffffffffffffffffffffffffff)) {
                                                                            if sub(calldataload(0x84), and(calldataload(0x84), 0xffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                                if iszero(and(calldataload(0x84), 0xffffffffffffffffffffffffffffff)) {
                                                                                    if iszero(and(0xffffffffffffffff, calldataload(0x0104))) {
                                                                                        if eq(and(sload(0x08), 0xffffffff), 0xffffffff) {
                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                            mstore(0x04, 0x11)
                                                                                            sstore(0x08, or(and(0xffffffff, add(and(sload(0x08), 0xffffffff), 0x01)), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffff00000000, sload(0x08))))
                                                                                            mstore(0, and(sload(0x08), 0xffffffff))
                                                                                            mstore(0x20, 0x07)
                                                                                            if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                                                sstore(sha3(0, 0x40), or(and(0xffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffffffffffffffffffff000000000000000000000000, sload(sha3(0, 0x40)))))
                                                                                                if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                                                    sstore(sha3(0, 0x40), or(and(0xffffffffffffffffffffffff000000000000000000000000, shl(0x60, calldataload(0x24))), and(0xffffffffffffffff000000000000000000000000ffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                                                                    if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffff)) { revert(0, 0); } else {
                                                                                                        sstore(sha3(0, 0x40), or(and(0xffffffff000000000000000000000000000000000000000000000000, shl(0xc0, calldataload(0x44))), and(0xffffffff00000000ffffffffffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                                                                        if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffff)) { revert(0, 0); } else {
                                                                                                            sstore(sha3(0, 0x40), or(and(0xffffffff00000000000000000000000000000000000000000000000000000000, shl(0xe0, calldataload(0x64))), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                                                                            if sub(calldataload(0x84), and(calldataload(0x84), 0xffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                                                                if sub(calldataload(0xa4), and(calldataload(0xa4), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                                                                                    sstore(add(sha3(0, 0x40), 0x01), or(or(and(0xffffffffffffffffff0000000000000000000000000000000000000000000000, sload(add(sha3(0, 0x40), 0x01))), and(0xffffffffffffffffffffffffffffff, calldataload(0x84))), and(shl(0x78, calldataload(0xa4)), 0xffffffffffffffff000000000000000000000000000000)))
                                                                                                                    if sub(calldataload(0xc4), and(calldataload(0xc4), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                                                                                        sstore(add(sha3(0, 0x40), 0x01), or(and(0xffffffffffffffff0000000000000000000000000000000000000000000000, shl(0xb8, calldataload(0xc4))), and(0xff0000000000000000ffffffffffffffffffffffffffffffffffffffffffffff, sload(add(sha3(0, 0x40), 0x01)))))
                                                                                                                        if sub(calldataload(0xe4), and(calldataload(0xe4), 0xffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                                                                            mstore(0xc0, 0x924d25e600000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0xc0, 0xb0cb274d00000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0xc0, 0xb0cb274d00000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0xc0, 0xb0cb274d00000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0xc0, 0xb0cb274d00000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_c10f1a75() public view returns (address)
            */
            case 0xc10f1a75 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x1e), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_2dcc7fce(uint256 arg0) public view returns (uint256)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x2dcc7fce {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if iszero(or(eq(div(mul(calldataload(0x04), sload(0x03)), calldataload(0x04)), sload(0x03)), iszero(calldataload(0x04)))) {
                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                            mstore(0x04, 0x11)
                            if iszero(sload(0x05)) { revert(0, 0); } else {
                                mstore(0xc0, div(mul(calldataload(0x04), sload(0x03)), sload(0x05)))
                                return(mload(0x40), 0x20)
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x12)
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_53e23e2e() public view returns (bool)
            */
            case 0x53e23e2e {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, iszero(iszero(and(sload(0x1d), 0xff))))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_827ad94c(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable returns (bytes memory)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            */
            case 0x827ad94c {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x80) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0xc0, 0x32db40c900000000000000000000000000000000000000000000000000000000)
                            mstore(0xc4, 0x0f)
                            mstore(0xe4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x0104, calldataload(0x24))
                            mstore(0x0124, calldataload(0x44))
                            mstore(0x0144, calldataload(0x64))
                            delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0xa4, mload(0x40), 0x60)
                            if iszero(delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0xa4, mload(0x40), 0x60)) { revert(mload(0x40), returndatasize()); } else {
                                returndatacopy(mload(0x40), 0, returndatasize())
                                if delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0xa4, mload(0x40), 0x60) {
                                    mstore(0xc0, 0)
                                    mstore(0xe0, 0)
                                    mstore(0x0100, 0)
                                    return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                    if gt(0x60, returndatasize()) {
                                        if or(lt(add(mload(0x40), 0x60), mload(0x40)), gt(add(mload(0x40), 0x60), 0xffffffffffffffff)) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x41)
                                            mstore(0x40, add(mload(0x40), 0x60))
                                            if slt(sub(add(mload(0x40), 0x60), mload(0x40)), 0x60) { revert(0, 0); } else {
                                                mstore(0x0120, mload(mload(0x40)))
                                                mstore(0x0140, mload(add(mload(0x40), 0x20)))
                                                mstore(0x0160, mload(add(mload(0x40), 0x40)))
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

            /*
            * @custom:signature    Unresolved_060447aa(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x060447aa {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(0, 0); } else {
                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x25, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x25))))
                                log2(0, 0, 0xc76a9da20bd06b6b26d0826dab481a66785c609c15fae99817a557e61229e9c5, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_2362f4de(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x2362f4de {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(mload(0x40), 0x04); } else {
                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e))) {
                                    mstore(0xc0, 0xc1a9a50800000000000000000000000000000000000000000000000000000000)
                                    mstore(0xc4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                    staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20)
                                    if iszero(staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                        returndatacopy(mload(0x40), 0, returndatasize())
                                        if staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20) {
                                            if iszero(0) {
                                                mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                mstore(0x20, 0x21)
                                                if iszero(sload(sha3(0, 0x40))) { revert(mload(0x40), 0x04); } else {
                                                    mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                    mstore(0x20, 0x21)
                                                    sstore(sha3(0, 0x40), 0)
                                                    log3(0, 0, 0x28f3adb5fa23ae5c83c811e67caf2ec192a816e4ef898c7f90d1484f65a9717e, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), 0)
                                                    mstore(0xc0, 0x0984a61700000000000000000000000000000000000000000000000000000000)
                                                    mstore(0xc0, 0x0576e00500000000000000000000000000000000000000000000000000000000)
                                                    if gt(0x20, returndatasize()) {
                                                        if or(lt(add(mload(0x40), 0x20), mload(0x40)), gt(add(mload(0x40), 0x20), 0xffffffffffffffff)) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            mstore(0x40, add(mload(0x40), 0x20))
                                                            if slt(sub(add(mload(0x40), 0x20), mload(0x40)), 0x20) { revert(0, 0); } else {
                                                                if sub(mload(mload(0x40)), and(mload(mload(0x40)), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                    mstore(0xc0, 0x967d697b00000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_dcab7f6a(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xdcab7f6a {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x14)
                            mstore(0xc0, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_01ad056f() public view returns (uint256)
            */
            case 0x01ad056f {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0xc0, shr(0x80, sload(0x16)))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_18715c9a() public payable returns (uint256)
            */
            case 0x18715c9a {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x06))) {
                            mstore(0xc0, 0xae74570300000000000000000000000000000000000000000000000000000000)
                            staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x06)), mload(0x40), 0x04, mload(0x40), 0x20)
                            if iszero(staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x06)), mload(0x40), 0x04, mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                returndatacopy(mload(0x40), 0, returndatasize())
                                if staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x06)), mload(0x40), 0x04, mload(0x40), 0x20) {
                                    mstore(0xc0, 0)
                                    return(mload(0x40), 0x20)
                                    if gt(0x20, returndatasize()) {
                                        if or(lt(add(mload(0x40), 0x20), mload(0x40)), gt(add(mload(0x40), 0x20), 0xffffffffffffffff)) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x41)
                                            mstore(0x40, add(mload(0x40), 0x20))
                                            if slt(sub(add(mload(0x40), 0x20), mload(0x40)), 0x20) { revert(0, 0); } else {
                                                mstore(0xe0, mload(mload(0x40)))
                                                return(mload(0x40), 0x20)
                                                mstore(0xc0, 0)
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

            /*
            * @custom:signature    Unresolved_7f99545a(uint256 arg0) public view
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x7f99545a {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, caller()))
                        mstore(0x20, 0x22)
                        if iszero(gt(number(), sload(sha3(0, 0x40)))) { revert(mload(0x40), 0x04); } else {
                            mstore(0xc0, 0x4f57ffae00000000000000000000000000000000000000000000000000000000)
                            if iszero(or(eq(div(mul(calldataload(0x04), sload(0x03)), calldataload(0x04)), sload(0x03)), iszero(calldataload(0x04)))) { revert(0, 0); } else {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x11)
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_9274682e() public view returns (address)
            */
            case 0x9274682e {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x1b), 0xffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_8da5cb5b() public view returns (address)
            */
            case 0x8da5cb5b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0))))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_9d47d4d3() public view returns (address)
            */
            case 0x9d47d4d3 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x59), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_c43fbc8c() public view returns (bool)
            */
            case 0xc43fbc8c {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x04), 0xff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_c0c53b8b(address arg0, address arg1, address arg2) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xc0c53b8b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))) { revert(0, 0); } else {
                                if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                    if and(sload(0), 0xff) {
                                        if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                            if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                                sstore(0, or(and(sload(0), 0xffffffffffffffffffff0000000000000000000000000000000000000000ffff), and(shl(0x10, calldataload(0x04)), 0xffffffffffffffffffffffffffffffffffffffff0000)))
                                                sstore(0x01, or(and(sload(0x01), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                sstore(0x02, or(and(sload(0x02), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))))
                                                sstore(0x17, 0x470de4df820000)
                                                sstore(0x18, 0x470de4df820000)
                                                sstore(0x19, 0x470de4df820000)
                                                sstore(0x1c, 0x0de0b6b3a7640000)
                                                mstore(0xc0, 0x313ce56700000000000000000000000000000000000000000000000000000000)
                                                staticcall(gas(), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x04, mload(0x40), 0x20)
                                                if staticcall(gas(), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x04, mload(0x40), 0x20) {
                                                    if staticcall(gas(), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x04, mload(0x40), 0x20) {
                                                        if gt(0x06, 0x12) { revert(mload(0x40), 0x04); } else {
                                                            mstore(0xc0, 0x6a42631500000000000000000000000000000000000000000000000000000000)
                                                            sstore(0x03, 0xe8d4a51000)
                                                            if lt(0x10, 0x06) {
                                                                sstore(0x04, or(and(sload(0x04), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00), 0x06))
                                                                sstore(0x05, 0xe8d4a51000)
                                                                sstore(0x11, 0x01)
                                                                codecopy(0, 0x5915, 0x20)
                                                                mstore(0, mload(0))
                                                                log2(0, 0, mload(0), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                                                    return(0, 0)
                                                                    sstore(0, or(and(0xffffffffffffffffffff000000000000000000000000000000000000000000ff, sload(0)), and(shl(0x10, calldataload(0x04)), 0xffffffffffffffffffffffffffffffffffffffff0000)))
                                                                    return(0, 0)
                                                                    if gt(0x20, returndatasize()) {
                                                                        if or(lt(add(mload(0x40), 0x20), mload(0x40)), gt(add(mload(0x40), 0x20), 0xffffffffffffffff)) {
                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0x04, 0x41)
                                                                            mstore(0x40, add(mload(0x40), 0x20))
                                                                            if slt(sub(add(mload(0x40), 0x20), mload(0x40)), 0x20) { revert(0, 0); } else {
                                                                                if sub(mload(mload(0x40)), and(mload(mload(0x40)), 0xff)) {
                                                                                    if staticcall(gas(), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x04, mload(0x40), 0x20) { revert(0, 0); } else {
                                                                                    }
                                                                                    sstore(0, or(0x0101, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000, sload(0))))
                                                                                    sstore(0, or(and(sload(0), 0xffffffffffffffffffff0000000000000000000000000000000000000000ffff), and(shl(0x10, calldataload(0x04)), 0xffffffffffffffffffffffffffffffffffffffff0000)))
                                                                                    sstore(0x01, or(and(sload(0x01), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                                                    sstore(0x02, or(and(sload(0x02), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))))
                                                                                    sstore(0x17, 0x470de4df820000)
                                                                                    sstore(0x18, 0x470de4df820000)
                                                                                    sstore(0x19, 0x470de4df820000)
                                                                                    sstore(0x1c, 0x0de0b6b3a7640000)
                                                                                    mstore(0xc0, 0x313ce56700000000000000000000000000000000000000000000000000000000)
                                                                                    staticcall(gas(), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x04, mload(0x40), 0x20)
                                                                                    if staticcall(gas(), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x04, mload(0x40), 0x20) {
                                                                                        if staticcall(gas(), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x04, mload(0x40), 0x20) {
                                                                                        }
                                                                                        if gt(0x20, returndatasize()) { revert(mload(0x40), 0x04); } else {
                                                                                        }
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

            /*
            * @custom:signature    Unresolved_fbddd751(address arg0) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xfbddd751 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(0, 0); } else {
                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x1e, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x1e))))
                                log2(0, 0, 0x06fb15b3928ea45c766cc3b08212ecc978647d51cf9551cdd13a70d6a00197c7, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                return(0, 0)
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_ddc63262(uint256 arg0) public view
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0xddc63262 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if iszero(sload(0x12)) {
                            if gt(and(sload(0x16), 0xffffffffffffffffffffffffffffffff), add(and(sload(0x16), 0xffffffffffffffffffffffffffffffff), shr(0x80, sload(0x16)))) { revert(0, 0); } else {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x11)
                                mstore(0xc0, 0x75e52f4f00000000000000000000000000000000000000000000000000000000)
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_f92576b1(address arg0) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xf92576b1 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(mload(0x40), 0x04); } else {
                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                if iszero(shr(0x80, sload(0x1a))) {
                                    sstore(0x1a, and(0xffffffffffffffffffffffffffffffff, sload(0x1a)))
                                    if sload(0x12) {
                                        if iszero(lt(0, shr(0x80, sload(0x1a)))) {
                                            if 0 {
                                                mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                mstore(0x20, 0x09)
                                                if gt(sload(sha3(0, 0x40)), add(sload(sha3(0, 0x40)), 0)) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x11)
                                                    sstore(sha3(0, 0x40), add(sload(sha3(0, 0x40)), 0))
                                                    if gt(add(and(0xffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffff, sload(0x16))), 0), 0xffffffffffffffffffffffffffffffff) {
                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x04, 0x11)
                                                        sstore(0x16, or(and(add(and(0xffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffff, sload(0x16))), 0), 0xffffffffffffffffffffffffffffffff), and(sload(0x16), 0xffffffffffffffffffffffffffffffff00000000000000000000000000000000)))
                                                        if lt(0, shr(0x80, sload(0x1a))) {
                                                            if iszero(extcodesize(0xac8ba1307815f74bd13d4d039c96f7b97e81aa49)) { revert(0, 0); } else {
                                                                mstore(0xc0, 0x18958ce200000000000000000000000000000000000000000000000000000000)
                                                                mstore(0xc4, 0x0f)
                                                                mstore(0xe4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                mstore(0x0104, sub(shr(0x80, sload(0x1a)), 0))
                                                                delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0x64, mload(0x40), 0)
                                                                if iszero(delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0x64, mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                                    returndatacopy(mload(0x40), 0, returndatasize())
                                                                    if delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0x64, mload(0x40), 0) {
                                                                        mstore(0xc0, shr(0x80, sload(0x1a)))
                                                                        log2(mload(0x40), 0x20, 0x4f162e5dbc97f219b96d1d1766c4851bf12dcd19b02a872933e8c2343cf22d80, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                        return(0, 0)
                                                                        if gt(mload(0x40), 0xffffffffffffffff) {
                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0x04, 0x41)
                                                                            mstore(0x40, mload(0x40))
                                                                            mstore(0xc0, shr(0x80, sload(0x1a)))
                                                                            log2(mload(0x40), 0x20, 0x4f162e5dbc97f219b96d1d1766c4851bf12dcd19b02a872933e8c2343cf22d80, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                            return(0, 0)
                                                                            mstore(0xc0, shr(0x80, sload(0x1a)))
                                                                            log2(mload(0x40), 0x20, 0x4f162e5dbc97f219b96d1d1766c4851bf12dcd19b02a872933e8c2343cf22d80, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                            return(0, 0)
                                                                            if gt(and(sload(0x16), 0xffffffffffffffffffffffffffffffff), add(and(sload(0x16), 0xffffffffffffffffffffffffffffffff), shr(0x80, sload(0x16)))) { revert(0, 0); } else {
                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                mstore(0x04, 0x11)
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
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_ff3bc415() public pure returns (uint256)
            */
            case 0xff3bc415 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, 0x40)
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_cb163b03(uint32 arg0) public view returns (bytes memory)
            * @param                arg0 ["uint32", "bytes4", "int32"]
            */
            case 0xcb163b03 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffff))
                            mstore(0x20, 0x24)
                            mstore(0xc0, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffff))
                            mstore(0xe0, and(shr(0x60, sload(sha3(0, 0x40))), 0xffffffffffffffffffffffff))
                            mstore(0x0100, and(sload(add(sha3(0, 0x40), 0x01)), 0xffffffffffffffffffffffffffffffff))
                            mstore(0x0120, shr(0x80, sload(add(sha3(0, 0x40), 0x01))))
                            mstore(0x0140, shr(0xc0, sload(sha3(0, 0x40))))
                            return(mload(0x40), 0xa0)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_31a39849() public view returns (uint256)
            */
            case 0x31a39849 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, sload(0x05))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_afdf6702() public view returns (address)
            */
            case 0xafdf6702 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x1a), 0xffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_dc8a47ef(uint32 arg0) public view returns (bytes memory)
            * @param                arg0 ["uint32", "bytes4", "int32"]
            */
            case 0xdc8a47ef {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffff))
                            mstore(0x20, 0x07)
                            mstore(0xc0, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffff))
                            mstore(0xe0, and(shr(0x60, sload(sha3(0, 0x40))), 0xffffffffffffffffffffffff))
                            mstore(0x0100, and(shr(0xc0, sload(sha3(0, 0x40))), 0xffffffff))
                            mstore(0x0120, shr(0xe0, sload(sha3(0, 0x40))))
                            mstore(0x0140, and(sload(add(sha3(0, 0x40), 0x01)), 0xffffffffffffffffffffffffffffff))
                            mstore(0x0160, and(shr(0x78, sload(add(sha3(0, 0x40), 0x01))), 0xffffffffffffffff))
                            mstore(0x0180, and(shr(0xb8, sload(add(sha3(0, 0x40), 0x01))), 0xffffffffffffffff))
                            mstore(0x01a0, and(sload(add(sha3(0, 0x40), 0x02)), 0xffffffffffffffffffffffffffffffff))
                            return(mload(0x40), 0x0100)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_551306f3(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x551306f3 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x13)
                            mstore(0xc0, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_ec6783f0(address arg0, uint32 arg1, uint256 arg2, address arg3, uint32 arg4, uint256 arg5, uint256 arg6, uint64 arg7, bool arg8, uint256 arg9, uint256 arg10) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint32", "bytes4", "int32"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["address", "uint128", "bytes16", "int128"]
            * @param                arg4 ["uint32", "bytes4", "int32"]
            * @param                arg5 ["uint256", "bytes32", "int256"]
            * @param                arg6 ["uint256", "bytes32", "int256"]
            * @param                arg7 ["uint64", "bytes8", "int64"]
            * @param                arg8 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg9 ["uint256", "bytes32", "int256"]
            * @param                arg10 ["uint256", "bytes32", "int256"]
            */
            case 0xec6783f0 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x0160) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x44), iszero(iszero(calldataload(0x44)))) { revert(0, 0); } else {
                                    if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                        if sub(calldataload(0x84), and(calldataload(0x84), 0xffffffff)) { revert(0, 0); } else {
                                            if sub(calldataload(0xa4), iszero(iszero(calldataload(0xa4)))) { revert(0, 0); } else {
                                                if sub(calldataload(0xe4), and(calldataload(0xe4), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                    if sub(calldataload(0x0104), and(calldataload(0x0104), 0xff)) { revert(0, 0); } else {
                                                        if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x58))) { revert(mload(0x40), 0x04); } else {
                                                            mstore(0xc0, 0xda96f0b600000000000000000000000000000000000000000000000000000000)
                                                            if iszero(extcodesize(and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))))) { revert(0, 0); } else {
                                                                mstore(0xc0, 0xb002b9fa00000000000000000000000000000000000000000000000000000000)
                                                                mstore(0xc4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                mstore(0xe4, calldataload(0xc4))
                                                                mstore(0x0104, and(calldataload(0xe4), 0xffffffffffffffff))
                                                                call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))), 0, mload(0x40), sub(add(0x60, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0)
                                                                if iszero(call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))), 0, mload(0x40), sub(add(0x60, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                                    returndatacopy(mload(0x40), 0, returndatasize())
                                                                    if call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))), 0, mload(0x40), sub(add(0x60, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0) {
                                                                        mstore(0xe0, 0xfce2fb41f9ff0457a0f012e62cfd6a7cff4e8439ae20008ab6979c740ba5a983)
                                                                        mstore(0x0100, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                        mstore(0x0120, and(0xffffffff, calldataload(0x24)))
                                                                        mstore(0x0140, iszero(iszero(calldataload(0x44))))
                                                                        mstore(0x0160, and(calldataload(0x64), 0xffffffffffffffffffffffffffffffff))
                                                                        mstore(0x0180, and(calldataload(0x84), 0xffffffff))
                                                                        mstore(0x01a0, iszero(iszero(calldataload(0xa4))))
                                                                        mstore(0x01c0, calldataload(0xc4))
                                                                        mstore(0x01e0, and(0xffffffffffffffff, calldataload(0xe4)))
                                                                        mstore(0xc0, 0x0120)
                                                                        if or(lt(0xffffffffffffffff, add(mload(0x40), 0x0140)), gt(mload(0x40), add(mload(0x40), 0x0140))) {
                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0x04, 0x41)
                                                                            mstore(0x40, add(mload(0x40), 0x0140))
                                                                            mstore(0x0200, 0x7f60825300000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0x0204, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                            mstore(0x0224, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                            mstore(0x0244, and(calldataload(0x0104), 0xff))
                                                                            mstore(0x0264, calldataload(0x0124))
                                                                            mstore(0x0284, calldataload(0x0144))
                                                                            staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))), add(mload(0x40), 0x0140), add(sub(add(add(mload(0x40), 0x0144), 0xa0), mload(0x40)), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffec0), add(mload(0x40), 0x0140), 0x20)
                                                                            if iszero(staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))), add(mload(0x40), 0x0140), add(sub(add(add(mload(0x40), 0x0144), 0xa0), mload(0x40)), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffec0), add(mload(0x40), 0x0140), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                                returndatacopy(mload(0x40), 0, returndatasize())
                                                                                if staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))), add(mload(0x40), 0x0140), add(sub(add(add(mload(0x40), 0x0144), 0xa0), mload(0x40)), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffec0), add(mload(0x40), 0x0140), 0x20) {
                                                                                    if and(sload(0x1d), 0xff) { revert(mload(0x40), 0x04); } else {
                                                                                        mstore(0x0200, 0x02b874a600000000000000000000000000000000000000000000000000000000)
                                                                                        if iszero(lt(and(calldataload(0x24), 0xffffffff), and(sload(0x08), 0xffffffff))) {
                                                                                            mstore(0, and(calldataload(0x24), 0xffffffff))
                                                                                            mstore(0x20, 0x07)
                                                                                            mstore(0x20, 0x23)
                                                                                            if and(sload(sha3(0, 0x40)), 0xff) { revert(mload(0x40), 0x04); } else {
                                                                                                mstore(0x0200, 0x741df93900000000000000000000000000000000000000000000000000000000)
                                                                                                if iszero(and(calldataload(0x84), 0xffffffff)) {
                                                                                                    if gt(and(calldataload(0x84), 0xffffffff), shr(0xe0, sload(sha3(0, 0x40)))) { revert(mload(0x40), 0x04); } else {
                                                                                                        mstore(0x0200, 0x0a4f5a0700000000000000000000000000000000000000000000000000000000)
                                                                                                        if lt(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), sload(0x1c)) { revert(mload(0x40), 0x04); } else {
                                                                                                            mstore(0x0200, 0x25a1ddf300000000000000000000000000000000000000000000000000000000)
                                                                                                            if iszero(or(eq(div(mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), and(calldataload(0x84), 0xffffffff)), and(0xffffffffffffffffffffffffffffffff, calldataload(0x64))), and(calldataload(0x84), 0xffffffff)), iszero(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64))))) {
                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                mstore(0x04, 0x11)
                                                                                                                if gt(mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), and(calldataload(0x84), 0xffffffff)), and(0xffffffffffffffffffffffffffffff, sload(add(sha3(0, 0x40), 0x01)))) { revert(mload(0x40), 0x04); } else {
                                                                                                                    mstore(0x0200, 0x543a6e1000000000000000000000000000000000000000000000000000000000)
                                                                                                                    mstore(0, and(calldataload(0x24), 0xffffffff))
                                                                                                                    mstore(0x20, 0x23)
                                                                                                                    if and(sload(sha3(0, 0x40)), 0xff) {
                                                                                                                        if gt(and(0xffffffffffffffff, shr(0x08, sload(sha3(0, 0x40)))), add(and(0xffffffffffffffff, shr(0x08, sload(sha3(0, 0x40)))), and(0xffffffffffffffff, shr(0x48, sload(sha3(0, 0x40)))))) {
                                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0x04, 0x11)
                                                                                                                            mstore(0, and(calldataload(0x24), 0xffffffff))
                                                                                                                            mstore(0x20, 0x24)
                                                                                                                            if iszero(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40))))) {
                                                                                                                                if iszero(or(eq(div(mul(mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), and(calldataload(0x84), 0xffffffff)), and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40))))), mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), and(calldataload(0x84), 0xffffffff))), and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40))))), iszero(mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), and(calldataload(0x84), 0xffffffff))))) {
                                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                    mstore(0x04, 0x11)
                                                                                                                                    if iszero(and(and(shr(0x01, add(and(0xffffffffffffffff, shr(0x08, sload(sha3(0, 0x40)))), and(0xffffffffffffffff, shr(0x48, sload(sha3(0, 0x40)))))), 0xffffffffffffffff), 0xffffffffffffffff)) {
                                                                                                                                        if gt(div(mul(mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), and(calldataload(0x84), 0xffffffff)), and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40))))), and(and(shr(0x01, add(and(0xffffffffffffffff, shr(0x08, sload(sha3(0, 0x40)))), and(0xffffffffffffffff, shr(0x48, sload(sha3(0, 0x40)))))), 0xffffffffffffffff), 0xffffffffffffffff)), 0xffffffffffffffffffffffff) { revert(mload(0x40), 0x04); } else {
                                                                                                                                            mstore(0x0200, 0x1b7f36f300000000000000000000000000000000000000000000000000000000)
                                                                                                                                            mstore(0, and(calldataload(0x24), 0xffffffff))
                                                                                                                                            mstore(0x20, 0x24)
                                                                                                                                            if eq(0, calldataload(0x44)) {
                                                                                                                                                if gt(add(and(0xffffffffffffffffffffffff, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffff)), and(0xffffffffffffffffffffffff, and(div(mul(mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), and(calldataload(0x84), 0xffffffff)), and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40))))), and(and(shr(0x01, add(and(0xffffffffffffffff, shr(0x08, sload(sha3(0, 0x40)))), and(0xffffffffffffffff, shr(0x48, sload(sha3(0, 0x40)))))), 0xffffffffffffffff), 0xffffffffffffffff)), 0xffffffffffffffffffffffff))), 0xffffffffffffffffffffffff) {
                                                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                    mstore(0x04, 0x11)
                                                                                                                                                    if gt(and(0xffffffffffffffffffffffff, add(and(0xffffffffffffffffffffffff, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffff)), and(0xffffffffffffffffffffffff, and(div(mul(mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), and(calldataload(0x84), 0xffffffff)), and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40))))), and(and(shr(0x01, add(and(0xffffffffffffffff, shr(0x08, sload(sha3(0, 0x40)))), and(0xffffffffffffffff, shr(0x48, sload(sha3(0, 0x40)))))), 0xffffffffffffffff), 0xffffffffffffffff)), 0xffffffffffffffffffffffff)))), and(0xffffffffffffffffffffffffffffffff, sload(add(sha3(0, 0x40), 0x01)))) { revert(mload(0x40), 0x04); } else {
                                                                                                                                                        mstore(0x0200, 0x40f9214300000000000000000000000000000000000000000000000000000000)
                                                                                                                                                        sstore(sha3(0, 0x40), or(and(0xffffffffffffffffffffffffffffffffffffffff000000000000000000000000, sload(sha3(0, 0x40))), and(0xffffffffffffffffffffffff, add(and(0xffffffffffffffffffffffff, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffff)), and(0xffffffffffffffffffffffff, and(div(mul(mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), and(calldataload(0x84), 0xffffffff)), and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40))))), and(and(shr(0x01, add(and(0xffffffffffffffff, shr(0x08, sload(sha3(0, 0x40)))), and(0xffffffffffffffff, shr(0x48, sload(sha3(0, 0x40)))))), 0xffffffffffffffff), 0xffffffffffffffff)), 0xffffffffffffffffffffffff))))))
                                                                                                                                                        if iszero(calldataload(0xa4)) {
                                                                                                                                                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                                                                                            mstore(0x20, 0x13)
                                                                                                                                                            if gt(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), sload(sha3(0, 0x40))) { revert(mload(0x40), 0x04); } else {
                                                                                                                                                                mstore(0x0200, 0x8e66735600000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                if iszero(extcodesize(0xac8ba1307815f74bd13d4d039c96f7b97e81aa49)) { revert(0, 0); } else {
                                                                                                                                                                    mstore(0x0200, 0x3f4e362600000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                    mstore(0x0204, 0x0f)
                                                                                                                                                                    mstore(0x0224, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                                                                                                    mstore(0x0244, and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)))
                                                                                                                                                                    delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0x64, mload(0x40), 0)
                                                                                                                                                                    if iszero(delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0x64, mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                                                                                                                                        returndatacopy(mload(0x40), 0, returndatasize())
                                                                                                                                                                        if delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0x64, mload(0x40), 0) {
                                                                                                                                                                            if iszero(sload(0x12)) {
                                                                                                                                                                                if iszero(sload(0x12)) {
                                                                                                                                                                                    sstore(0x0b, add(sload(0x0b), 0x01))
                                                                                                                                                                                    if or(gt(add(mload(0x40), 0x0120), 0xffffffffffffffff), lt(add(mload(0x40), 0x0120), mload(0x40))) {
                                                                                                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                        mstore(0x04, 0x41)
                                                                                                                                                                                        mstore(0x40, add(mload(0x40), 0x0120))
                                                                                                                                                                                        mstore(0x0200, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                                                                                                        mstore(0x0220, and(0xffffffff, calldataload(0x24)))
                                                                                                                                                                                        mstore(0x0240, and(0xffffffffffffffff, and(shr(0x01, add(and(0xffffffffffffffff, shr(0x08, sload(sha3(0, 0x40)))), and(0xffffffffffffffff, shr(0x48, sload(sha3(0, 0x40)))))), 0xffffffffffffffff)))
                                                                                                                                                                                        mstore(0x0260, and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)))
                                                                                                                                                                                        mstore(0x0280, and(calldataload(0x84), 0xffffffff))
                                                                                                                                                                                        mstore(0x02a0, and(0xffffffffffffffff, timestamp()))
                                                                                                                                                                                        mstore(0x02c0, iszero(iszero(calldataload(0x44))))
                                                                                                                                                                                        mstore(0x02e0, iszero(iszero(calldataload(0xa4))))
                                                                                                                                                                                        mstore(0x0300, 0x01)
                                                                                                                                                                                        mstore(0, sload(0x0b))
                                                                                                                                                                                        mstore(0x20, 0x0a)
                                                                                                                                                                                        sstore(sha3(0, 0x40), or(and(0xffffffff0000000000000000000000000000000000000000, shl(0xa0, mload(add(mload(0x40), 0x20)))), or(and(0xffffffffffffffffffffffffffffffffffffffff, mload(mload(0x40))), and(sload(sha3(0, 0x40)), 0xffffffffffffffff000000000000000000000000000000000000000000000000))))
                                                                                                                                                                                        sstore(sha3(0, 0x40), or(and(0xffffffffffffffff000000000000000000000000000000000000000000000000, shl(0xc0, and(mload(add(mload(0x40), 0x40)), 0xffffffffffffffff))), and(0xffffffffffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                                                                                                                                                        sstore(add(0x01, sha3(0, 0x40)), or(and(0xff000000000000000000000000000000000000000000000000000000000000, shl(0xf0, iszero(iszero(mload(add(mload(0x40), 0x0100)))))), or(and(0xff0000000000000000000000000000000000000000000000000000000000, shl(0xe8, iszero(iszero(mload(add(mload(0x40), 0xe0)))))), or(and(0xff00000000000000000000000000000000000000000000000000000000, shl(0xe0, iszero(iszero(mload(add(mload(0x40), 0xc0)))))), or(and(0xffffffffffffffff0000000000000000000000000000000000000000, shl(0xa0, mload(add(mload(0x40), 0xa0)))), or(and(0xffffffff00000000000000000000000000000000, shl(0x80, mload(add(mload(0x40), 0x80)))), or(and(0xffffffffffffffffffffffffffffffff, mload(add(mload(0x40), 0x60))), and(sload(add(0x01, sha3(0, 0x40))), 0xff00000000000000000000000000000000000000000000000000000000000000))))))))
                                                                                                                                                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                                                                                                                        mstore(0x20, 0x0c)
                                                                                                                                                                                        if iszero(lt(sload(sha3(0, 0x40)), 0x010000000000000000)) {
                                                                                                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                            mstore(0x04, 0x41)
                                                                                                                                                                                            sstore(sha3(0, 0x40), add(sload(sha3(0, 0x40)), 0x01))
                                                                                                                                                                                            if iszero(lt(sload(sha3(0, 0x40)), sload(sha3(0, 0x40)))) {
                                                                                                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                mstore(0x04, 0x32)
                                                                                                                                                                                                mstore(0, sha3(0, 0x40))
                                                                                                                                                                                                sstore(add(sha3(0, 0x20), sload(sha3(0, 0x40))), or(and(0, sload(add(sha3(0, 0x20), sload(sha3(0, 0x40))))), shl(0, sload(0x0b))))
                                                                                                                                                                                                mstore(0, sload(0x0b))
                                                                                                                                                                                                mstore(0x20, 0x0d)
                                                                                                                                                                                                sstore(sha3(0, 0x40), sload(sha3(0, 0x40)))
                                                                                                                                                                                                mstore(0x0320, and(0xffffffff, calldataload(0x24)))
                                                                                                                                                                                                mstore(0x0340, iszero(iszero(calldataload(0x44))))
                                                                                                                                                                                                mstore(0x0360, iszero(iszero(calldataload(0xa4))))
                                                                                                                                                                                                mstore(0x0380, and(0xffffffffffffffff, and(shr(0x01, add(and(0xffffffffffffffff, shr(0x08, sload(sha3(0, 0x40)))), and(0xffffffffffffffff, shr(0x48, sload(sha3(0, 0x40)))))), 0xffffffffffffffff)))
                                                                                                                                                                                                mstore(0x03a0, and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)))
                                                                                                                                                                                                mstore(0x03c0, and(calldataload(0x84), 0xffffffff))
                                                                                                                                                                                                log3(mload(0x40), 0xc0, 0x88451ea1189f73b554f0bf39c09868560ed149b3d788fcc933ff66ba926827f3, sload(0x0b), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                                                                                                                mstore(0x0320, sload(0x0b))
                                                                                                                                                                                                return(mload(0x40), 0x20)
                                                                                                                                                                                                if iszero(iszero(and(0xffffffffffffffffffffffffffffffff, sload(0x1b)))) {
                                                                                                                                                                                                }
                                                                                                                                                                                                if gt(mload(0x40), 0xffffffffffffffff) {
                                                                                                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                    mstore(0x04, 0x41)
                                                                                                                                                                                                    mstore(0x40, mload(0x40))
                                                                                                                                                                                                    if 0 { revert(0, 0); } else {
                                                                                                                                                                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                                                                                                                                        mstore(0x20, 0x09)
                                                                                                                                                                                                        if lt(sload(sha3(0, 0x40)), and(0xffffffffffffffffffffffffffffffff, calldataload(0x64))) { revert(mload(0x40), 0x04); } else {
                                                                                                                                                                                                            mstore(0x0200, 0xf4d678b800000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                                                                                                                                            mstore(0x20, 0x09)
                                                                                                                                                                                                            sstore(sha3(0, 0x40), sub(sload(sha3(0, 0x40)), and(0xffffffffffffffffffffffffffffffff, calldataload(0x64))))
                                                                                                                                                                                                            if gt(add(and(0xffffffffffffffffffffffffffffffff, shr(0x80, or(and(sub(and(0xffffffffffffffffffffffffffffffff, sload(0x16)), calldataload(0x64)), 0xffffffffffffffffffffffffffffffff), and(sload(0x16), 0xffffffffffffffffffffffffffffffff00000000000000000000000000000000)))), and(0xffffffffffffffffffffffffffffffff, calldataload(0x64))), 0xffffffffffffffffffffffffffffffff) { revert(mload(0x40), 0x04); } else {
                                                                                                                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                mstore(0x04, 0x11)
                                                                                                                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                mstore(0x04, 0x12)
                                                                                                                                                                                                                mstore(0x0200, 0x924d25e600000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                mstore(0x0200, 0xc018266900000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                mstore(0x0204, and(0xffffffff, and(shr(0xc0, sload(sha3(0, 0x40))), 0xffffffff)))
                                                                                                                                                                                                                staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), mload(0x40), 0x24, mload(0x40), 0x20)
                                                                                                                                                                                                                if iszero(staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), mload(0x40), 0x24, mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                                                                                                                                                                    returndatacopy(mload(0x40), 0, returndatasize())
                                                                                                                                                                                                                    if staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), mload(0x40), 0x24, mload(0x40), 0x20) {
                                                                                                                                                                                                                        if gt(0x20, returndatasize()) {
                                                                                                                                                                                                                            if or(lt(add(mload(0x40), 0x20), mload(0x40)), gt(add(mload(0x40), 0x20), 0xffffffffffffffff)) {
                                                                                                                                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                                mstore(0x04, 0x41)
                                                                                                                                                                                                                                mstore(0x40, add(mload(0x40), 0x20))
                                                                                                                                                                                                                                if slt(sub(add(mload(0x40), 0x20), mload(0x40)), 0x20) { revert(0, 0); } else {
                                                                                                                                                                                                                                    if sub(mload(mload(0x40)), and(mload(mload(0x40)), 0xffffffffffffffff)) {
                                                                                                                                                                                                                                        mstore(0, and(calldataload(0x24), 0xffffffff))
                                                                                                                                                                                                                                        mstore(0x20, 0x24)
                                                                                                                                                                                                                                        if iszero(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40))))) {
                                                                                                                                                                                                                                            if iszero(or(eq(div(mul(mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), and(calldataload(0x84), 0xffffffff)), and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40))))), mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), and(calldataload(0x84), 0xffffffff))), and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40))))), iszero(mul(and(0xffffffffffffffffffffffffffffffff, calldataload(0x64)), and(calldataload(0x84), 0xffffffff))))) { revert(mload(0x40), 0x04); } else {
                                                                                                                                                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                                                mstore(0x04, 0x11)
                                                                                                                                                                                                                                                mstore(0x0220, 0x924d25e600000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                                                mstore(0x0200, 0x641f87fc00000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                                                mstore(0x0200, 0x67207a8800000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                                                if gt(0x20, returndatasize()) { revert(0, 0); } else {
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
            * @custom:signature    Unresolved_0cdd5fc4() public view returns (uint256)
            */
            case 0x0cdd5fc4 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        if sload(0x12) {
                            mstore(0xc0, 0)
                            return(mload(0x40), 0x20)
                            if gt(and(sload(0x16), 0xffffffffffffffffffffffffffffffff), add(and(sload(0x16), 0xffffffffffffffffffffffffffffffff), shr(0x80, sload(0x16)))) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x11)
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_ed410ee1() public view returns (address)
            */
            case 0xed410ee1 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x06), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_7dc0d1d0() public view returns (address)
            */
            case 0x7dc0d1d0 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_ec0bdcfc() public view returns (uint256)
            */
            case 0xec0bdcfc {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, sload(0x03))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_f1a8786c() public view returns (uint256)
            */
            case 0xf1a8786c {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, sload(0x17))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_4a4d9eea(address arg0, uint256 arg1, uint256 arg2) public payable returns (bytes memory)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            */
            case 0x4a4d9eea {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0xc0, 0xca02ff9100000000000000000000000000000000000000000000000000000000)
                            mstore(0xc4, 0x0f)
                            mstore(0xe4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x0104, calldataload(0x24))
                            mstore(0x0124, calldataload(0x44))
                            delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0x84, mload(0x40), 0x60)
                            if iszero(delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0x84, mload(0x40), 0x60)) { revert(mload(0x40), returndatasize()); } else {
                                returndatacopy(mload(0x40), 0, returndatasize())
                                if delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0x84, mload(0x40), 0x60) {
                                    mstore(0xc0, 0)
                                    mstore(0xe0, 0)
                                    mstore(0x0100, 0)
                                    return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                    if gt(0x60, returndatasize()) {
                                        if or(lt(add(mload(0x40), 0x60), mload(0x40)), gt(add(mload(0x40), 0x60), 0xffffffffffffffff)) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x41)
                                            mstore(0x40, add(mload(0x40), 0x60))
                                            if slt(sub(add(mload(0x40), 0x60), mload(0x40)), 0x60) { revert(0, 0); } else {
                                                mstore(0x0120, mload(mload(0x40)))
                                                mstore(0x0140, mload(add(mload(0x40), 0x20)))
                                                mstore(0x0160, mload(add(mload(0x40), 0x40)))
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

            /*
            * @custom:signature    Unresolved_2792e706(address arg0, uint256 arg1, uint256 arg2, uint64 arg3, bool arg4, uint256 arg5, uint256 arg6) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint64", "bytes8", "int64"]
            * @param                arg4 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg5 ["uint256", "bytes32", "int256"]
            * @param                arg6 ["uint256", "bytes32", "int256"]
            */
            case 0x2792e706 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xe0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if gt(calldataload(0x24), 0xffffffffffffffff) { revert(0, 0); } else {
                                if iszero(slt(add(add(0x04, calldataload(0x24)), 0x1f), calldatasize())) {
                                    if gt(calldataload(add(0x04, calldataload(0x24))), 0xffffffffffffffff) { revert(0, 0); } else {
                                        if gt(add(add(shl(0x05, calldataload(add(0x04, calldataload(0x24)))), add(0x04, calldataload(0x24))), 0x20), calldatasize()) {
                                            if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                if sub(calldataload(0x84), and(calldataload(0x84), 0xff)) { revert(0, 0); } else {
                                                    if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x58))) { revert(mload(0x40), 0x04); } else {
                                                        mstore(0xc0, 0xda96f0b600000000000000000000000000000000000000000000000000000000)
                                                        if iszero(extcodesize(and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))))) { revert(0, 0); } else {
                                                            mstore(0xc0, 0xb002b9fa00000000000000000000000000000000000000000000000000000000)
                                                            mstore(0xc4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                            mstore(0xe4, calldataload(0x44))
                                                            mstore(0x0104, and(calldataload(0x64), 0xffffffffffffffff))
                                                            call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))), 0, mload(0x40), sub(add(0x60, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0)
                                                            if iszero(call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))), 0, mload(0x40), sub(add(0x60, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                                returndatacopy(mload(0x40), 0, returndatasize())
                                                                if call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))), 0, mload(0x40), sub(add(0x60, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0) {
                                                                    if gt(calldataload(add(0x04, calldataload(0x24))), 0x07ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) { revert(0, 0); } else {
                                                                        calldatacopy(add(mload(0x40), 0x20), add(add(0x04, calldataload(0x24)), 0x20), shl(0x05, calldataload(add(0x04, calldataload(0x24)))))
                                                                        mstore(0xc0, sub(add(mload(0x40), shl(0x05, calldataload(add(0x04, calldataload(0x24))))), mload(0x40)))
                                                                        if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(sub(add(mload(0x40), shl(0x05, calldataload(add(0x04, calldataload(0x24))))), mload(0x40)), 0x20), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(sub(add(mload(0x40), shl(0x05, calldataload(add(0x04, calldataload(0x24))))), mload(0x40)), 0x20), 0x1f))), 0xffffffffffffffff)) {
                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0x04, 0x41)
                                                                            mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(sub(add(mload(0x40), shl(0x05, calldataload(add(0x04, calldataload(0x24))))), mload(0x40)), 0x20), 0x1f))))
                                                                            mstore(0x0100, 0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13)
                                                                            mstore(0x0120, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                            mstore(0x0140, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                            mstore(0x0160, calldataload(0x44))
                                                                            mstore(0x0180, and(0xffffffffffffffff, calldataload(0x64)))
                                                                            mstore(0xe0, 0xa0)
                                                                            if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                mstore(0x04, 0x41)
                                                                                mstore(0x40, add(mload(0x40), 0xc0))
                                                                                mstore(0x01a0, 0x7f60825300000000000000000000000000000000000000000000000000000000)
                                                                                mstore(0x01a4, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                mstore(0x01c4, sha3(add(0x20, mload(0x40)), mload(mload(0x40))))
                                                                                mstore(0x01e4, and(calldataload(0x84), 0xff))
                                                                                mstore(0x0204, calldataload(0xa4))
                                                                                mstore(0x0224, calldataload(0xc4))
                                                                                staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))), mload(0x40), sub(add(add(mload(0x40), 0x04), 0xa0), mload(0x40)), mload(0x40), 0x20)
                                                                                if iszero(staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))), mload(0x40), sub(add(add(mload(0x40), 0x04), 0xa0), mload(0x40)), mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                                    returndatacopy(mload(0x40), 0, returndatasize())
                                                                                    if staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))), mload(0x40), sub(add(add(mload(0x40), 0x04), 0xa0), mload(0x40)), mload(0x40), 0x20) {
                                                                                        if iszero(calldataload(add(0x04, calldataload(0x24)))) {
                                                                                            if gt(calldataload(add(0x04, calldataload(0x24))), 0x19) { revert(mload(0x40), 0x04); } else {
                                                                                                mstore(0x01a0, 0x8431a15a00000000000000000000000000000000000000000000000000000000)
                                                                                                if or(gt(mload(0x40), add(mload(0x40), 0x0180)), gt(add(mload(0x40), 0x0180), 0xffffffffffffffff)) {
                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                    mstore(0x04, 0x41)
                                                                                                    mstore(0x40, add(mload(0x40), 0x0180))
                                                                                                    mstore(0x01a0, 0)
                                                                                                    mstore(0x01c0, 0)
                                                                                                    mstore(0x01e0, 0)
                                                                                                    mstore(0x0200, 0)
                                                                                                    mstore(0x0220, 0)
                                                                                                    mstore(0x0240, 0)
                                                                                                    mstore(0x0260, 0)
                                                                                                    mstore(0x0280, 0)
                                                                                                    mstore(0x02a0, 0)
                                                                                                    mstore(0x02c0, 0)
                                                                                                    mstore(0x02e0, 0)
                                                                                                    mstore(0x0300, 0)
                                                                                                    if sload(0x12) {
                                                                                                        mstore(0x02e0, 0)
                                                                                                        if gt(and(sload(0x08), 0xffffffff), 0xffffffffffffffff) {
                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                            mstore(0x04, 0x41)
                                                                                                            if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, shl(0x05, and(sload(0x08), 0xffffffff))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, shl(0x05, and(sload(0x08), 0xffffffff))), 0x1f))), 0xffffffffffffffff)) {
                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                mstore(0x04, 0x41)
                                                                                                                mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, shl(0x05, and(sload(0x08), 0xffffffff))), 0x1f))))
                                                                                                                mstore(0x0320, and(sload(0x08), 0xffffffff))
                                                                                                                if gt(and(sload(0x08), 0xffffffff), 0xffffffffffffffff) {
                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                    mstore(0x04, 0x41)
                                                                                                                    if gt(and(sload(0x16), 0xffffffffffffffffffffffffffffffff), add(and(sload(0x16), 0xffffffffffffffffffffffffffffffff), shr(0x80, sload(0x16)))) { revert(mload(0x40), 0x04); } else {
                                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                        mstore(0x04, 0x11)
                                                                                                                        mstore(0x01a0, 0xad0ef2c500000000000000000000000000000000000000000000000000000000)
                                                                                                                        if gt(0x20, returndatasize()) {
                                                                                                                        }
                                                                                                                        if gt(mload(0x40), 0xffffffffffffffff) { revert(0, 0); } else {
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
            * @custom:signature    Unresolved_6155be59() public view returns (uint256)
            */
            case 0x6155be59 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, sload(0x1c))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_58d3ec6a(uint256 arg0) public pure
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x58d3ec6a {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if gt(calldataload(0x04), 0xffffffffffffffff) { revert(0, 0); } else {
                            if iszero(slt(add(add(0x04, calldataload(0x04)), 0x1f), calldatasize())) {
                                if gt(calldataload(add(0x04, calldataload(0x04))), 0xffffffffffffffff) { revert(0, 0); } else {
                                    if gt(add(add(shl(0x05, calldataload(add(0x04, calldataload(0x04)))), add(0x04, calldataload(0x04))), 0x20), calldatasize()) { revert(0, 0); } else {
                                        mstore(0xc0, 0x58f03bf700000000000000000000000000000000000000000000000000000000)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_af210ecc() public pure returns (uint256)
            */
            case 0xaf210ecc {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, 0x19)
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_899346c7() public view returns (uint256)
            */
            case 0x899346c7 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, sload(0x0b))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_27e235e3(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x27e235e3 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x09)
                            mstore(0xc0, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_b29af6b0(uint256 arg0) public payable returns (uint256)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0xb29af6b0 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(0, 0); } else {
                            mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                            sstore(0x1c, calldataload(0x04))
                            mstore(0xc0, calldataload(0x04))
                            log1(mload(0x40), 0x20, 0xdee13c5fdf8317818089a807120a01c749f2de4df72559428fa974e6c4414964)
                            return(0, 0)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_bacd9ea0(uint256 arg0) public view returns (uint256)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0xbacd9ea0 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if iszero(or(eq(div(mul(calldataload(0x04), sload(0x03)), calldataload(0x04)), sload(0x03)), iszero(calldataload(0x04)))) { revert(0, 0); } else {
                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                            mstore(0x04, 0x11)
                            mstore(0xc0, mul(calldataload(0x04), sload(0x03)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_13dd495b() public view returns (address)
            */
            case 0x13dd495b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x58), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_7e4174fc(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x7e4174fc {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x21)
                            mstore(0xc0, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_e0189108(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xe0189108 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e))) {
                                mstore(0xc0, 0xc1a9a50800000000000000000000000000000000000000000000000000000000)
                                mstore(0xc4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20)
                                if iszero(staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                    returndatacopy(mload(0x40), 0, returndatasize())
                                    if staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20) {
                                        if iszero(0) {
                                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                            mstore(0x20, 0x21)
                                            if sload(sha3(0, 0x40)) { revert(mload(0x40), 0x04); } else {
                                                mstore(0xc0, 0x28ef431400000000000000000000000000000000000000000000000000000000)
                                                mstore(0, 0)
                                                mstore(0x20, 0x20)
                                                if iszero(gt(number(), sload(sha3(0, 0x40)))) { revert(mload(0x40), 0x04); } else {
                                                    mstore(0xc0, 0xfefe83a000000000000000000000000000000000000000000000000000000000)
                                                    mstore(0, 0)
                                                    mstore(0x20, 0x20)
                                                    sstore(sha3(0, 0x40), number())
                                                    mstore(0xe0, 0)
                                                    mstore(0x0100, 0)
                                                    mstore(0xc0, 0x40)
                                                    if or(lt(add(mload(0x40), 0x60), mload(0x40)), gt(add(mload(0x40), 0x60), 0xffffffffffffffff)) {
                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x04, 0x41)
                                                        mstore(0x40, add(mload(0x40), 0x60))
                                                        staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)
                                                        if iszero(returndatasize()) {
                                                            if iszero(iszero(staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0))) {
                                                                if iszero(staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x04); } else {
                                                                    mstore(0x0120, 0x0a9e018000000000000000000000000000000000000000000000000000000000)
                                                                    if slt(sub(add(0x60, mload(0x60)), 0x60), 0x60) {
                                                                        if sub(mload(0x80), and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                                            if lt(mload(0x60), 0x60) { revert(mload(0x40), 0x04); } else {
                                                                                mstore(0x0120, 0x0a9e018000000000000000000000000000000000000000000000000000000000)
                                                                                if gt(returndatasize(), 0xffffffffffffffff) {
                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                    mstore(0x04, 0x41)
                                                                                    if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), 0xffffffffffffffff)) {
                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                        mstore(0x04, 0x41)
                                                                                        mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))))
                                                                                        mstore(0x0120, returndatasize())
                                                                                        returndatacopy(add(mload(0x40), 0x20), 0, returndatasize())
                                                                                        if iszero(iszero(staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0))) {
                                                                                            if iszero(staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x04); } else {
                                                                                                mstore(0x0160, 0x0a9e018000000000000000000000000000000000000000000000000000000000)
                                                                                                mstore(0xc0, 0x0576e00500000000000000000000000000000000000000000000000000000000)
                                                                                                if gt(0x20, returndatasize()) { revert(0, 0); } else {
                                                                                                }
                                                                                                mstore(0xc0, 0x967d697b00000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_e1f9209b() public view returns (address)
            */
            case 0xe1f9209b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x1f), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_e634384f(uint256 arg0) public view returns (bytes memory)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0xe634384f {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) { revert(0, 0); } else {
                        mstore(0, calldataload(0x04))
                        mstore(0x20, 0x0f)
                        mstore(0xc0, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff))
                        mstore(0xe0, and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffffffff))
                        mstore(0x0100, shr(0xd0, sload(sha3(0, 0x40))))
                        mstore(0x0120, sload(add(sha3(0, 0x40), 0x01)))
                        return(mload(0x40), 0x80)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_138e9de2() public view
            */
            case 0x138e9de2 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        if gt(and(sload(0x16), 0xffffffffffffffffffffffffffffffff), add(and(sload(0x16), 0xffffffffffffffffffffffffffffffff), shr(0x80, sload(0x16)))) {
                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                            mstore(0x04, 0x11)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_21f55a6c() public view returns (address)
            */
            case 0x21f55a6c {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x25), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_5fb3b1b5() public view returns (uint256)
            */
            case 0x5fb3b1b5 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, sload(0x19))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_c8372577(uint32 arg0) public view returns (bool)
            * @param                arg0 ["uint32", "bytes4", "int32"]
            */
            case 0xc8372577 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffff))
                            mstore(0x20, 0x23)
                            mstore(0xc0, iszero(iszero(and(sload(sha3(0, 0x40)), 0xff))))
                            mstore(0xe0, and(shr(0x08, sload(sha3(0, 0x40))), 0xffffffffffffffff))
                            mstore(0x0100, and(shr(0x48, sload(sha3(0, 0x40))), 0xffffffffffffffff))
                            mstore(0x0120, and(shr(0x88, sload(sha3(0, 0x40))), 0xffffffffffffffff))
                            return(mload(0x40), 0x80)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_50c23fab(uint256 arg0) public view returns (uint64)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x50c23fab {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        mstore(0, calldataload(0x04))
                        mstore(0x20, 0x0a)
                        mstore(0, and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffff))
                        mstore(0x20, 0x07)
                        if iszero(and(0xffffffff, and(shr(0x80, sload(add(sha3(0, 0x40), 0x01))), 0xffffffff))) {
                            if iszero(and(shr(0xe0, sload(add(sha3(0, 0x40), 0x01))), 0xff)) {
                                if gt(sub(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), div(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), and(0xffffffff, and(shr(0x80, sload(add(sha3(0, 0x40), 0x01))), 0xffffffff)))), and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40))))) {
                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                    mstore(0x04, 0x11)
                                    if iszero(or(eq(div(mul(sub(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), div(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), and(0xffffffff, and(shr(0x80, sload(add(sha3(0, 0x40), 0x01))), 0xffffffff)))), and(shr(0x78, sload(add(sha3(0, 0x40), 0x01))), 0xffffffffffffffff)), sub(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), div(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), and(0xffffffff, and(shr(0x80, sload(add(sha3(0, 0x40), 0x01))), 0xffffffff))))), and(shr(0x78, sload(add(sha3(0, 0x40), 0x01))), 0xffffffffffffffff)), iszero(sub(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), div(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), and(0xffffffff, and(shr(0x80, sload(add(sha3(0, 0x40), 0x01))), 0xffffffff))))))) {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x11)
                                        if gt(sub(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), div(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), and(0xffffffff, and(shr(0x80, sload(add(sha3(0, 0x40), 0x01))), 0xffffffff)))), add(sub(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), div(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), and(0xffffffff, and(shr(0x80, sload(add(sha3(0, 0x40), 0x01))), 0xffffffff)))), div(mul(sub(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), div(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), and(0xffffffff, and(shr(0x80, sload(add(sha3(0, 0x40), 0x01))), 0xffffffff)))), and(shr(0x78, sload(add(sha3(0, 0x40), 0x01))), 0xffffffffffffffff)), 0x0de0b6b3a7640000))) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x11)
                                            mstore(0xc0, and(0xffffffffffffffff, and(add(sub(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), div(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), and(0xffffffff, and(shr(0x80, sload(add(sha3(0, 0x40), 0x01))), 0xffffffff)))), div(mul(sub(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), div(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), and(0xffffffff, and(shr(0x80, sload(add(sha3(0, 0x40), 0x01))), 0xffffffff)))), and(shr(0x78, sload(add(sha3(0, 0x40), 0x01))), 0xffffffffffffffff)), 0x0de0b6b3a7640000)), 0xffffffffffffffff)))
                                            return(mload(0x40), 0x20)
                                            if gt(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), add(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), div(and(0xffffffffffffffff, shr(0xc0, sload(sha3(0, 0x40)))), and(0xffffffff, and(shr(0x80, sload(add(sha3(0, 0x40), 0x01))), 0xffffffff))))) { revert(0, 0); } else {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x11)
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x12)
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
            * @custom:signature    Unresolved_63ca348f(uint32 arg0, uint256 arg1, address arg2, uint32 arg3, uint256 arg4) public pure
            * @param                arg0 ["uint32", "bytes4", "int32"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["address", "uint128", "bytes16", "int128"]
            * @param                arg3 ["uint32", "bytes4", "int32"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            */
            case 0x63ca348f {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xa0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), iszero(iszero(calldataload(0x24)))) { revert(0, 0); } else {
                                if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                    if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffff)) { revert(0, 0); } else {
                                        if sub(iszero(iszero(calldataload(0x84))), calldataload(0x84)) { revert(0, 0); } else {
                                            mstore(0xc0, 0x58f03bf700000000000000000000000000000000000000000000000000000000)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_d188c049(address arg0) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xd188c049 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(0, 0); } else {
                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x58, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x58))))
                                log2(0, 0, 0x3cfda8ee6e20b237d2949c3d16b6f12822b6f1bc0580f188f932c0771cac729d, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                return(0, 0)
                            }
                        }
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
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(0, 0); } else {
                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0, or(and(0xffffffffffffffffffffffffffffffffffffffff0000, shl(0x10, calldataload(0x04))), and(0xffffffffffffffffffff0000000000000000000000000000000000000000ffff, sload(0))))
                                codecopy(0, 0x5915, 0x20)
                                mstore(0, mload(0))
                                log2(0, 0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                return(0, 0)
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_f37d3c4f(uint32 arg0) public view returns (bytes memory)
            * @param                arg0 ["uint32", "bytes4", "int32"]
            */
            case 0xf37d3c4f {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffff))
                            mstore(0x20, 0x24)
                            mstore(0xc0, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffff))
                            mstore(0xe0, and(shr(0x60, sload(sha3(0, 0x40))), 0xffffffffffffffffffffffff))
                            mstore(0x0100, shr(0xc0, sload(sha3(0, 0x40))))
                            mstore(0x0120, and(sload(add(sha3(0, 0x40), 0x01)), 0xffffffffffffffffffffffffffffffff))
                            mstore(0x0140, shr(0x80, sload(add(sha3(0, 0x40), 0x01))))
                            return(mload(0x40), 0xa0)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_fdfd905d() public pure returns (uint256)
            */
            case 0xfdfd905d {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, 0x0de0b6b3a7640000)
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_31a4956c(address arg0) public view returns (bool)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x31a4956c {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x21)
                            mstore(0xc0, iszero(iszero(iszero(iszero(sload(sha3(0, 0x40)))))))
                            mstore(0xe0, and(and(sload(sha3(0, 0x40)), 0xffffffffffffffff), 0xffffffffffffffff))
                            mstore(0x0100, and(and(shr(0x40, sload(sha3(0, 0x40))), 0xffffffffffffffff), 0xffffffffffffffff))
                            mstore(0x0120, and(and(shr(0x80, sload(sha3(0, 0x40))), 0xffffffff), 0xffffffff))
                            return(mload(0x40), 0x80)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_ae4daf4e(address arg0, uint256 arg1, uint256 arg2) public payable returns (bytes memory)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            */
            case 0xae4daf4e {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0xc0, 0x2448a55300000000000000000000000000000000000000000000000000000000)
                            mstore(0xc4, 0x0f)
                            mstore(0xe4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x0104, calldataload(0x24))
                            mstore(0x0124, calldataload(0x44))
                            mstore(0x0144, 0x0de0b6b3a7640000)
                            delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0xa4, mload(0x40), 0x60)
                            if iszero(delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0xa4, mload(0x40), 0x60)) { revert(mload(0x40), returndatasize()); } else {
                                returndatacopy(mload(0x40), 0, returndatasize())
                                if delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0xa4, mload(0x40), 0x60) {
                                    mstore(0xc0, 0)
                                    mstore(0xe0, 0)
                                    mstore(0x0100, 0)
                                    return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                    if gt(0x60, returndatasize()) {
                                        if or(lt(add(mload(0x40), 0x60), mload(0x40)), gt(add(mload(0x40), 0x60), 0xffffffffffffffff)) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x41)
                                            mstore(0x40, add(mload(0x40), 0x60))
                                            if slt(sub(add(mload(0x40), 0x60), mload(0x40)), 0x60) { revert(0, 0); } else {
                                                mstore(0x0120, mload(mload(0x40)))
                                                mstore(0x0140, mload(add(mload(0x40), 0x20)))
                                                mstore(0x0160, mload(add(mload(0x40), 0x40)))
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

            /*
            * @custom:signature    Unresolved_01681a62(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x01681a62 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x21)
                            if iszero(sload(sha3(0, 0x40))) {
                                if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e))) {
                                    mstore(0xc0, 0xc1a9a50800000000000000000000000000000000000000000000000000000000)
                                    mstore(0xc4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                    staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20)
                                    if iszero(staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                        returndatacopy(mload(0x40), 0, returndatasize())
                                        if staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20) {
                                            if iszero(0) {
                                                mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                mstore(0x20, 0x21)
                                                if iszero(iszero(iszero(sload(sha3(0, 0x40))))) {
                                                    if iszero(gt(number(), and(0xffffffff, and(shr(0x80, sload(sha3(0, 0x40))), 0xffffffff)))) { revert(mload(0x40), 0x04); } else {
                                                        mstore(0xc0, 0xd26ffacb00000000000000000000000000000000000000000000000000000000)
                                                        mstore(0xe0, 0)
                                                        mstore(0x0100, 0)
                                                        mstore(0xc0, 0x40)
                                                        if or(lt(add(mload(0x40), 0x60), mload(0x40)), gt(add(mload(0x40), 0x60), 0xffffffffffffffff)) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            mstore(0x40, add(mload(0x40), 0x60))
                                                            staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)
                                                            if iszero(returndatasize()) {
                                                                if iszero(iszero(staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0))) {
                                                                    if iszero(staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x04); } else {
                                                                        mstore(0x0120, 0x0a9e018000000000000000000000000000000000000000000000000000000000)
                                                                        if slt(sub(add(0x60, mload(0x60)), 0x60), 0x60) {
                                                                            if sub(mload(0x80), and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                                                if lt(mload(0x60), 0x60) { revert(mload(0x40), 0x04); } else {
                                                                                    mstore(0x0120, 0x0a9e018000000000000000000000000000000000000000000000000000000000)
                                                                                    if gt(returndatasize(), 0xffffffffffffffff) {
                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                        mstore(0x04, 0x41)
                                                                                        if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), 0xffffffffffffffff)) {
                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                            mstore(0x04, 0x41)
                                                                                            mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))))
                                                                                            mstore(0x0120, returndatasize())
                                                                                            returndatacopy(add(mload(0x40), 0x20), 0, returndatasize())
                                                                                            if iszero(iszero(staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0))) {
                                                                                                if iszero(staticcall(gas(), 0x0801, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x04); } else {
                                                                                                    mstore(0x0160, 0x0a9e018000000000000000000000000000000000000000000000000000000000)
                                                                                                    mstore(0xc0, 0x0984a61700000000000000000000000000000000000000000000000000000000)
                                                                                                    mstore(0xc0, 0x0576e00500000000000000000000000000000000000000000000000000000000)
                                                                                                    if gt(0x20, returndatasize()) { revert(mload(0x40), 0x04); } else {
                                                                                                    }
                                                                                                    mstore(0xc0, 0x967d697b00000000000000000000000000000000000000000000000000000000)
                                                                                                    if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e))) {
                                                                                                        mstore(0xc0, 0xc1a9a50800000000000000000000000000000000000000000000000000000000)
                                                                                                        mstore(0xc4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                                        staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20)
                                                                                                        if iszero(staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                                                            returndatacopy(mload(0x40), 0, returndatasize())
                                                                                                            if staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1e)), mload(0x40), 0x24, mload(0x40), 0x20) {
                                                                                                                if iszero(0) {
                                                                                                                    mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                                                    mstore(0x20, 0x21)
                                                                                                                    if sload(sha3(0, 0x40)) { revert(mload(0x40), 0x04); } else {
                                                                                                                        mstore(0xc0, 0x28ef431400000000000000000000000000000000000000000000000000000000)
                                                                                                                        mstore(0, 0)
                                                                                                                        mstore(0x20, 0x20)
                                                                                                                        if iszero(gt(number(), sload(sha3(0, 0x40)))) { revert(mload(0x40), 0x04); } else {
                                                                                                                            mstore(0xc0, 0xfefe83a000000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0xc0, 0x0576e00500000000000000000000000000000000000000000000000000000000)
                                                                                                                            if gt(0x20, returndatasize()) { revert(0, 0); } else {
                                                                                                                            }
                                                                                                                            mstore(0xc0, 0x967d697b00000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_1afd17e9(uint32 arg0, uint256 arg1, address arg2, uint32 arg3) public pure
            * @param                arg0 ["uint32", "bytes4", "int32"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["address", "uint128", "bytes16", "int128"]
            * @param                arg3 ["uint32", "bytes4", "int32"]
            */
            case 0x1afd17e9 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x80) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), iszero(iszero(calldataload(0x24)))) { revert(0, 0); } else {
                                if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                    if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffff)) { revert(0, 0); } else {
                                        mstore(0xc0, 0x58f03bf700000000000000000000000000000000000000000000000000000000)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_628a9fd6(uint32 arg0, address arg1, address arg2) public payable returns (uint256)
            * @param                arg0 ["uint32", "bytes4", "int32"]
            * @param                arg1 ["address", "uint128", "bytes16", "int128"]
            * @param                arg2 ["address", "uint128", "bytes16", "int128"]
            */
            case 0x628a9fd6 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                    if iszero(eq(caller(), and(shr(0x10, sload(0)), 0xffffffffffffffffffffffffffffffffffffffff))) {
                                        if iszero(eq(caller(), and(sload(0x25), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(mload(0x40), 0x04); } else {
                                            mstore(0xc0, 0x989c4c7c00000000000000000000000000000000000000000000000000000000)
                                            if iszero(lt(and(calldataload(0x04), 0xffffffff), and(sload(0x08), 0xffffffff))) { revert(0, 0); } else {
                                                mstore(0, and(calldataload(0x04), 0xffffffff))
                                                mstore(0x20, 0x24)
                                                sstore(add(sha3(0, 0x40), 0x01), or(and(calldataload(0x24), 0xffffffffffffffffffffffffffffffff), and(shl(0x80, calldataload(0x44)), 0xffffffffffffffffffffffffffffffff00000000000000000000000000000000)))
                                                mstore(0xc0, and(calldataload(0x24), 0xffffffffffffffffffffffffffffffff))
                                                mstore(0xe0, and(calldataload(0x44), 0xffffffffffffffffffffffffffffffff))
                                                log2(mload(0x40), 0x40, 0xa065d6ba54c5124cd73ce640fd3fbc0ce6eb8a4f4c9d5155347dcc461ad0cffe, and(calldataload(0x04), 0xffffffff))
                                                return(0, 0)
                                                mstore(0xc0, 0x67207a8800000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_e53e3de6(address arg0, uint256 arg1) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            */
            case 0xe53e3de6 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x1f))) { revert(mload(0x40), 0x04); } else {
                                mstore(0xc0, 0x538ccdfd00000000000000000000000000000000000000000000000000000000)
                                if iszero(calldataload(0x24)) {
                                    mstore(0, caller())
                                    mstore(0x20, 0x09)
                                    if lt(sload(sha3(0, 0x40)), calldataload(0x24)) { revert(mload(0x40), 0x04); } else {
                                        mstore(0xc0, 0xf4d678b800000000000000000000000000000000000000000000000000000000)
                                        mstore(0, caller())
                                        mstore(0x20, 0x09)
                                        sstore(sha3(0, 0x40), sub(sload(sha3(0, 0x40)), calldataload(0x24)))
                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                        if gt(sload(sha3(0, 0x40)), add(sload(sha3(0, 0x40)), calldataload(0x24))) { revert(0, 0); } else {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x11)
                                            sstore(sha3(0, 0x40), add(sload(sha3(0, 0x40)), calldataload(0x24)))
                                            mstore(0xc0, calldataload(0x24))
                                            log2(mload(0x40), 0x20, 0xe7fd56edb8bf641db0dc0a89a9d7d3a10da1fedab015ab0c51f1c418d2bc15b0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                            return(0, 0)
                                            return(0, 0)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_f28bbdb2() public view returns (uint32)
            */
            case 0xf28bbdb2 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x08), 0xffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_a0bf0f75(address arg0) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xa0bf0f75 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(0, 0); } else {
                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x06, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x06))))
                                log2(0, 0, 0xaf80993709a0eea3136bd8cf21081dcc85e10d1df039a9267406920306fd0781, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                return(0, 0)
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_a25dc87f(address arg0) public view returns (bytes memory)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xa25dc87f {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x0c)
                            mstore(0xc0, sload(sha3(0, 0x40)))
                            mstore(0, sha3(0, 0x40))
                            if lt(0, sload(sha3(0, 0x40))) {
                                if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(mload(0x40), 0x20), mload(0x40)), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(mload(0x40), 0x20), mload(0x40)), 0x1f))), 0xffffffffffffffff)) {
                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                    mstore(0x04, 0x41)
                                    mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(mload(0x40), 0x20), mload(0x40)), 0x1f))))
                                    mstore(0xe0, 0x20)
                                    mstore(0x0100, mload(mload(0x40)))
                                    if lt(0, mload(mload(0x40))) { revert(0, 0); } else {
                                        return(mload(0x40), sub(add(mload(0x40), 0x40), mload(0x40)))
                                    }
                                }
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_6a3214c9(address arg0, uint256 arg1) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            */
            case 0x6a3214c9 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(mload(0x40), 0x04); } else {
                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                mstore(0x20, 0x21)
                                if sload(sha3(0, 0x40)) { revert(mload(0x40), 0x04); } else {
                                    mstore(0xc0, 0x28ef431400000000000000000000000000000000000000000000000000000000)
                                    if iszero(or(eq(div(mul(calldataload(0x24), sload(0x03)), calldataload(0x24)), sload(0x03)), iszero(calldataload(0x24)))) {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x11)
                                        if iszero(mul(calldataload(0x24), sload(0x03))) {
                                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                            mstore(0x20, 0x09)
                                            if gt(sload(sha3(0, 0x40)), add(sload(sha3(0, 0x40)), mul(calldataload(0x24), sload(0x03)))) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x11)
                                                sstore(sha3(0, 0x40), add(sload(sha3(0, 0x40)), mul(calldataload(0x24), sload(0x03))))
                                                if gt(add(and(0xffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffff, sload(0x16))), and(0xffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffff, mul(calldataload(0x24), sload(0x03))))), 0xffffffffffffffffffffffffffffffff) { revert(0, 0); } else {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x11)
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

            /*
            * @custom:signature    Unresolved_d7c7e5fb(uint32 arg0, uint32 arg1, address arg2) public payable returns (uint256)
            * @param                arg0 ["uint32", "bytes4", "int32"]
            * @param                arg1 ["uint32", "bytes4", "int32"]
            * @param                arg2 ["address", "uint120", "bytes15", "int120"]
            */
            case 0xd7c7e5fb {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffff)) { revert(0, 0); } else {
                                if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(mload(0x40), 0x04); } else {
                                    mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                    if iszero(lt(and(calldataload(0x04), 0xffffffff), and(sload(0x08), 0xffffffff))) {
                                        if iszero(iszero(and(calldataload(0x24), 0xffffffff))) {
                                            if iszero(calldataload(0x44)) {
                                                if gt(calldataload(0x44), 0xffffffffffffffffffffffffffffff) { revert(0, 0); } else {
                                                    mstore(0xc0, 0xb0cb274d00000000000000000000000000000000000000000000000000000000)
                                                    mstore(0, and(calldataload(0x04), 0xffffffff))
                                                    mstore(0x20, 0x07)
                                                    sstore(sha3(0, 0x40), or(and(0xffffffff00000000000000000000000000000000000000000000000000000000, shl(0xe0, calldataload(0x24))), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffff, sload(sha3(0, 0x40)))))
                                                    sstore(add(sha3(0, 0x40), 0x01), or(and(calldataload(0x44), 0xffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffff000000000000000000000000000000, sload(add(sha3(0, 0x40), 0x01)))))
                                                    mstore(0xc0, and(calldataload(0x24), 0xffffffff))
                                                    mstore(0xe0, calldataload(0x44))
                                                    log2(mload(0x40), 0x40, 0x62db1b2b923b6f20043c492d3586df1a823e447c63e44d15dbc90c1a3bc9fcc5, and(calldataload(0x04), 0xffffffff))
                                                    return(0, 0)
                                                    mstore(0xc0, 0xb0cb274d00000000000000000000000000000000000000000000000000000000)
                                                    mstore(0xc0, 0x67207a8800000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_efc1bd46(address arg0) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xefc1bd46 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(0, 0); } else {
                                mstore(0xc0, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x59, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x59))))
                                log2(0, 0, 0xabf32d7cef1e07c4d0e9f8a6e1af1ac77dff1a5f0e0b04263a53e8f0d0660083, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                return(0, 0)
                            }
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_48ee5e08() public view returns (uint256)
            */
            case 0x48ee5e08 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, sload(0x18))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_753a369c(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable returns (bytes memory)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            */
            case 0x753a369c {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x80) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0xc0, 0x3cf4208d00000000000000000000000000000000000000000000000000000000)
                            mstore(0xc4, 0x0f)
                            mstore(0xe4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x0104, calldataload(0x24))
                            mstore(0x0124, calldataload(0x44))
                            mstore(0x0144, calldataload(0x64))
                            mstore(0x0164, 0x0de0b6b3a7640000)
                            delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0xc4, mload(0x40), 0x60)
                            if iszero(delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0xc4, mload(0x40), 0x60)) { revert(mload(0x40), returndatasize()); } else {
                                returndatacopy(mload(0x40), 0, returndatasize())
                                if delegatecall(gas(), 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49, mload(0x40), 0xc4, mload(0x40), 0x60) {
                                    mstore(0xc0, 0)
                                    mstore(0xe0, 0)
                                    mstore(0x0100, 0)
                                    return(mload(0x40), sub(add(mload(0x40), 0x60), mload(0x40)))
                                    if gt(0x60, returndatasize()) {
                                        if or(lt(add(mload(0x40), 0x60), mload(0x40)), gt(add(mload(0x40), 0x60), 0xffffffffffffffff)) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x41)
                                            mstore(0x40, add(mload(0x40), 0x60))
                                            if slt(sub(add(mload(0x40), 0x60), mload(0x40)), 0x60) { revert(0, 0); } else {
                                                mstore(0x0120, mload(mload(0x40)))
                                                mstore(0x0140, mload(add(mload(0x40), 0x20)))
                                                mstore(0x0160, mload(add(mload(0x40), 0x40)))
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

            /*
            * @custom:signature    Unresolved_8d09f23f(address arg0, uint256 arg1, uint256 arg2, uint64 arg3, bool arg4, uint256 arg5, uint256 arg6) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint64", "bytes8", "int64"]
            * @param                arg4 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg5 ["uint256", "bytes32", "int256"]
            * @param                arg6 ["uint256", "bytes32", "int256"]
            */
            case 0x8d09f23f {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xe0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x84), and(calldataload(0x84), 0xff)) { revert(0, 0); } else {
                                    if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04))) {
                                        mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                        mstore(0x20, 0x22)
                                        if iszero(gt(number(), sload(sha3(0, 0x40)))) { revert(mload(0x40), 0x04); } else {
                                            mstore(0xc0, 0x4f57ffae00000000000000000000000000000000000000000000000000000000)
                                            if iszero(extcodesize(and(shr(0x08, sload(0x1d)), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0); } else {
                                                mstore(0xc0, 0xb002b9fa00000000000000000000000000000000000000000000000000000000)
                                                mstore(0xc4, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                mstore(0xe4, calldataload(0x44))
                                                mstore(0x0104, and(calldataload(0x64), 0xffffffffffffffff))
                                                call(gas(), and(shr(0x08, sload(0x1d)), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), sub(add(0x60, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0)
                                                if iszero(call(gas(), and(shr(0x08, sload(0x1d)), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), sub(add(0x60, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                    returndatacopy(mload(0x40), 0, returndatasize())
                                                    if call(gas(), and(shr(0x08, sload(0x1d)), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), sub(add(0x60, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0) {
                                                        mstore(0xe0, 0xac4ddb8d63e9d7a862c5d61ce47517623a448262414a7eef6797102104b31214)
                                                        mstore(0x0100, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                        mstore(0x0120, calldataload(0x24))
                                                        mstore(0x0140, calldataload(0x44))
                                                        mstore(0x0160, and(0xffffffffffffffff, calldataload(0x64)))
                                                        mstore(0xc0, 0xa0)
                                                        if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            mstore(0x40, add(mload(0x40), 0xc0))
                                                            mstore(0x0180, 0xd45167d000000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x0184, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                            mstore(0x01a4, and(calldataload(0x84), 0xff))
                                                            mstore(0x01c4, calldataload(0xa4))
                                                            mstore(0x01e4, calldataload(0xc4))
                                                            staticcall(gas(), and(shr(0x08, sload(0x1d)), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x84, mload(0x40), 0x20)
                                                            if iszero(staticcall(gas(), and(shr(0x08, sload(0x1d)), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x84, mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                returndatacopy(mload(0x40), 0, returndatasize())
                                                                if staticcall(gas(), and(shr(0x08, sload(0x1d)), 0xffffffffffffffffffffffffffffffffffffffff), mload(0x40), 0x84, mload(0x40), 0x20) {
                                                                    if iszero(iszero(0)) {
                                                                        if iszero(eq(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))) { revert(mload(0x40), 0x04); } else {
                                                                            mstore(0x0180, 0xc20280ea00000000000000000000000000000000000000000000000000000000)
                                                                            if iszero(or(eq(div(mul(calldataload(0x24), sload(0x03)), calldataload(0x24)), sload(0x03)), iszero(calldataload(0x24)))) {
                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                mstore(0x04, 0x11)
                                                                                if iszero(0) { revert(mload(0x40), 0x04); } else {
                                                                                    mstore(0x0180, 0xc20280ea00000000000000000000000000000000000000000000000000000000)
                                                                                    if gt(0x20, returndatasize()) {
                                                                                        if or(lt(add(mload(0x40), 0x20), mload(0x40)), gt(add(mload(0x40), 0x20), 0xffffffffffffffff)) {
                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                            mstore(0x04, 0x41)
                                                                                            mstore(0x40, add(mload(0x40), 0x20))
                                                                                            if slt(sub(add(mload(0x40), 0x20), mload(0x40)), 0x20) { revert(0, 0); } else {
                                                                                                if sub(mload(mload(0x40)), and(mload(mload(0x40)), 0xffffffffffffffffffffffffffffffffffffffff)) {
                                                                                                    if iszero(iszero(and(mload(mload(0x40)), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(0, 0); } else {
                                                                                                    }
                                                                                                    if gt(mload(0x40), 0xffffffffffffffff) {
                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                        mstore(0x04, 0x41)
                                                                                                        mstore(0x40, mload(0x40))
                                                                                                        if 0 { revert(0, 0); } else {
                                                                                                            mstore(0xc0, 0xc20280ea00000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_96523644() public view returns (uint256)
            */
            case 0x96523644 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, sload(0x10))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_7d004aeb() public view returns (uint256)
            */
            case 0x7d004aeb {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, shr(0x80, sload(0x1a)))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_99fbab88(uint256 arg0) public view returns (bool)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x99fbab88 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) { revert(0, 0); } else {
                        mstore(0, calldataload(0x04))
                        mstore(0x20, 0x0a)
                        mstore(0xc0, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff))
                        mstore(0xe0, and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffff))
                        mstore(0x0100, shr(0xc0, sload(sha3(0, 0x40))))
                        mstore(0x0120, and(sload(add(sha3(0, 0x40), 0x01)), 0xffffffffffffffffffffffffffffffff))
                        mstore(0x0140, and(shr(0x80, sload(add(sha3(0, 0x40), 0x01))), 0xffffffff))
                        mstore(0x0160, and(shr(0xa0, sload(add(sha3(0, 0x40), 0x01))), 0xffffffffffffffff))
                        mstore(0x0180, iszero(iszero(and(shr(0xe0, sload(add(sha3(0, 0x40), 0x01))), 0xff))))
                        mstore(0x01a0, iszero(iszero(and(shr(0xe8, sload(add(sha3(0, 0x40), 0x01))), 0xff))))
                        mstore(0x01c0, iszero(iszero(and(shr(0xf0, sload(add(sha3(0, 0x40), 0x01))), 0xff))))
                        return(mload(0x40), 0x0120)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_24a3d622() public view returns (address)
            */
            case 0x24a3d622 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(sload(0x01), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_61d027b3() public view returns (uint256)
            */
            case 0x61d027b3 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0xc0, sload(0x0e))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_f84a74d3(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xf84a74d3 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x20)
                            mstore(0xc0, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_0b826190() public view returns (address)
            */
            case 0x0b826190 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0xc0, and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x08, sload(0x1d))))
                        return(mload(0x40), 0x20)
                    }
                }
            }

            /*
            * @custom:signature    Unresolved_415f1240(uint256 arg0) public payable
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0x415f1240 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if or(gt(add(mload(0x40), 0x20), 0xffffffffffffffff), lt(add(mload(0x40), 0x20), mload(0x40))) {
                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                            mstore(0x04, 0x41)
                            mstore(0x40, add(mload(0x40), 0x20))
                            mstore(0xc0, 0)
                            if or(gt(add(mload(0x40), 0x20), 0xffffffffffffffff), lt(add(mload(0x40), 0x20), mload(0x40))) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x41)
                                mstore(0x40, add(mload(0x40), 0x20))
                                mstore(0xe0, 0)
                                mstore(0, calldataload(0x04))
                                mstore(0x20, 0x0a)
                                if iszero(and(shr(0xf0, sload(add(sha3(0, 0x40), 0x01))), 0xff)) {
                                    mstore(0, and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffff))
                                    mstore(0x20, 0x07)
                                    if lt(and(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffff), 0xffffffff), mload(mload(0x40))) {
                                        if iszero(lt(and(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffff), 0xffffffff), mload(mload(0x40)))) {
                                            if iszero(lt(and(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffff), 0xffffffff), mload(mload(0x40)))) {
                                                if iszero(mload(add(add(shl(0x05, and(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffff), 0xffffffff)), mload(0x40)), 0x20))) {
                                                    mstore(0, and(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffff), 0xffffffff))
                                                    mstore(0x20, 0x23)
                                                    if and(sload(sha3(0, 0x40)), 0xff) {
                                                        if gt(and(0xffffffffffffffff, shr(0x08, sload(sha3(0, 0x40)))), add(and(0xffffffffffffffff, shr(0x08, sload(sha3(0, 0x40)))), and(0xffffffffffffffff, shr(0x48, sload(sha3(0, 0x40)))))) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x11)
                                                            if iszero(lt(and(and(shr(0xa0, sload(sha3(0, 0x40))), 0xffffffff), 0xffffffff), mload(mload(0x40)))) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x32)
                                                                mstore(0x0100, 0xc018266900000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x0104, and(0xffffffff, and(shr(0xc0, sload(sha3(0, 0x40))), 0xffffffff)))
                                                                staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), mload(0x40), 0x24, mload(0x40), 0x20)
                                                                if iszero(staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), mload(0x40), 0x24, mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                    returndatacopy(mload(0x40), 0, returndatasize())
                                                                    if staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), mload(0x40), 0x24, mload(0x40), 0x20) {
                                                                        if gt(0x20, returndatasize()) {
                                                                            if or(lt(add(mload(0x40), 0x20), mload(0x40)), gt(add(mload(0x40), 0x20), 0xffffffffffffffff)) {
                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                mstore(0x04, 0x41)
                                                                                mstore(0x40, add(mload(0x40), 0x20))
                                                                                if slt(sub(add(mload(0x40), 0x20), mload(0x40)), 0x20) { revert(0, 0); } else {
                                                                                    if sub(mload(mload(0x40)), and(mload(mload(0x40)), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                        mstore(0x04, 0x32)
                                                                                        mstore(0x0100, 0x94e88a2100000000000000000000000000000000000000000000000000000000)
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
            default { revert(0, 0) }
        }
    }
}
