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
            * @custom:signature    Unresolved_a066fae9(uint32 arg0) public payable returns (uint64)
            * @param                arg0 ["uint32", "bytes4", "int32"]
            */
            case 0xa066fae9 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            mstore(0xa0, and(calldataload(0x04), 0xffffffff))
                            mstore(0x80, 0x20)
                            if or(gt(add(mload(0x40), 0x40), 0xffffffffffffffff), lt(add(mload(0x40), 0x40), mload(0x40))) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x41)
                                mstore(0x40, add(mload(0x40), 0x40))
                                staticcall(gas(), 0x0806, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)
                                if iszero(returndatasize()) {
                                    if staticcall(gas(), 0x0806, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                        if iszero(staticcall(gas(), 0x0806, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x64); } else {
                                            mstore(0xc0, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                            mstore(0xc4, 0x20)
                                            mstore(0xe4, 0x16)
                                            mstore(0x0104, 0x4d61726b2070726963652072656164206661696c656400000000000000000000)
                                            if slt(sub(add(0x60, mload(0x60)), 0x60), 0x20) {
                                                if sub(mload(0x80), and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                    if iszero(and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                        mstore(0xc0, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                        mstore(0xc4, 0x20)
                                                        mstore(0xe4, 0x12)
                                                        mstore(0x0104, 0x4d61726b207072696365206973207a65726f0000000000000000000000000000)
                                                        mstore(0xc0, and(mload(0x80), 0xffffffffffffffff))
                                                        return(mload(0x40), 0x20)
                                                        if iszero(iszero(lt(mload(0x60), 0x20))) { revert(mload(0x40), 0x64); } else {
                                                            mstore(0xc0, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                            mstore(0xc4, 0x20)
                                                            mstore(0xe4, 0x16)
                                                            mstore(0x0104, 0x4d61726b2070726963652072656164206661696c656400000000000000000000)
                                                            if gt(returndatasize(), 0xffffffffffffffff) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), 0xffffffffffffffff)) {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x41)
                                                                    mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))))
                                                                    mstore(0xc0, returndatasize())
                                                                    returndatacopy(add(mload(0x40), 0x20), 0, returndatasize())
                                                                    if staticcall(gas(), 0x0806, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                                                        if iszero(staticcall(gas(), 0x0806, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(0, 0); } else {
                                                                            mstore(0x0100, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0x0104, 0x20)
                                                                            mstore(0x0124, 0x16)
                                                                            mstore(0x0144, 0x4d61726b2070726963652072656164206661696c656400000000000000000000)
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_c4d66de8(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xc4d66de8 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if and(sload(0), 0xff) {
                                if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                    if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                        sstore(0, or(and(0xffffffffffffffffffffffffffffffffffffffff0000, shl(0x10, calldataload(0x04))), and(0xffffffffffffffffffff0000000000000000000000000000000000000000ffff, sload(0))))
                                        log2(0, 0, 0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                        if iszero(and(shr(0x08, sload(0)), 0xff)) { revert(mload(0x40), 0x04); } else {
                                            sstore(0, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00ff, sload(0)))
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
            
            /*
            * @custom:signature    Unresolved_2af78bd1(uint32 arg0) public payable returns (uint64)
            * @param                arg0 ["uint32", "bytes4", "int32"]
            */
            case 0x2af78bd1 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            mstore(0xa0, and(calldataload(0x04), 0xffffffff))
                            mstore(0x80, 0x20)
                            if or(gt(add(mload(0x40), 0x40), 0xffffffffffffffff), lt(add(mload(0x40), 0x40), mload(0x40))) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x41)
                                mstore(0x40, add(mload(0x40), 0x40))
                                staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)
                                if iszero(returndatasize()) {
                                    if staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                        if iszero(staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x64); } else {
                                            mstore(0xc0, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                            mstore(0xc4, 0x20)
                                            mstore(0xe4, 0x12)
                                            mstore(0x0104, 0x4f7261636c652072656164206661696c65640000000000000000000000000000)
                                            if slt(sub(add(0x60, mload(0x60)), 0x60), 0x20) {
                                                if sub(mload(0x80), and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                    if iszero(and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                        mstore(0xc0, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                        mstore(0xc4, 0x20)
                                                        mstore(0xe4, 0x14)
                                                        mstore(0x0104, 0x4f7261636c65207072696365206973207a65726f000000000000000000000000)
                                                        mstore(0xc0, and(mload(0x80), 0xffffffffffffffff))
                                                        return(mload(0x40), 0x20)
                                                        if iszero(iszero(lt(mload(0x60), 0x20))) { revert(mload(0x40), 0x64); } else {
                                                            mstore(0xc0, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                            mstore(0xc4, 0x20)
                                                            mstore(0xe4, 0x12)
                                                            mstore(0x0104, 0x4f7261636c652072656164206661696c65640000000000000000000000000000)
                                                            if gt(returndatasize(), 0xffffffffffffffff) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), 0xffffffffffffffff)) {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x41)
                                                                    mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))))
                                                                    mstore(0xc0, returndatasize())
                                                                    returndatacopy(add(mload(0x40), 0x20), 0, returndatasize())
                                                                    if staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                                                        if iszero(staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(0, 0); } else {
                                                                            mstore(0x0100, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0x0104, 0x20)
                                                                            mstore(0x0124, 0x12)
                                                                            mstore(0x0144, 0x4f7261636c652072656164206661696c65640000000000000000000000000000)
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_766cd255(uint32 arg0) public payable
            * @param                arg0 ["uint32", "bytes4", "int32"]
            */
            case 0x766cd255 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            if or(lt(add(mload(0x40), 0xa0), mload(0x40)), gt(add(mload(0x40), 0xa0), 0xffffffffffffffff)) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x41)
                                mstore(0x40, add(mload(0x40), 0xa0))
                                mstore(0x80, 0)
                                mstore(0xa0, 0)
                                mstore(0xc0, 0)
                                mstore(0xe0, 0)
                                mstore(0x0100, 0)
                                if or(lt(add(mload(0x40), 0xa0), mload(0x40)), gt(add(mload(0x40), 0xa0), 0xffffffffffffffff)) {
                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                    mstore(0x04, 0x41)
                                    mstore(0x40, add(mload(0x40), 0xa0))
                                    mstore(0x0120, 0)
                                    mstore(0x0140, 0)
                                    mstore(0x0160, 0)
                                    mstore(0x0180, 0)
                                    mstore(0x01a0, 0)
                                    mstore(0x01e0, and(calldataload(0x04), 0xffffffff))
                                    mstore(0x01c0, 0x20)
                                    if or(gt(add(mload(0x40), 0x40), 0xffffffffffffffff), lt(add(mload(0x40), 0x40), mload(0x40))) {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x41)
                                        mstore(0x40, add(mload(0x40), 0x40))
                                        staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)
                                        if iszero(returndatasize()) {
                                            if staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                                if iszero(staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x64); } else {
                                                    mstore(0x0200, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x0204, 0x20)
                                                    mstore(0x0224, 0x12)
                                                    mstore(0x0244, 0x4f7261636c652072656164206661696c65640000000000000000000000000000)
                                                    if slt(sub(add(0x60, mload(0x60)), 0x60), 0x20) {
                                                        if sub(mload(0x80), and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                            if iszero(and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                                mstore(0x0200, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x0204, 0x20)
                                                                mstore(0x0224, 0x14)
                                                                mstore(0x0244, 0x4f7261636c65207072696365206973207a65726f000000000000000000000000)
                                                                if iszero(iszero(lt(mload(0x60), 0x20))) { revert(mload(0x40), 0x64); } else {
                                                                    mstore(0x0200, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x0204, 0x20)
                                                                    mstore(0x0224, 0x12)
                                                                    mstore(0x0244, 0x4f7261636c652072656164206661696c65640000000000000000000000000000)
                                                                    if gt(returndatasize(), 0xffffffffffffffff) {
                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                        mstore(0x04, 0x41)
                                                                        if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), 0xffffffffffffffff)) {
                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0x04, 0x41)
                                                                            mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))))
                                                                            mstore(0x0200, returndatasize())
                                                                            returndatacopy(add(mload(0x40), 0x20), 0, returndatasize())
                                                                            if staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                                                                if iszero(staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(0, 0); } else {
                                                                                    mstore(0x0240, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                                    mstore(0x0244, 0x20)
                                                                                    mstore(0x0264, 0x12)
                                                                                    mstore(0x0284, 0x4f7261636c652072656164206661696c65640000000000000000000000000000)
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_a7f06462(uint256 arg0, uint32 arg1) public payable returns (bytes memory)
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["uint32", "bytes4", "int32"]
            */
            case 0xa7f06462 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x20) {
                        if gt(calldataload(0x04), 0xffffffffffffffff) { revert(0, 0); } else {
                            if iszero(slt(add(calldataload(0x04), 0x23), calldatasize())) {
                                if gt(calldataload(add(calldataload(0x04), 0x04)), 0xffffffffffffffff) { revert(0, 0); } else {
                                    if gt(add(add(calldataload(0x04), shl(0x05, calldataload(add(calldataload(0x04), 0x04)))), 0x24), calldatasize()) {
                                        if gt(calldataload(add(calldataload(0x04), 0x04)), 0xffffffffffffffff) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x41)
                                            if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, shl(0x05, calldataload(add(calldataload(0x04), 0x04)))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, shl(0x05, calldataload(add(calldataload(0x04), 0x04)))), 0x1f))), 0xffffffffffffffff)) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, shl(0x05, calldataload(add(calldataload(0x04), 0x04)))), 0x1f))))
                                                mstore(0x80, calldataload(add(calldataload(0x04), 0x04)))
                                                if gt(calldataload(add(calldataload(0x04), 0x04)), 0xffffffffffffffff) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x41)
                                                    if lt(0, add(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x20, shl(0x05, calldataload(add(calldataload(0x04), 0x04)))))) {
                                                        if or(lt(add(mload(0x40), 0xa0), mload(0x40)), gt(add(mload(0x40), 0xa0), 0xffffffffffffffff)) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            if lt(0, calldataload(add(calldataload(0x04), 0x04))) {
                                                                if sub(calldataload(add(add(calldataload(0x04), 0), 0x24)), and(calldataload(add(add(calldataload(0x04), 0), 0x24)), 0xffffffff)) { revert(0, 0); } else {
                                                                    if or(lt(add(mload(0x40), 0xa0), mload(0x40)), gt(add(mload(0x40), 0xa0), 0xffffffffffffffff)) {
                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                        mstore(0x04, 0x41)
                                                                        mstore(0x40, add(mload(0x40), 0xa0))
                                                                        mstore(0xa0, 0)
                                                                        mstore(0xc0, 0)
                                                                        mstore(0xe0, 0)
                                                                        mstore(0x0100, 0)
                                                                        mstore(0x0120, 0)
                                                                        mstore(0x0160, and(calldataload(add(add(calldataload(0x04), 0), 0x24)), 0xffffffff))
                                                                        mstore(0x0140, 0x20)
                                                                        if or(gt(add(mload(0x40), 0x40), 0xffffffffffffffff), lt(add(mload(0x40), 0x40), mload(0x40))) {
                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                            mstore(0x04, 0x41)
                                                                            mstore(0x40, add(mload(0x40), 0x40))
                                                                            staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)
                                                                            if iszero(returndatasize()) {
                                                                                if staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                                                                    if iszero(staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x64); } else {
                                                                                        mstore(0x0180, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                                        mstore(0x0184, 0x20)
                                                                                        mstore(0x01a4, 0x12)
                                                                                        mstore(0x01c4, 0x4f7261636c652072656164206661696c65640000000000000000000000000000)
                                                                                        if slt(sub(add(0x60, mload(0x60)), 0x60), 0x20) {
                                                                                            if sub(mload(0x80), and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                                                                if iszero(and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                                                                    mstore(0x0180, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                                                    mstore(0x0184, 0x20)
                                                                                                    mstore(0x01a4, 0x14)
                                                                                                    mstore(0x01c4, 0x4f7261636c65207072696365206973207a65726f000000000000000000000000)
                                                                                                    if iszero(iszero(lt(mload(0x60), 0x20))) { revert(mload(0x40), 0x64); } else {
                                                                                                        mstore(0x0180, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                                                        mstore(0x0184, 0x20)
                                                                                                        mstore(0x01a4, 0x12)
                                                                                                        mstore(0x01c4, 0x4f7261636c652072656164206661696c65640000000000000000000000000000)
                                                                                                        if gt(returndatasize(), 0xffffffffffffffff) {
                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                            mstore(0x04, 0x41)
                                                                                                            if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), 0xffffffffffffffff)) {
                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                mstore(0x04, 0x41)
                                                                                                                mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))))
                                                                                                                mstore(0x0180, returndatasize())
                                                                                                                returndatacopy(add(mload(0x40), 0x20), 0, returndatasize())
                                                                                                                if staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                                                                                                    if iszero(staticcall(gas(), 0x0807, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x64); } else {
                                                                                                                        mstore(0x01c0, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                                                                        mstore(0x01c4, 0x20)
                                                                                                                        mstore(0x01e4, 0x12)
                                                                                                                        mstore(0x0204, 0x4f7261636c652072656164206661696c65640000000000000000000000000000)
                                                                                                                        mstore(0xa0, 0x20)
                                                                                                                        mstore(0xc0, mload(mload(0x40)))
                                                                                                                        if lt(0, mload(mload(0x40))) { revert(0, 0); } else {
                                                                                                                            return(mload(0x40), sub(add(0x40, mload(0x40)), mload(0x40)))
                                                                                                                        }
                                                                                                                    }
                                                                                                                }
                                                                                                            }
                                                                                                        }
                                                                                                    }
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_f2fde38b(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xf2fde38b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(shr(0x10, sload(0)), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0, or(and(0xffffffffffffffffffffffffffffffffffffffff0000, shl(0x10, calldataload(0x04))), and(0xffffffffffffffffffff0000000000000000000000000000000000000000ffff, sload(0))))
                                log2(0, 0, 0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_c0182669(uint32 arg0) public payable
            * @param                arg0 ["uint32", "bytes4", "int32"]
            */
            case 0xc0182669 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            mstore(0xa0, and(calldataload(0x04), 0xffffffff))
                            mstore(0x80, 0x20)
                            if or(gt(add(mload(0x40), 0x40), 0xffffffffffffffff), lt(add(mload(0x40), 0x40), mload(0x40))) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x41)
                                mstore(0x40, add(mload(0x40), 0x40))
                                staticcall(gas(), 0x080e, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)
                                if iszero(returndatasize()) {
                                    if staticcall(gas(), 0x080e, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                        if iszero(staticcall(gas(), 0x080e, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x64); } else {
                                            mstore(0xc0, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                            mstore(0xc4, 0x20)
                                            mstore(0xe4, 0x0f)
                                            mstore(0x0104, 0x42424f2072656164206661696c65640000000000000000000000000000000000)
                                            if slt(sub(add(0x60, mload(0x60)), 0x60), 0x40) {
                                                if sub(mload(0x80), and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                    if iszero(iszero(lt(mload(0x60), 0x40))) { revert(mload(0x40), 0x64); } else {
                                                        mstore(0xc0, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                        mstore(0xc4, 0x20)
                                                        mstore(0xe4, 0x0f)
                                                        mstore(0x0104, 0x42424f2072656164206661696c65640000000000000000000000000000000000)
                                                        if gt(returndatasize(), 0xffffffffffffffff) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), 0xffffffffffffffff)) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))))
                                                                mstore(0xc0, returndatasize())
                                                                returndatacopy(add(mload(0x40), 0x20), 0, returndatasize())
                                                                if staticcall(gas(), 0x080e, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                                                    if iszero(staticcall(gas(), 0x080e, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(0, 0); } else {
                                                                        mstore(0x0100, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                        mstore(0x0104, 0x20)
                                                                        mstore(0x0124, 0x0f)
                                                                        mstore(0x0144, 0x42424f2072656164206661696c65640000000000000000000000000000000000)
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_fb466481(uint32 arg0) public payable
            * @param                arg0 ["uint32", "bytes4", "int32"]
            */
            case 0xfb466481 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffff)) { revert(0, 0); } else {
                            mstore(0xa0, and(calldataload(0x04), 0xffffffff))
                            mstore(0x80, 0x20)
                            if or(gt(add(mload(0x40), 0x40), 0xffffffffffffffff), lt(add(mload(0x40), 0x40), mload(0x40))) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x41)
                                mstore(0x40, add(mload(0x40), 0x40))
                                staticcall(gas(), 0x080e, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)
                                if iszero(returndatasize()) {
                                    if staticcall(gas(), 0x080e, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                        if iszero(staticcall(gas(), 0x080e, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x64); } else {
                                            mstore(0xc0, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                            mstore(0xc4, 0x20)
                                            mstore(0xe4, 0x0f)
                                            mstore(0x0104, 0x42424f2072656164206661696c65640000000000000000000000000000000000)
                                            if slt(sub(add(0x60, mload(0x60)), 0x60), 0x40) {
                                                if sub(mload(0x80), and(mload(0x80), 0xffffffffffffffff)) { revert(0, 0); } else {
                                                    if iszero(iszero(lt(mload(0x60), 0x40))) { revert(mload(0x40), 0x64); } else {
                                                        mstore(0xc0, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                        mstore(0xc4, 0x20)
                                                        mstore(0xe4, 0x0f)
                                                        mstore(0x0104, 0x42424f2072656164206661696c65640000000000000000000000000000000000)
                                                        if gt(returndatasize(), 0xffffffffffffffff) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), 0xffffffffffffffff)) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))))
                                                                mstore(0xc0, returndatasize())
                                                                returndatacopy(add(mload(0x40), 0x20), 0, returndatasize())
                                                                if staticcall(gas(), 0x080e, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                                                    if iszero(staticcall(gas(), 0x080e, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(0, 0); } else {
                                                                        mstore(0x0100, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                        mstore(0x0104, 0x20)
                                                                        mstore(0x0124, 0x0f)
                                                                        mstore(0x0144, 0x42424f2072656164206661696c65640000000000000000000000000000000000)
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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