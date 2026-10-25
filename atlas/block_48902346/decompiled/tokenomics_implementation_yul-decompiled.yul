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
            * @custom:signature    Unresolved_12baae3b(uint256 arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            */
            case 0x12baae3b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x80) {
                        if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(mload(0x40), 0x04); } else {
                            mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                            if iszero(iszero(calldataload(0x04))) {
                                if iszero(iszero(calldataload(0x24))) {
                                    if iszero(iszero(calldataload(0x44))) {
                                        if iszero(iszero(calldataload(0x64))) {
                                            if lt(calldataload(0x24), calldataload(0x04)) { revert(mload(0x40), 0x04); } else {
                                                mstore(0x80, 0xbad8ef9500000000000000000000000000000000000000000000000000000000)
                                                codecopy(0, 0x0c47, 0x20)
                                                mstore(0, mload(0))
                                                sstore(0x05, calldataload(0x04))
                                                sstore(0x06, calldataload(0x24))
                                                sstore(0x07, calldataload(0x44))
                                                sstore(0x08, calldataload(0x64))
                                                mstore(0x80, calldataload(0x04))
                                                mstore(0xa0, calldataload(0x24))
                                                mstore(0xc0, calldataload(0x44))
                                                mstore(0xe0, calldataload(0x64))
                                                log1(mload(0x40), 0x80, mload(0))
                                                if iszero(calldataload(0x64)) { revert(0, 0); } else {
                                                    codecopy(0, 0x0c47, 0x20)
                                                    mstore(0, mload(0))
                                                    sstore(0x05, calldataload(0x04))
                                                    sstore(0x06, calldataload(0x24))
                                                    sstore(0x07, calldataload(0x44))
                                                    sstore(0x08, calldataload(0x64))
                                                    mstore(0x80, calldataload(0x04))
                                                    mstore(0xa0, calldataload(0x24))
                                                    mstore(0xc0, calldataload(0x44))
                                                    mstore(0xe0, calldataload(0x64))
                                                    log1(mload(0x40), 0x80, mload(0))
                                                    mstore(0x80, 0xbad8ef9500000000000000000000000000000000000000000000000000000000)
                                                }
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
            * @custom:signature    Unresolved_c218c676(uint256 arg0) public payable
            * @param                arg0 ["uint256", "bytes32", "int256"]
            */
            case 0xc218c676 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x01))) { revert(mload(0x40), 0x04); } else {
                            mstore(0x80, 0xe343677f00000000000000000000000000000000000000000000000000000000)
                            if iszero(calldataload(0x04)) {
                                if iszero(sgt(sload(0x03), sload(0x06))) {
                                    if or(and(slt(sub(sload(0x03), sload(0x06)), sload(0x03)), sgt(0, sload(0x06))), and(sgt(sub(sload(0x03), sload(0x06)), sload(0x03)), iszero(sgt(0, sload(0x06))))) {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x11)
                                        if gt(calldataload(0x04), sub(sload(0x03), sload(0x06))) { revert(mload(0x40), 0x04); } else {
                                            mstore(0x80, 0xe247b81f00000000000000000000000000000000000000000000000000000000)
                                            if or(and(slt(sub(sload(0x03), calldataload(0x04)), sload(0x03)), sgt(0, calldataload(0x04))), and(sgt(sub(sload(0x03), calldataload(0x04)), sload(0x03)), iszero(sgt(0, calldataload(0x04))))) { revert(0, 0); } else {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x11)
                                                sstore(0x03, sub(sload(0x03), calldataload(0x04)))
                                                mstore(0x80, calldataload(0x04))
                                                mstore(0xa0, sub(sload(0x03), calldataload(0x04)))
                                                mstore(0xc0, sload(0x04))
                                                log1(mload(0x40), 0x60, 0x09f6ca7b163aa16d9feb37c8882b930e40c3e111f64037cb2b00adf65693e14f)
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
            * @custom:signature    Unresolved_7c7df7b4(address arg0, uint64 arg1, bool arg2) public pure
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg3 ["uint64", "bytes8", "int64"]
            * @param                arg4 ["bool", "uint8", "bytes1", "int8"]
            */
            case 0x7c7df7b4 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xe0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(and(calldataload(0x64), 0xffffffffffffffff), calldataload(0x64)) { revert(0, 0); } else {
                                if sub(and(calldataload(0x84), 0xff), calldataload(0x84)) { revert(0, 0); } else {
                                    mstore(0x80, 0x32aa90b000000000000000000000000000000000000000000000000000000000)
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_ed722c96(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            */
            case 0xed722c96 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x80) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x01))) { revert(mload(0x40), 0x04); } else {
                                mstore(0x80, 0xe343677f00000000000000000000000000000000000000000000000000000000)
                                if gt(calldataload(0x64), calldataload(0x44)) { revert(mload(0x40), 0x04); } else {
                                    mstore(0x80, 0x85c5839600000000000000000000000000000000000000000000000000000000)
                                    if calldataload(0x24) {
                                        if or(and(slt(sub(sload(0x03), calldataload(0x24)), sload(0x03)), sgt(0, calldataload(0x24))), and(sgt(sub(sload(0x03), calldataload(0x24)), sload(0x03)), iszero(sgt(0, calldataload(0x24))))) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x11)
                                            sstore(0x03, sub(sload(0x03), calldataload(0x24)))
                                            if iszero(calldataload(0x44)) {
                                                if or(and(iszero(slt(sload(0x03), 0)), slt(add(sload(0x03), calldataload(0x64)), calldataload(0x64))), and(slt(sload(0x03), 0), iszero(slt(add(sload(0x03), calldataload(0x64)), calldataload(0x64))))) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x11)
                                                    if calldataload(0x64) {
                                                        sstore(0x03, add(sload(0x03), calldataload(0x64)))
                                                        mstore(0x80, 0x7aac24ba00000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x84, sload(0x03))
                                                        mstore(0xa4, sload(0x04))
                                                        mstore(0xc4, calldataload(0x44))
                                                        mstore(0xe4, sload(0x05))
                                                        mstore(0x0104, sload(0x07))
                                                        mstore(0x0124, sload(0x08))
                                                        delegatecall(gas(), 0xe991817199363046da0a28da6fbad0284e4aa492, mload(0x40), sub(add(add(mload(0x40), 0x04), 0xc0), mload(0x40)), mload(0x40), 0x40)
                                                        if iszero(delegatecall(gas(), 0xe991817199363046da0a28da6fbad0284e4aa492, mload(0x40), sub(add(add(mload(0x40), 0x04), 0xc0), mload(0x40)), mload(0x40), 0x40)) { revert(mload(0x40), returndatasize()); } else {
                                                            returndatacopy(mload(0x40), 0, returndatasize())
                                                            if delegatecall(gas(), 0xe991817199363046da0a28da6fbad0284e4aa492, mload(0x40), sub(add(add(mload(0x40), 0x04), 0xc0), mload(0x40)), mload(0x40), 0x40) {
                                                                if 0 {
                                                                    if gt(sload(0x04), add(sload(0x04), 0)) {
                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                        mstore(0x04, 0x11)
                                                                        sstore(0x04, add(sload(0x04), 0))
                                                                        if iszero(iszero(0)) {
                                                                            if iszero(iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)))) {
                                                                                if iszero(extcodesize(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)))) { revert(0, 0); } else {
                                                                                    mstore(0x80, 0x40c10f1900000000000000000000000000000000000000000000000000000000)
                                                                                    mstore(0x84, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                    mstore(0xa4, 0)
                                                                                    call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), 0, mload(0x40), sub(add(0x40, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0)
                                                                                    if iszero(call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), 0, mload(0x40), sub(add(0x40, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                                                        returndatacopy(mload(0x40), 0, returndatasize())
                                                                                        codecopy(0, 0x0ca7, 0x20)
                                                                                        mstore(0, mload(0))
                                                                                        if call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), 0, mload(0x40), sub(add(0x40, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0) {
                                                                                            mstore(0x80, calldataload(0x24))
                                                                                            mstore(0xa0, calldataload(0x44))
                                                                                            mstore(0xc0, sload(0x03))
                                                                                            mstore(0xe0, add(sload(0x03), calldataload(0x64)))
                                                                                            mstore(0x0100, 0)
                                                                                            mstore(0x0120, 0)
                                                                                            codecopy(0, 0x0ca7, 0x20)
                                                                                            mstore(0, mload(0))
                                                                                            log2(mload(0x40), 0xc0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                            if gt(mload(0x40), 0xffffffffffffffff) {
                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                mstore(0x04, 0x41)
                                                                                                mstore(0x40, mload(0x40))
                                                                                                mstore(0x80, calldataload(0x24))
                                                                                                mstore(0xa0, calldataload(0x44))
                                                                                                mstore(0xc0, sload(0x03))
                                                                                                mstore(0xe0, add(sload(0x03), calldataload(0x64)))
                                                                                                mstore(0x0100, 0)
                                                                                                mstore(0x0120, 0)
                                                                                                codecopy(0, 0x0ca7, 0x20)
                                                                                                mstore(0, mload(0))
                                                                                                log2(mload(0x40), 0xc0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                mstore(0x80, calldataload(0x24))
                                                                                                mstore(0xa0, calldataload(0x44))
                                                                                                mstore(0xc0, sload(0x03))
                                                                                                mstore(0xe0, add(sload(0x03), calldataload(0x64)))
                                                                                                mstore(0x0100, 0)
                                                                                                mstore(0x0120, 0)
                                                                                                codecopy(0, 0x0ca7, 0x20)
                                                                                                mstore(0, mload(0))
                                                                                                log2(mload(0x40), 0xc0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                if gt(0x40, returndatasize()) {
                                                                                                    if or(lt(add(mload(0x40), 0x40), mload(0x40)), gt(add(mload(0x40), 0x40), 0xffffffffffffffff)) {
                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                        mstore(0x04, 0x41)
                                                                                                        mstore(0x40, add(mload(0x40), 0x40))
                                                                                                        if slt(sub(add(mload(0x40), 0x40), mload(0x40)), 0x40) { revert(0, 0); } else {
                                                                                                            codecopy(0, 0x0ca7, 0x20)
                                                                                                            mstore(0, mload(0))
                                                                                                            mstore(0x80, calldataload(0x24))
                                                                                                            mstore(0xa0, 0)
                                                                                                            mstore(0xc0, sload(0x03))
                                                                                                            mstore(0xe0, sload(0x03))
                                                                                                            mstore(0x0100, 0)
                                                                                                            mstore(0x0120, 0)
                                                                                                            log2(mload(0x40), 0xc0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                        }
                                                                                                    }
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_485cc955(address arg0, address arg1) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x485cc955 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))) { revert(0, 0); } else {
                                if and(sload(0), 0xff) {
                                    if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                        codecopy(0, 0x0c47, 0x20)
                                        mstore(0, mload(0))
                                        if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                            sstore(0, or(and(sload(0), 0xffffffffffffffffffff0000000000000000000000000000000000000000ffff), and(shl(0x10, calldataload(0x04)), 0xffffffffffffffffffffffffffffffffffffffff0000)))
                                            sstore(0x01, or(and(sload(0x01), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))))
                                            sstore(0x05, 0x01a784379d99db42000000)
                                            sstore(0x06, 0x0422ca8b0a00a425000000)
                                            sstore(0x07, 0x056bc75e2d63100000)
                                            sstore(0x08, 0x6342fd08f00f6378000000)
                                            codecopy(0, 0x0c67, 0x20)
                                            mstore(0, mload(0))
                                            log2(0, 0, mload(0), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                            mstore(0x80, 0x01a784379d99db42000000)
                                            mstore(0xa0, 0x0422ca8b0a00a425000000)
                                            mstore(0xc0, 0x056bc75e2d63100000)
                                            mstore(0xe0, 0x6342fd08f00f6378000000)
                                            log1(mload(0x40), 0x80, mload(0))
                                            if iszero(and(shr(0x08, sload(0)), 0xff)) { revert(mload(0x40), 0x04); } else {
                                                sstore(0, or(and(0xffffffffffffffffffff000000000000000000000000000000000000000000ff, sload(0)), and(shl(0x10, calldataload(0x04)), 0xffffffffffffffffffffffffffffffffffffffff0000)))
                                                mstore(0x80, 0x0dc149f000000000000000000000000000000000000000000000000000000000)
                                                if and(sload(0), 0xff) { revert(0, 0); } else {
                                                    mstore(0x80, 0x0dc149f000000000000000000000000000000000000000000000000000000000)
                                                }
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
                        mstore(0x80, and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0))))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_1c3972ba() public view returns (uint256)
            */
            case 0x1c3972ba {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x07))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_d2f7265a() public view returns (address)
            */
            case 0xd2f7265a {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x01), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_fe16eae8() public pure
            */
            case 0xfe16eae8 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) { revert(0, 0); } else {
                        mstore(0x80, 0x32aa90b000000000000000000000000000000000000000000000000000000000)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_ae745703() public view returns (uint256)
            */
            case 0xae745703 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        if iszero(sgt(sload(0x03), sload(0x06))) {
                            if or(and(slt(sub(sload(0x03), sload(0x06)), sload(0x03)), sgt(0, sload(0x06))), and(sgt(sub(sload(0x03), sload(0x06)), sload(0x03)), iszero(sgt(0, sload(0x06))))) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x11)
                                mstore(0x80, sub(sload(0x03), sload(0x06)))
                                return(mload(0x40), 0x20)
                                mstore(0x80, 0)
                                return(mload(0x40), 0x20)
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_e9ed73e9() public view returns (uint256)
            */
            case 0xe9ed73e9 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x05))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_cbb451da() public view returns (uint256)
            */
            case 0xcbb451da {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x08))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_0efdf838(address arg0, uint256 arg1, uint256 arg2, uint256 arg3, uint256 arg4) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            */
            case 0x0efdf838 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xa0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x44), iszero(iszero(calldataload(0x44)))) { revert(0, 0); } else {
                                if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x01))) { revert(0x80, 0x04); } else {
                                    mstore(0x80, 0xe343677f00000000000000000000000000000000000000000000000000000000)
                                    if gt(calldataload(0x84), calldataload(0x64)) { revert(mload(0x40), 0x04); } else {
                                        mstore(0x80, 0x85c5839600000000000000000000000000000000000000000000000000000000)
                                        if iszero(calldataload(0x64)) {
                                            if or(and(iszero(slt(sload(0x03), 0)), slt(add(sload(0x03), calldataload(0x84)), calldataload(0x84))), and(slt(sload(0x03), 0), iszero(slt(add(sload(0x03), calldataload(0x84)), calldataload(0x84))))) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x11)
                                                if calldataload(0x84) {
                                                    sstore(0x03, add(sload(0x03), calldataload(0x84)))
                                                    mstore(0x80, 0x7aac24ba00000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x84, sload(0x03))
                                                    mstore(0xa4, sload(0x04))
                                                    mstore(0xc4, calldataload(0x64))
                                                    mstore(0xe4, sload(0x05))
                                                    mstore(0x0104, sload(0x07))
                                                    mstore(0x0124, sload(0x08))
                                                    delegatecall(gas(), 0xe991817199363046da0a28da6fbad0284e4aa492, mload(0x40), sub(add(add(mload(0x40), 0x04), 0xc0), mload(0x40)), mload(0x40), 0x40)
                                                    if iszero(delegatecall(gas(), 0xe991817199363046da0a28da6fbad0284e4aa492, mload(0x40), sub(add(add(mload(0x40), 0x04), 0xc0), mload(0x40)), mload(0x40), 0x40)) { revert(mload(0x40), returndatasize()); } else {
                                                        returndatacopy(mload(0x40), 0, returndatasize())
                                                        if delegatecall(gas(), 0xe991817199363046da0a28da6fbad0284e4aa492, mload(0x40), sub(add(add(mload(0x40), 0x04), 0xc0), mload(0x40)), mload(0x40), 0x40) {
                                                            if 0 {
                                                                if gt(sload(0x04), add(sload(0x04), 0)) {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x11)
                                                                    sstore(0x04, add(sload(0x04), 0))
                                                                    if iszero(iszero(0)) {
                                                                        if iszero(iszero(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)))) {
                                                                            if iszero(extcodesize(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)))) { revert(0, 0); } else {
                                                                                mstore(0x80, 0x40c10f1900000000000000000000000000000000000000000000000000000000)
                                                                                mstore(0x84, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                mstore(0xa4, 0)
                                                                                call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), 0, mload(0x40), sub(add(0x40, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0)
                                                                                if iszero(call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), 0, mload(0x40), sub(add(0x40, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                                                    returndatacopy(mload(0x40), 0, returndatasize())
                                                                                    codecopy(0, 0x0c87, 0x20)
                                                                                    mstore(0, mload(0))
                                                                                    if call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), 0, mload(0x40), sub(add(0x40, add(mload(0x40), 0x04)), mload(0x40)), mload(0x40), 0) {
                                                                                        mstore(0x80, iszero(iszero(calldataload(0x44))))
                                                                                        mstore(0xa0, calldataload(0x64))
                                                                                        mstore(0xc0, sload(0x03))
                                                                                        mstore(0xe0, add(sload(0x03), calldataload(0x84)))
                                                                                        mstore(0x0100, 0)
                                                                                        mstore(0x0120, 0)
                                                                                        codecopy(0, 0x0c87, 0x20)
                                                                                        mstore(0, mload(0))
                                                                                        log3(mload(0x40), 0xc0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), calldataload(0x24))
                                                                                        if gt(mload(0x40), 0xffffffffffffffff) {
                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                            mstore(0x04, 0x41)
                                                                                            mstore(0x40, mload(0x40))
                                                                                            mstore(0x80, iszero(iszero(calldataload(0x44))))
                                                                                            mstore(0xa0, calldataload(0x64))
                                                                                            mstore(0xc0, sload(0x03))
                                                                                            mstore(0xe0, add(sload(0x03), calldataload(0x84)))
                                                                                            mstore(0x0100, 0)
                                                                                            mstore(0x0120, 0)
                                                                                            codecopy(0, 0x0c87, 0x20)
                                                                                            mstore(0, mload(0))
                                                                                            log3(mload(0x40), 0xc0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), calldataload(0x24))
                                                                                            mstore(0x80, iszero(iszero(calldataload(0x44))))
                                                                                            mstore(0xa0, calldataload(0x64))
                                                                                            mstore(0xc0, sload(0x03))
                                                                                            mstore(0xe0, add(sload(0x03), calldataload(0x84)))
                                                                                            mstore(0x0100, 0)
                                                                                            mstore(0x0120, 0)
                                                                                            codecopy(0, 0x0c87, 0x20)
                                                                                            mstore(0, mload(0))
                                                                                            log3(mload(0x40), 0xc0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), calldataload(0x24))
                                                                                            if gt(0x40, returndatasize()) {
                                                                                                if or(lt(add(mload(0x40), 0x40), mload(0x40)), gt(add(mload(0x40), 0x40), 0xffffffffffffffff)) {
                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                    mstore(0x04, 0x41)
                                                                                                    mstore(0x40, add(mload(0x40), 0x40))
                                                                                                    if slt(sub(add(mload(0x40), 0x40), mload(0x40)), 0x40) { revert(0, 0); } else {
                                                                                                    }
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_3886cade() public view returns (uint256)
            */
            case 0x3886cade {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x05))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_8cf554a7() public view returns (uint256)
            */
            case 0x8cf554a7 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x03))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_98255e15() public view returns (address)
            */
            case 0x98255e15 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_e6ee2285(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xe6ee2285 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x02, or(and(sload(0x02), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)))
                                log2(0, 0, 0x430bfdc2fc284dd0409a30c5119cc184eb9971421e45c37bc9904ce47fb2ffef, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_db006a75() public pure
            */
            case 0xdb006a75 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) { revert(0, 0); } else {
                        mstore(0x80, 0x32aa90b000000000000000000000000000000000000000000000000000000000)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_c16017ca() public view returns (uint256)
            */
            case 0xc16017ca {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x06))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_dc5682d2() public view returns (uint256)
            */
            case 0xdc5682d2 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x04))
                        return(mload(0x40), 0x20)
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
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0, or(and(0xffffffffffffffffffffffffffffffffffffffff0000, shl(0x10, calldataload(0x04))), and(0xffffffffffffffffffff0000000000000000000000000000000000000000ffff, sload(0))))
                                codecopy(0, 0x0c67, 0x20)
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