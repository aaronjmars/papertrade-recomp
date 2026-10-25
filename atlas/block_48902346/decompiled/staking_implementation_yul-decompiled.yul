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
            * @custom:signature    Unresolved_83115825(address arg0, uint256 arg1, bool arg2, uint64 arg3, bool arg4, uint256 arg5, uint256 arg6) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg3 ["uint64", "bytes8", "int64"]
            * @param                arg4 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg5 ["uint256", "bytes32", "int256"]
            * @param                arg6 ["uint256", "bytes32", "int256"]
            */
            case 0x83115825 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xe0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x84), and(calldataload(0x84), 0xff)) { revert(0, 0); } else {
                                    if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x10))) { revert(mload(0x40), 0x04); } else {
                                        mstore(0x80, 0xda96f0b600000000000000000000000000000000000000000000000000000000)
                                        if sub(sload(0x0d), 0x01) {
                                            sstore(0x0d, 0x02)
                                            codecopy(0, 0x1711, 0x20)
                                            mstore(0, mload(0))
                                            mstore(0xa0, mload(0))
                                            mstore(0xc0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                            mstore(0xe0, calldataload(0x24))
                                            mstore(0x0100, calldataload(0x44))
                                            mstore(0x0120, and(calldataload(0x64), 0xffffffffffffffff))
                                            mstore(0x80, 0xa0)
                                            if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                mstore(0x40, add(mload(0x40), 0xc0))
                                                if gt(timestamp(), and(0xffffffffffffffff, calldataload(0x64))) {
                                                    mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                    mstore(0x20, 0x0e)
                                                    mstore(0, shr(0x08, calldataload(0x44)))
                                                    mstore(0x20, sha3(0, 0x40))
                                                    if and(sload(sha3(0, 0x40)), shl(and(calldataload(0x44), 0xff), 0x01)) { revert(mload(0x40), 0x04); } else {
                                                        mstore(0x0140, 0x756688fe00000000000000000000000000000000000000000000000000000000)
                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        mstore(0x20, 0x0e)
                                                        mstore(0, shr(0x08, calldataload(0x44)))
                                                        mstore(0x20, sha3(0, 0x40))
                                                        sstore(sha3(0, 0x40), or(sload(sha3(0, 0x40)), shl(and(calldataload(0x44), 0xff), 0x01)))
                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        mstore(0x20, 0x0c)
                                                        if iszero(lt(calldataload(0x44), sload(sha3(0, 0x40)))) {
                                                            mstore(0x0140, sload(sha3(0, 0x40)))
                                                            log3(mload(0x40), 0x20, 0x3fde1edb52bbe023081a01c60e06e15396e067be4699a5044fdfa793f67bfc28, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), calldataload(0x44))
                                                            mstore(0x0160, 0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f)
                                                            mstore(0x0180, 0xa590bdeba6833d2f012b59246147e3ca39761a6d26f69a0b227977965a50f955)
                                                            mstore(0x01a0, 0xc89efdaa54c0f20c7adf612882df0950f5a951637e0307cdcb4c672f298b8bc6)
                                                            mstore(0x01c0, chainid())
                                                            mstore(0x01e0, and(0xffffffffffffffffffffffffffffffffffffffff, address()))
                                                            mstore(0x0140, 0xa0)
                                                            if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                mstore(0x40, add(mload(0x40), 0xc0))
                                                                mstore(0x0220, 0x1901000000000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x0222, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                mstore(0x0242, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                mstore(0x0200, 0x42)
                                                                if or(gt(add(mload(0x40), 0x80), 0xffffffffffffffff), lt(add(mload(0x40), 0x80), mload(0x40))) {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x41)
                                                                    mstore(0x40, add(mload(0x40), 0x80))
                                                                    if iszero(eq(and(0xff, calldataload(0x84)), 0x1b)) {
                                                                        if iszero(eq(and(0xff, calldataload(0x84)), 0x1b)) {
                                                                            if gt(calldataload(0xc4), 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0) {
                                                                                if iszero(iszero(0)) {
                                                                                    if iszero(eq(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(mload(0x40), 0x04); } else {
                                                                                        mstore(0x0280, 0x8baa579f00000000000000000000000000000000000000000000000000000000)
                                                                                        if iszero(calldataload(0x24)) {
                                                                                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                            mstore(0x20, 0x09)
                                                                                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                            mstore(0x20, 0x09)
                                                                                            if iszero(or(eq(div(mul(sload(sha3(0, 0x40)), sload(0x06)), sload(sha3(0, 0x40))), sload(0x06)), iszero(sload(sha3(0, 0x40))))) {
                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                mstore(0x04, 0x11)
                                                                                                mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                mstore(0x20, 0x0a)
                                                                                                if gt(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40))) {
                                                                                                    if gt(sub(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40))), div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000)) {
                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                        mstore(0x04, 0x11)
                                                                                                        mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                        mstore(0x20, 0x0b)
                                                                                                        if gt(sload(sha3(0, 0x40)), add(sload(sha3(0, 0x40)), sub(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40))))) {
                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                            mstore(0x04, 0x11)
                                                                                                            sstore(sha3(0, 0x40), add(sload(sha3(0, 0x40)), sub(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40)))))
                                                                                                            mstore(0x0280, 0x23b872dd00000000000000000000000000000000000000000000000000000000)
                                                                                                            mstore(0x0284, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                                            mstore(0x02a4, address())
                                                                                                            mstore(0x02c4, calldataload(0x24))
                                                                                                            call(gas(), and(sload(0x03), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), 0x64, mload(0x40), 0x20)
                                                                                                            if iszero(call(gas(), and(sload(0x03), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), 0x64, mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                                                                returndatacopy(mload(0x40), 0, returndatasize())
                                                                                                                if call(gas(), and(sload(0x03), 0xffffffffffffffffffffffffffffffffffffffff), 0, mload(0x40), 0x64, mload(0x40), 0x20) {
                                                                                                                    if iszero(0) { revert(mload(0x40), 0x04); } else {
                                                                                                                        mstore(0x0280, 0x90b8ec1800000000000000000000000000000000000000000000000000000000)
                                                                                                                        if gt(0x20, returndatasize()) {
                                                                                                                            if or(lt(add(mload(0x40), 0x20), mload(0x40)), gt(add(mload(0x40), 0x20), 0xffffffffffffffff)) {
                                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                mstore(0x04, 0x41)
                                                                                                                                mstore(0x40, add(mload(0x40), 0x20))
                                                                                                                                if slt(sub(add(mload(0x40), 0x20), mload(0x40)), 0x20) { revert(0, 0); } else {
                                                                                                                                    if sub(mload(mload(0x40)), iszero(iszero(mload(mload(0x40))))) {
                                                                                                                                        if iszero(mload(mload(0x40))) { revert(mload(0x40), 0x04); } else {
                                                                                                                                            mstore(0x02a0, 0x90b8ec1800000000000000000000000000000000000000000000000000000000)
                                                                                                                                            mstore(0x0280, 0x1f2a200500000000000000000000000000000000000000000000000000000000)
                                                                                                                                            if iszero(0) { revert(mload(0x40), 0x04); } else {
                                                                                                                                                mstore(0x0280, 0x8baa579f00000000000000000000000000000000000000000000000000000000)
                                                                                                                                                mstore(0x0280, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                                                                                                mstore(0x02a0, and(0xff, calldataload(0x84)))
                                                                                                                                                mstore(0x02c0, calldataload(0xa4))
                                                                                                                                                mstore(0x02e0, calldataload(0xc4))
                                                                                                                                                mstore(0, 0)
                                                                                                                                                staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)
                                                                                                                                                if iszero(staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                                                                                                    returndatacopy(mload(0x40), 0, returndatasize())
                                                                                                                                                    if gt(calldataload(0x44), add(calldataload(0x44), 0x01)) { revert(0, 0); } else {
                                                                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                        mstore(0x04, 0x11)
                                                                                                                                                        mstore(0x0140, 0xf87d927100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                        mstore(0x80, 0xab143c0600000000000000000000000000000000000000000000000000000000)
                                                                                                                                                    }
                                                                                                                                                }
                                                                                                                                            }
                                                                                                                                        }
                                                                                                                                    }
                                                                                                                                }
                                                                                                                            }
                                                                                                                        }
                                                                                                                    }
                                                                                                                }
                                                                                                            }
                                                                                                        }
                                                                                                    }
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_9c96d4a1(address arg0, bool arg1, uint64 arg2, bool arg3, uint256 arg4, uint256 arg5) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg2 ["uint64", "bytes8", "int64"]
            * @param                arg3 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            * @param                arg5 ["uint256", "bytes32", "int256"]
            */
            case 0x9c96d4a1 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xc0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x64), and(calldataload(0x64), 0xff)) { revert(0, 0); } else {
                                    if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x10))) { revert(mload(0x40), 0x04); } else {
                                        mstore(0x80, 0xda96f0b600000000000000000000000000000000000000000000000000000000)
                                        if sub(sload(0x0d), 0x01) {
                                            sstore(0x0d, 0x02)
                                            codecopy(0, 0x16d1, 0x20)
                                            mstore(0, mload(0))
                                            mstore(0xa0, mload(0))
                                            mstore(0xc0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                            mstore(0xe0, calldataload(0x24))
                                            mstore(0x0100, and(calldataload(0x44), 0xffffffffffffffff))
                                            mstore(0x80, 0x80)
                                            if or(gt(add(mload(0x40), 0xa0), 0xffffffffffffffff), lt(add(mload(0x40), 0xa0), mload(0x40))) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                mstore(0x40, add(mload(0x40), 0xa0))
                                                if gt(timestamp(), and(0xffffffffffffffff, calldataload(0x44))) {
                                                    mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                    mstore(0x20, 0x0e)
                                                    mstore(0, shr(0x08, calldataload(0x24)))
                                                    mstore(0x20, sha3(0, 0x40))
                                                    if and(sload(sha3(0, 0x40)), shl(and(calldataload(0x24), 0xff), 0x01)) { revert(mload(0x40), 0x04); } else {
                                                        mstore(0x0120, 0x756688fe00000000000000000000000000000000000000000000000000000000)
                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        mstore(0x20, 0x0e)
                                                        mstore(0, shr(0x08, calldataload(0x24)))
                                                        mstore(0x20, sha3(0, 0x40))
                                                        sstore(sha3(0, 0x40), or(sload(sha3(0, 0x40)), shl(and(calldataload(0x24), 0xff), 0x01)))
                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        mstore(0x20, 0x0c)
                                                        if iszero(lt(calldataload(0x24), sload(sha3(0, 0x40)))) {
                                                            mstore(0x0120, sload(sha3(0, 0x40)))
                                                            log3(mload(0x40), 0x20, 0x3fde1edb52bbe023081a01c60e06e15396e067be4699a5044fdfa793f67bfc28, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), calldataload(0x24))
                                                            mstore(0x0140, 0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f)
                                                            mstore(0x0160, 0xa590bdeba6833d2f012b59246147e3ca39761a6d26f69a0b227977965a50f955)
                                                            mstore(0x0180, 0xc89efdaa54c0f20c7adf612882df0950f5a951637e0307cdcb4c672f298b8bc6)
                                                            mstore(0x01a0, chainid())
                                                            mstore(0x01c0, and(0xffffffffffffffffffffffffffffffffffffffff, address()))
                                                            mstore(0x0120, 0xa0)
                                                            if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                mstore(0x40, add(mload(0x40), 0xc0))
                                                                mstore(0x0200, 0x1901000000000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x0202, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                mstore(0x0222, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                mstore(0x01e0, 0x42)
                                                                if or(gt(add(mload(0x40), 0x80), 0xffffffffffffffff), lt(add(mload(0x40), 0x80), mload(0x40))) {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x41)
                                                                    mstore(0x40, add(mload(0x40), 0x80))
                                                                    if iszero(eq(and(0xff, calldataload(0x64)), 0x1b)) {
                                                                        if iszero(eq(and(0xff, calldataload(0x64)), 0x1b)) {
                                                                            if gt(calldataload(0xa4), 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0) {
                                                                                if iszero(iszero(0)) {
                                                                                    if iszero(eq(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(mload(0x40), 0x04); } else {
                                                                                        mstore(0x0260, 0x8baa579f00000000000000000000000000000000000000000000000000000000)
                                                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                        mstore(0x20, 0x09)
                                                                                        mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                        mstore(0x20, 0x09)
                                                                                        if iszero(or(eq(div(mul(sload(sha3(0, 0x40)), sload(0x06)), sload(sha3(0, 0x40))), sload(0x06)), iszero(sload(sha3(0, 0x40))))) {
                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                            mstore(0x04, 0x11)
                                                                                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                            mstore(0x20, 0x0a)
                                                                                            if gt(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40))) {
                                                                                                if gt(sub(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40))), div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000)) {
                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                    mstore(0x04, 0x11)
                                                                                                    mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                    mstore(0x20, 0x0b)
                                                                                                    if gt(sload(sha3(0, 0x40)), add(sload(sha3(0, 0x40)), sub(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40))))) {
                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                        mstore(0x04, 0x11)
                                                                                                        if iszero(0) { revert(mload(0x40), 0x04); } else {
                                                                                                            mstore(0x0260, 0x8baa579f00000000000000000000000000000000000000000000000000000000)
                                                                                                            mstore(0x0260, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                                                            mstore(0x0280, and(0xff, calldataload(0x64)))
                                                                                                            mstore(0x02a0, calldataload(0x84))
                                                                                                            mstore(0x02c0, calldataload(0xa4))
                                                                                                            mstore(0, 0)
                                                                                                            staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)
                                                                                                            if iszero(staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                                                                returndatacopy(mload(0x40), 0, returndatasize())
                                                                                                                if gt(calldataload(0x24), add(calldataload(0x24), 0x01)) { revert(0, 0); } else {
                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                    mstore(0x04, 0x11)
                                                                                                                    mstore(0x0120, 0xf87d927100000000000000000000000000000000000000000000000000000000)
                                                                                                                    mstore(0x80, 0xab143c0600000000000000000000000000000000000000000000000000000000)
                                                                                                                }
                                                                                                            }
                                                                                                        }
                                                                                                    }
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_f7c618c1() public view returns (address)
            */
            case 0xf7c618c1 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
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
                                    if iszero(and(shr(0xa0, sload(0x10)), 0xff)) {
                                        if and(shr(0xa0, sload(0x10)), 0xff) { revert(mload(0x40), 0x04); } else {
                                            mstore(0x80, 0x3f733c4f00000000000000000000000000000000000000000000000000000000)
                                            if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04))) { revert(0, 0); } else {
                                                sstore(0x0f, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x0f))))
                                                sstore(0x10, or(0x010000000000000000000000000000000000000000, or(and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff), and(sload(0x10), 0xffffffffffffffffffffff000000000000000000000000000000000000000000))))
                                                codecopy(0, 0x1751, 0x20)
                                                mstore(0, mload(0))
                                                log2(0, 0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                codecopy(0, 0x16f1, 0x20)
                                                mstore(0, mload(0))
                                                log2(0, 0, mload(0), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
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
            * @custom:signature    Unresolved_4e71d92d() public pure
            */
            case 0x4e71d92d {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(mload(0x40), 0x04); } else {
                        mstore(0x80, 0xa15ce1ba00000000000000000000000000000000000000000000000000000000)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_9ccae24e(address arg0, address arg1, address arg2, address arg3, address arg4) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["address", "uint160", "bytes20", "int160"]
            * @param                arg3 ["address", "uint160", "bytes20", "int160"]
            * @param                arg4 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x9ccae24e {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xa0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                    if sub(calldataload(0x64), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x64))) { revert(0, 0); } else {
                                        if sub(calldataload(0x84), and(calldataload(0x84), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                            if and(sload(0), 0xff) {
                                                if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                                    if iszero(and(shr(0x08, sload(0)), 0xff)) {
                                                        sstore(0x02, or(and(sload(0x02), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                        sstore(0x03, or(and(sload(0x03), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                        sstore(0x04, or(and(sload(0x04), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff)))
                                                        sstore(0x0d, 0x01)
                                                        if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x64))) {
                                                            sstore(0x0f, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x64)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x0f))))
                                                            sstore(0x10, or(0x010000000000000000000000000000000000000000, or(and(calldataload(0x84), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffff000000000000000000000000000000000000000000, sload(0x10)))))
                                                            mstore(0xa0, 0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f)
                                                            mstore(0xc0, 0xa590bdeba6833d2f012b59246147e3ca39761a6d26f69a0b227977965a50f955)
                                                            mstore(0xe0, 0xc89efdaa54c0f20c7adf612882df0950f5a951637e0307cdcb4c672f298b8bc6)
                                                            mstore(0x0100, chainid())
                                                            mstore(0x0120, and(0xffffffffffffffffffffffffffffffffffffffff, address()))
                                                            mstore(0x80, 0xa0)
                                                            if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                mstore(0x40, add(mload(0x40), 0xc0))
                                                                sstore(0x01, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                codecopy(0, 0x1751, 0x20)
                                                                mstore(0, mload(0))
                                                                log2(0, 0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x64)))
                                                                codecopy(0, 0x16f1, 0x20)
                                                                mstore(0, mload(0))
                                                                log2(0, 0, mload(0), and(calldataload(0x84), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                if iszero(and(shr(0x08, sload(0)), 0xff)) { revert(mload(0x40), 0x04); } else {
                                                                    sstore(0, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00ff, sload(0)))
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
                }
            }
            
            /*
            * @custom:signature    Unresolved_e4fc6b6d() public pure
            */
            case 0xe4fc6b6d {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(mload(0x40), 0x04); } else {
                        mstore(0x80, 0xa15ce1ba00000000000000000000000000000000000000000000000000000000)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_d2f7265a() public view returns (address)
            */
            case 0xd2f7265a {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_6090cf16() public view returns (bool)
            */
            case 0x6090cf16 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, iszero(iszero(and(shr(0xa0, sload(0x10)), 0xff))))
                        return(mload(0x40), 0x20)
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
                            mstore(0x20, 0x0e)
                            mstore(0, calldataload(0x24))
                            mstore(0x20, sha3(0, 0x40))
                            mstore(0x80, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_fa2871b5(address arg0, uint256 arg1, bool arg2, uint64 arg3, bool arg4, uint256 arg5, uint256 arg6) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg3 ["uint64", "bytes8", "int64"]
            * @param                arg4 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg5 ["uint256", "bytes32", "int256"]
            * @param                arg6 ["uint256", "bytes32", "int256"]
            */
            case 0xfa2871b5 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xe0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x64), and(calldataload(0x64), 0xffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x84), and(calldataload(0x84), 0xff)) { revert(0, 0); } else {
                                    if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x10))) { revert(mload(0x40), 0x04); } else {
                                        mstore(0x80, 0xda96f0b600000000000000000000000000000000000000000000000000000000)
                                        if sub(sload(0x0d), 0x01) {
                                            sstore(0x0d, 0x02)
                                            codecopy(0, 0x1691, 0x20)
                                            mstore(0, mload(0))
                                            mstore(0xa0, mload(0))
                                            mstore(0xc0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                            mstore(0xe0, calldataload(0x24))
                                            mstore(0x0100, calldataload(0x44))
                                            mstore(0x0120, and(calldataload(0x64), 0xffffffffffffffff))
                                            mstore(0x80, 0xa0)
                                            if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                mstore(0x40, add(mload(0x40), 0xc0))
                                                if gt(timestamp(), and(0xffffffffffffffff, calldataload(0x64))) {
                                                    mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                    mstore(0x20, 0x0e)
                                                    mstore(0, shr(0x08, calldataload(0x44)))
                                                    mstore(0x20, sha3(0, 0x40))
                                                    if and(sload(sha3(0, 0x40)), shl(and(calldataload(0x44), 0xff), 0x01)) { revert(mload(0x40), 0x04); } else {
                                                        mstore(0x0140, 0x756688fe00000000000000000000000000000000000000000000000000000000)
                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        mstore(0x20, 0x0e)
                                                        mstore(0, shr(0x08, calldataload(0x44)))
                                                        mstore(0x20, sha3(0, 0x40))
                                                        sstore(sha3(0, 0x40), or(sload(sha3(0, 0x40)), shl(and(calldataload(0x44), 0xff), 0x01)))
                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        mstore(0x20, 0x0c)
                                                        if iszero(lt(calldataload(0x44), sload(sha3(0, 0x40)))) {
                                                            mstore(0x0140, sload(sha3(0, 0x40)))
                                                            log3(mload(0x40), 0x20, 0x3fde1edb52bbe023081a01c60e06e15396e067be4699a5044fdfa793f67bfc28, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), calldataload(0x44))
                                                            mstore(0x0160, 0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f)
                                                            mstore(0x0180, 0xa590bdeba6833d2f012b59246147e3ca39761a6d26f69a0b227977965a50f955)
                                                            mstore(0x01a0, 0xc89efdaa54c0f20c7adf612882df0950f5a951637e0307cdcb4c672f298b8bc6)
                                                            mstore(0x01c0, chainid())
                                                            mstore(0x01e0, and(0xffffffffffffffffffffffffffffffffffffffff, address()))
                                                            mstore(0x0140, 0xa0)
                                                            if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                mstore(0x40, add(mload(0x40), 0xc0))
                                                                mstore(0x0220, 0x1901000000000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x0222, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                mstore(0x0242, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                mstore(0x0200, 0x42)
                                                                if or(gt(add(mload(0x40), 0x80), 0xffffffffffffffff), lt(add(mload(0x40), 0x80), mload(0x40))) {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x41)
                                                                    mstore(0x40, add(mload(0x40), 0x80))
                                                                    if iszero(eq(and(0xff, calldataload(0x84)), 0x1b)) {
                                                                        if iszero(eq(and(0xff, calldataload(0x84)), 0x1b)) {
                                                                            if gt(calldataload(0xc4), 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0) {
                                                                                if iszero(iszero(0)) {
                                                                                    if iszero(eq(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(mload(0x40), 0x04); } else {
                                                                                        mstore(0x0280, 0x8baa579f00000000000000000000000000000000000000000000000000000000)
                                                                                        if iszero(calldataload(0x24)) {
                                                                                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                            mstore(0x20, 0x09)
                                                                                            if lt(sload(sha3(0, 0x40)), calldataload(0x24)) { revert(mload(0x40), 0x04); } else {
                                                                                                mstore(0x0280, 0xf1bc94d200000000000000000000000000000000000000000000000000000000)
                                                                                                mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                mstore(0x20, 0x09)
                                                                                                if iszero(or(eq(div(mul(sload(sha3(0, 0x40)), sload(0x06)), sload(sha3(0, 0x40))), sload(0x06)), iszero(sload(sha3(0, 0x40))))) {
                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                    mstore(0x04, 0x11)
                                                                                                    mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                    mstore(0x20, 0x0a)
                                                                                                    if gt(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40))) {
                                                                                                        if gt(sub(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40))), div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000)) {
                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                            mstore(0x04, 0x11)
                                                                                                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                                                                            mstore(0x20, 0x0b)
                                                                                                            if gt(sload(sha3(0, 0x40)), add(sload(sha3(0, 0x40)), sub(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40))))) { revert(mload(0x40), 0x04); } else {
                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                mstore(0x04, 0x11)
                                                                                                                mstore(0x0280, 0x1f2a200500000000000000000000000000000000000000000000000000000000)
                                                                                                                if iszero(0) { revert(mload(0x40), 0x04); } else {
                                                                                                                    mstore(0x0280, 0x8baa579f00000000000000000000000000000000000000000000000000000000)
                                                                                                                    mstore(0x0280, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                                                                    mstore(0x02a0, and(0xff, calldataload(0x84)))
                                                                                                                    mstore(0x02c0, calldataload(0xa4))
                                                                                                                    mstore(0x02e0, calldataload(0xc4))
                                                                                                                    mstore(0, 0)
                                                                                                                    staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)
                                                                                                                    if iszero(staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                                                                        returndatacopy(mload(0x40), 0, returndatasize())
                                                                                                                        if gt(calldataload(0x44), add(calldataload(0x44), 0x01)) { revert(0, 0); } else {
                                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0x04, 0x11)
                                                                                                                            mstore(0x0140, 0xf87d927100000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0x80, 0xab143c0600000000000000000000000000000000000000000000000000000000)
                                                                                                                        }
                                                                                                                    }
                                                                                                                }
                                                                                                            }
                                                                                                        }
                                                                                                    }
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_51ed6a30() public view returns (address)
            */
            case 0x51ed6a30 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x03), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_cab64bcd() public view returns (uint256)
            */
            case 0xcab64bcd {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x07))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_31d7a262(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x31d7a262 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x0b)
                            mstore(0x80, sload(sha3(0, 0x40)))
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
                        mstore(0x80, and(sload(0x10), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_5638b3e5() public pure returns (uint256)
            */
            case 0x5638b3e5 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        codecopy(0, 0x1731, 0x20)
                        mstore(0, mload(0))
                        mstore(0x80, mload(0))
                        return(mload(0x40), 0x20)
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
                            mstore(0x20, 0x0c)
                            mstore(0x80, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_89ee09f0() public pure returns (uint256)
            */
            case 0x89ee09f0 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        codecopy(0, 0x1711, 0x20)
                        mstore(0, mload(0))
                        mstore(0x80, mload(0))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_939d6237() public view returns (uint256)
            */
            case 0x939d6237 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x06))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_f40f0f52(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xf40f0f52 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x09)
                            if iszero(or(eq(div(mul(sload(sha3(0, 0x40)), sload(0x06)), sload(sha3(0, 0x40))), sload(0x06)), iszero(sload(sha3(0, 0x40))))) {
                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                mstore(0x04, 0x11)
                                mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                mstore(0x20, 0x0a)
                                mstore(0x20, 0x0b)
                                if gt(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40))) {
                                    if gt(sub(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40))), div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000)) {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x11)
                                        if gt(sload(sha3(0, 0x40)), add(sload(sha3(0, 0x40)), sub(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40))))) { revert(0, 0); } else {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x11)
                                            mstore(0x80, add(sload(sha3(0, 0x40)), sub(div(mul(sload(sha3(0, 0x40)), sload(0x06)), 0x033b2e3c9fd0803ce8000000), sload(sha3(0, 0x40)))))
                                            return(mload(0x40), 0x20)
                                            mstore(0x80, sload(sha3(0, 0x40)))
                                            return(mload(0x40), 0x20)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_d188c049(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xd188c049 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x0f))) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x10, or(and(sload(0x10), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)))
                                codecopy(0, 0x16f1, 0x20)
                                mstore(0, mload(0))
                                log2(0, 0, mload(0), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
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
                            if sub(caller(), and(sload(0x0f), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x0f, or(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x0f))))
                                codecopy(0, 0x1751, 0x20)
                                mstore(0, mload(0))
                                log2(0, 0, mload(0), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_5873eb9b(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x5873eb9b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x0a)
                            mstore(0x80, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_60217267(address arg0) public view returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x60217267 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x09)
                            mstore(0x80, sload(sha3(0, 0x40)))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_6b0509b1() public pure returns (uint256)
            */
            case 0x6b0509b1 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        codecopy(0, 0x16d1, 0x20)
                        mstore(0, mload(0))
                        mstore(0x80, mload(0))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_f0355460(address arg0, bool arg1, uint64 arg2, bool arg3, uint256 arg4, uint256 arg5) public payable returns (uint256)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg2 ["uint64", "bytes8", "int64"]
            * @param                arg3 ["bool", "uint8", "bytes1", "int8"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            * @param                arg5 ["uint256", "bytes32", "int256"]
            */
            case 0xf0355460 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0xc0) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x64), and(calldataload(0x64), 0xff)) { revert(0, 0); } else {
                                    if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x10))) { revert(mload(0x40), 0x04); } else {
                                        mstore(0x80, 0xda96f0b600000000000000000000000000000000000000000000000000000000)
                                        if sub(sload(0x0d), 0x01) {
                                            sstore(0x0d, 0x02)
                                            codecopy(0, 0x1731, 0x20)
                                            mstore(0, mload(0))
                                            mstore(0xa0, mload(0))
                                            mstore(0xc0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                            mstore(0xe0, calldataload(0x24))
                                            mstore(0x0100, and(calldataload(0x44), 0xffffffffffffffff))
                                            mstore(0x80, 0x80)
                                            if or(gt(add(mload(0x40), 0xa0), 0xffffffffffffffff), lt(add(mload(0x40), 0xa0), mload(0x40))) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                mstore(0x40, add(mload(0x40), 0xa0))
                                                if gt(timestamp(), and(0xffffffffffffffff, calldataload(0x44))) {
                                                    mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                    mstore(0x20, 0x0e)
                                                    mstore(0, shr(0x08, calldataload(0x24)))
                                                    mstore(0x20, sha3(0, 0x40))
                                                    if and(sload(sha3(0, 0x40)), shl(and(calldataload(0x24), 0xff), 0x01)) { revert(mload(0x40), 0x04); } else {
                                                        mstore(0x0120, 0x756688fe00000000000000000000000000000000000000000000000000000000)
                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        mstore(0x20, 0x0e)
                                                        mstore(0, shr(0x08, calldataload(0x24)))
                                                        mstore(0x20, sha3(0, 0x40))
                                                        sstore(sha3(0, 0x40), or(sload(sha3(0, 0x40)), shl(and(calldataload(0x24), 0xff), 0x01)))
                                                        mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                        mstore(0x20, 0x0c)
                                                        if iszero(lt(calldataload(0x24), sload(sha3(0, 0x40)))) {
                                                            mstore(0x0120, sload(sha3(0, 0x40)))
                                                            log3(mload(0x40), 0x20, 0x3fde1edb52bbe023081a01c60e06e15396e067be4699a5044fdfa793f67bfc28, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), calldataload(0x24))
                                                            mstore(0x0140, 0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f)
                                                            mstore(0x0160, 0xa590bdeba6833d2f012b59246147e3ca39761a6d26f69a0b227977965a50f955)
                                                            mstore(0x0180, 0xc89efdaa54c0f20c7adf612882df0950f5a951637e0307cdcb4c672f298b8bc6)
                                                            mstore(0x01a0, chainid())
                                                            mstore(0x01c0, and(0xffffffffffffffffffffffffffffffffffffffff, address()))
                                                            mstore(0x0120, 0xa0)
                                                            if or(gt(add(mload(0x40), 0xc0), 0xffffffffffffffff), lt(add(mload(0x40), 0xc0), mload(0x40))) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                mstore(0x40, add(mload(0x40), 0xc0))
                                                                mstore(0x0200, 0x1901000000000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x0202, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                mstore(0x0222, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                mstore(0x01e0, 0x42)
                                                                if or(gt(add(mload(0x40), 0x80), 0xffffffffffffffff), lt(add(mload(0x40), 0x80), mload(0x40))) {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x41)
                                                                    mstore(0x40, add(mload(0x40), 0x80))
                                                                    if iszero(eq(and(0xff, calldataload(0x64)), 0x1b)) {
                                                                        if iszero(eq(and(0xff, calldataload(0x64)), 0x1b)) {
                                                                            if gt(calldataload(0xa4), 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0) {
                                                                                if iszero(iszero(0)) {
                                                                                    if iszero(eq(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))) { revert(mload(0x40), 0x04); } else {
                                                                                        mstore(0x0260, 0x8baa579f00000000000000000000000000000000000000000000000000000000)
                                                                                        if iszero(extcodesize(and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)))) { revert(0, 0); } else {
                                                                                            mstore(0x0260, 0x7b9f526400000000000000000000000000000000000000000000000000000000)
                                                                                            call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), 0, mload(0x40), 0x04, mload(0x40), 0)
                                                                                            if iszero(call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), 0, mload(0x40), 0x04, mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                                                                returndatacopy(mload(0x40), 0, returndatasize())
                                                                                                if call(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), 0, mload(0x40), 0x04, mload(0x40), 0) {
                                                                                                    mstore(0x0260, 0x27e235e300000000000000000000000000000000000000000000000000000000)
                                                                                                    mstore(0x0264, address())
                                                                                                    staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), mload(0x40), 0x24, mload(0x40), 0x20)
                                                                                                    if iszero(staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), mload(0x40), 0x24, mload(0x40), 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                                                        returndatacopy(mload(0x40), 0, returndatasize())
                                                                                                        if staticcall(gas(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x02)), mload(0x40), 0x24, mload(0x40), 0x20) {
                                                                                                            if iszero(gt(0, sload(0x07))) {
                                                                                                                if gt(sub(0, sload(0x07)), 0) {
                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                    mstore(0x04, 0x11)
                                                                                                                    if iszero(sload(0x05)) {
                                                                                                                        if gt(sub(0, sload(0x07)), add(sub(0, sload(0x07)), sload(0x08))) {
                                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                            mstore(0x04, 0x11)
                                                                                                                            if iszero(iszero(add(sub(0, sload(0x07)), sload(0x08)))) {
                                                                                                                                if sub(0, sload(0x07)) {
                                                                                                                                    if gt(sload(0x07), add(sload(0x07), sub(0, sload(0x07)))) {
                                                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                        mstore(0x04, 0x11)
                                                                                                                                        sstore(0x07, add(sload(0x07), sub(0, sload(0x07))))
                                                                                                                                        sstore(0x08, 0)
                                                                                                                                        if iszero(or(eq(div(mul(add(sub(0, sload(0x07)), sload(0x08)), 0x033b2e3c9fd0803ce8000000), add(sub(0, sload(0x07)), sload(0x08))), 0x033b2e3c9fd0803ce8000000), iszero(add(sub(0, sload(0x07)), sload(0x08))))) {
                                                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                            mstore(0x04, 0x11)
                                                                                                                                            mstore(0x0260, 0)
                                                                                                                                            mstore(0x0280, sub(0, sload(0x07)))
                                                                                                                                            mstore(0x02a0, add(sub(0, sload(0x07)), sload(0x08)))
                                                                                                                                            mstore(0x02c0, sload(0x06))
                                                                                                                                            codecopy(0, 0x16b1, 0x20)
                                                                                                                                            mstore(0, mload(0))
                                                                                                                                            log1(mload(0x40), 0x80, mload(0))
                                                                                                                                            sstore(0x0d, 0x01)
                                                                                                                                            mstore(0x0260, add(sub(0, sload(0x07)), sload(0x08)))
                                                                                                                                            return(mload(0x40), 0x20)
                                                                                                                                            codecopy(0, 0x16b1, 0x20)
                                                                                                                                            mstore(0, mload(0))
                                                                                                                                            if sub(0, sload(0x07)) {
                                                                                                                                            }
                                                                                                                                        }
                                                                                                                                        if gt(0x20, returndatasize()) {
                                                                                                                                            if or(lt(add(mload(0x40), 0x20), mload(0x40)), gt(add(mload(0x40), 0x20), 0xffffffffffffffff)) {
                                                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                mstore(0x04, 0x41)
                                                                                                                                                mstore(0x40, add(mload(0x40), 0x20))
                                                                                                                                                if slt(sub(add(mload(0x40), 0x20), mload(0x40)), 0x20) { revert(0, 0); } else {
                                                                                                                                                    if iszero(gt(mload(mload(0x40)), sload(0x07))) {
                                                                                                                                                    }
                                                                                                                                                    if gt(mload(0x40), 0xffffffffffffffff) {
                                                                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                        mstore(0x04, 0x41)
                                                                                                                                                        if iszero(0) { revert(mload(0x40), 0x04); } else {
                                                                                                                                                            mstore(0x0260, 0x8baa579f00000000000000000000000000000000000000000000000000000000)
                                                                                                                                                            mstore(0x0260, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                                                                                                            mstore(0x0280, and(0xff, calldataload(0x64)))
                                                                                                                                                            mstore(0x02a0, calldataload(0x84))
                                                                                                                                                            mstore(0x02c0, calldataload(0xa4))
                                                                                                                                                            mstore(0, 0)
                                                                                                                                                            staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)
                                                                                                                                                            if iszero(staticcall(gas(), 0x01, mload(0x40), 0x80, 0, 0x20)) { revert(mload(0x40), returndatasize()); } else {
                                                                                                                                                                returndatacopy(mload(0x40), 0, returndatasize())
                                                                                                                                                                if gt(calldataload(0x24), add(calldataload(0x24), 0x01)) { revert(0, 0); } else {
                                                                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                    mstore(0x04, 0x11)
                                                                                                                                                                    mstore(0x0120, 0xf87d927100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                    mstore(0x80, 0xab143c0600000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                }
                                                                                                                                                            }
                                                                                                                                                        }
                                                                                                                                                    }
                                                                                                                                                }
                                                                                                                                            }
                                                                                                                                        }
                                                                                                                                    }
                                                                                                                                }
                                                                                                                            }
                                                                                                                        }
                                                                                                                    }
                                                                                                                }
                                                                                                            }
                                                                                                        }
                                                                                                    }
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_cab7e8eb(address arg0, bool arg1) public view returns (bool)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["bool", "uint8", "bytes1", "int8"]
            */
            case 0xcab7e8eb {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                            mstore(0x20, 0x0e)
                            mstore(0, shr(0x08, calldataload(0x24)))
                            mstore(0x20, sha3(0, 0x40))
                            mstore(0x80, iszero(iszero(and(sload(sha3(0, 0x40)), shl(and(calldataload(0x24), 0xff), 0x01)))))
                            return(mload(0x40), 0x20)
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
                        mstore(0x80, and(sload(0x0f), 0xffffffffffffffffffffffffffffffffffffffff))
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
                        mstore(0xc0, 0xa590bdeba6833d2f012b59246147e3ca39761a6d26f69a0b227977965a50f955)
                        mstore(0xe0, 0xc89efdaa54c0f20c7adf612882df0950f5a951637e0307cdcb4c672f298b8bc6)
                        mstore(0x0100, chainid())
                        mstore(0x0120, and(0xffffffffffffffffffffffffffffffffffffffff, address()))
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
            * @custom:signature    Unresolved_c0c53b8b(address arg0, address arg1, address arg2) public pure
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["address", "uint160", "bytes20", "int160"]
            * @param                arg2 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xc0c53b8b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                    mstore(0x80, 0xb7b2509c00000000000000000000000000000000000000000000000000000000)
                                }
                            }
                        }
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_0700cc42() public pure returns (uint256)
            */
            case 0x0700cc42 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        codecopy(0, 0x1691, 0x20)
                        mstore(0, mload(0))
                        mstore(0x80, mload(0))
                        return(0x80, 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_2b6fdc7e() public view returns (uint256)
            */
            case 0x2b6fdc7e {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x08))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_817b1cd2() public view returns (uint256)
            */
            case 0x817b1cd2 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, sload(0x05))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_2e17de78() public pure
            */
            case 0x2e17de78 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) { revert(0, 0); } else {
                        mstore(0x80, 0xa15ce1ba00000000000000000000000000000000000000000000000000000000)
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
            * @custom:signature    Unresolved_a694fc3a() public pure
            */
            case 0xa694fc3a {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) { revert(0, 0); } else {
                        mstore(0x80, 0xa15ce1ba00000000000000000000000000000000000000000000000000000000)
                    }
                }
            }
            default { revert(0, 0) }
        }
    }
}