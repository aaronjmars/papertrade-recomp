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
            * @custom:signature    Unresolved_c4d66de8(address arg0) public pure
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xc4d66de8 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0x80, 0xb7b2509c00000000000000000000000000000000000000000000000000000000)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_29710388(address arg0) public view returns (bool)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x29710388 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x02)
                            mstore(0x80, iszero(iszero(and(sload(sha3(0, 0x40)), 0xff))))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_d600539a(address arg0) public view
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xd600539a {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0xa0, and(0xffffffffffffffffffffffffffffffffffffffff000000000000000000000000, shl(0x60, calldataload(0x04))))
                            mstore(0x80, 0x14)
                            if or(gt(add(mload(0x40), 0x40), 0xffffffffffffffff), lt(add(mload(0x40), 0x40), mload(0x40))) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x41)
                                mstore(0x40, add(mload(0x40), 0x40))
                                if or(lt(add(mload(0x40), 0x0760), mload(0x40)), gt(add(mload(0x40), 0x0760), 0xffffffffffffffff)) {
                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                    mstore(0x04, 0x41)
                                    mstore(0x40, add(mload(0x40), 0x0760))
                                    mstore(0xc0, 0x0721)
                                    codecopy(add(mload(0x40), 0x20), 0x07b7, 0x0721)
                                    mstore(0x0840, and(0xffffffffffffffffffffffffffffffffffffffff, and(shr(0x10, sload(0)), 0xffffffffffffffffffffffffffffffffffffffff)))
                                    mstore(0x0860, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                    mstore(0x0820, add(sub(add(0x40, add(mload(0x40), 0x20)), mload(0x40)), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
                                    if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(0x40, add(mload(0x40), 0x20)), mload(0x40)), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(0x40, add(mload(0x40), 0x20)), mload(0x40)), 0x1f))), 0xffffffffffffffff)) {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x41)
                                        mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(sub(add(0x40, add(mload(0x40), 0x20)), mload(0x40)), 0x1f))))
                                        if lt(0, mload(mload(0x40))) { revert(0, 0); } else {
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_56e8d85b(address arg0, address arg1, address arg2) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x56e8d85b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                    if and(sload(0), 0xff) {
                                        if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                            if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                                if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))) {
                                                    if iszero(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) {
                                                        sstore(0, or(and(0xffffffffffffffffffff0000000000000000000000000000000000000000ffff, sload(0)), and(shl(0x10, calldataload(0x04)), 0xffffffffffffffffffffffffffffffffffffffff0000)))
                                                        sstore(0x03, or(and(sload(0x03), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24))))
                                                        sstore(0x04, or(and(sload(0x04), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                        codecopy(0, 0x0ef8, 0x20)
                                                        mstore(0, mload(0))
                                                        log2(0, 0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)))
                                                        codecopy(0, 0x0ed8, 0x20)
                                                        mstore(0, mload(0))
                                                        log2(0, 0, mload(0), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        if iszero(and(shr(0x08, sload(0)), 0xff)) { revert(mload(0x40), 0x04); } else {
                                                            sstore(0, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00ff, sload(0)))
                                                            mstore(0x80, 0x40892c3300000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x80, 0x904bc50300000000000000000000000000000000000000000000000000000000)
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
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_c1a9a508(address arg0) public view returns (address)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xc1a9a508 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x01)
                            mstore(0x80, and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_0f71c8bc(address arg0, address arg1) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x0f71c8bc {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103))) { revert(mload(0x40), 0x04); } else {
                                    mstore(0x80, 0xc031a0df00000000000000000000000000000000000000000000000000000000)
                                    if and(sload(0x03), 0xffffffffffffffffffffffffffffffffffffffff) { revert(mload(0x40), 0x04); } else {
                                        mstore(0x80, 0x3f733c4f00000000000000000000000000000000000000000000000000000000)
                                        if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04))) {
                                            if iszero(and(and(shr(0x10, sload(0)), 0xffffffffffffffffffffffffffffffffffffffff), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                sstore(0, or(and(0xffffffffffffffffffff0000000000000000000000000000000000000000ffff, sload(0)), and(shl(0x10, and(shr(0x10, sload(0)), 0xffffffffffffffffffffffffffffffffffffffff)), 0xffffffffffffffffffffffffffffffffffffffff0000)))
                                                sstore(0x03, or(and(sload(0x03), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04))))
                                                sstore(0x04, or(and(sload(0x04), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                codecopy(0, 0x0ef8, 0x20)
                                                mstore(0, mload(0))
                                                log2(0, 0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                codecopy(0, 0x0ed8, 0x20)
                                                mstore(0, mload(0))
                                                log2(0, 0, mload(0), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
                                                mstore(0x80, 0x40892c3300000000000000000000000000000000000000000000000000000000)
                                                mstore(0x80, 0x904bc50300000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_c6f881bc(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xc6f881bc {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x03))) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x04, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x04))))
                                codecopy(0, 0x0ed8, 0x20)
                                mstore(0, mload(0))
                                log2(0, 0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
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
                            if sub(caller(), and(sload(0x03), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(mload(0x40), 0x04); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                if iszero(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                    sstore(0x03, or(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x03))))
                                    codecopy(0, 0x0ef8, 0x20)
                                    mstore(0, mload(0))
                                    log2(0, 0, mload(0), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                    mstore(0x80, 0x904bc50300000000000000000000000000000000000000000000000000000000)
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_03b802b6() public view returns (address)
            */
            case 0x03b802b6 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x04)))
                        return(0x80, 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_d2f7265a() public view returns (address)
            */
            case 0xd2f7265a {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0))))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_cbd433f4(address arg0) public payable returns (address)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xcbd433f4 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if iszero(eq(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x03)))) {
                                if iszero(eq(caller(), and(sload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(mload(0x40), 0x04); } else {
                                    mstore(0x80, 0x27fba80a00000000000000000000000000000000000000000000000000000000)
                                    if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) {
                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                        mstore(0x20, 0x01)
                                        if and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff) {
                                            mstore(0x80, and(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffff), 0xffffffffffffffffffffffffffffffffffffffff))
                                            return(mload(0x40), 0x20)
                                            mstore(0xa0, and(0xffffffffffffffffffffffffffffffffffffffff000000000000000000000000, shl(0x60, calldataload(0x04))))
                                            mstore(0x80, 0x14)
                                            if or(gt(add(mload(0x40), 0x40), 0xffffffffffffffff), lt(add(mload(0x40), 0x40), mload(0x40))) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                mstore(0x40, add(mload(0x40), 0x40))
                                                if or(gt(add(mload(0x40), 0x0721), 0xffffffffffffffff), lt(add(mload(0x40), 0x0721), mload(0x40))) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x41)
                                                    codecopy(mload(0x40), 0x07b7, 0x0721)
                                                    mstore(0x07e1, and(0xffffffffffffffffffffffffffffffffffffffff, and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))))
                                                    mstore(0x0801, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                    create2(0, mload(0x40), sub(add(0x40, add(mload(0x40), 0x0721)), mload(0x40)), sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                    if iszero(create2(0, mload(0x40), sub(add(0x40, add(mload(0x40), 0x0721)), mload(0x40)), sha3(add(mload(0x40), 0x20), mload(mload(0x40))))) { revert(0, 0); } else {
                                                        returndatacopy(mload(0x40), 0, returndatasize())
                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        mstore(0x20, 0x01)
                                                        sstore(sha3(0, 0x40), or(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(create2(0, mload(0x40), sub(add(0x40, add(mload(0x40), 0x0721)), mload(0x40)), sha3(add(mload(0x40), 0x20), mload(mload(0x40)))), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                        mstore(0, and(create2(0, mload(0x40), sub(add(0x40, add(mload(0x40), 0x0721)), mload(0x40)), sha3(add(mload(0x40), 0x20), mload(mload(0x40)))), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        mstore(0x20, 0x02)
                                                        sstore(sha3(0, 0x40), or(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00), 0x01))
                                                        log3(0, 0, 0x3d2489efb661e8b1c3679865db649ca1de61d76a71184a1234de2e55786a6aad, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), and(create2(0, mload(0x40), sub(add(0x40, add(mload(0x40), 0x0721)), mload(0x40)), sha3(add(mload(0x40), 0x20), mload(mload(0x40)))), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        mstore(0xc0, and(and(create2(0, mload(0x40), sub(add(0x40, add(mload(0x40), 0x0721)), mload(0x40)), sha3(add(mload(0x40), 0x20), mload(mload(0x40)))), 0xffffffffffffffffffffffffffffffffffffffff), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        return(mload(0x40), 0x20)
                                                        mstore(0x80, 0x40892c3300000000000000000000000000000000000000000000000000000000)
                                                    }
                                                }
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