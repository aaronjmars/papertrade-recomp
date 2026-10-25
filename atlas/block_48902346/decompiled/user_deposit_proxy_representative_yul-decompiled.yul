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
            * @custom:signature    Unresolved_0c506e96(address arg0, uint256 arg1) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            */
            case 0x0c506e96 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), 0xfb94d3404c1d3d9d6f08f79e58041d5ea95accfa) {
                                if iszero(calldataload(0x24)) {
                                    mstore(0xa0, 0xa9059cbb00000000000000000000000000000000000000000000000000000000)
                                    mstore(0xa4, 0xfb94d3404c1d3d9d6f08f79e58041d5ea95accfa)
                                    mstore(0xc4, calldataload(0x24))
                                    mstore(0x80, 0x44)
                                    if or(gt(add(mload(0x40), 0x80), 0xffffffffffffffff), lt(add(mload(0x40), 0x80), mload(0x40))) {
                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                        mstore(0x04, 0x41)
                                        mstore(0x40, add(mload(0x40), 0x80))
                                        call(gas(), calldataload(0x04), 0, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)
                                        if iszero(returndatasize()) {
                                            if call(gas(), calldataload(0x04), 0, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                                if iszero(call(gas(), calldataload(0x04), 0, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0)) { revert(mload(0x40), 0x64); } else {
                                                    mstore(0x0100, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x0104, 0x20)
                                                    mstore(0x0124, 0x0f)
                                                    mstore(0x0144, 0x7472616e73666572206661696c65640000000000000000000000000000000000)
                                                    mstore(0x0100, calldataload(0x24))
                                                    log3(mload(0x40), 0x20, 0x3d95e1dd133840fdfe95e9a3b6c9fc44f85019531359313e278c6e358ef5b1e0, 0xfb94d3404c1d3d9d6f08f79e58041d5ea95accfa, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                    if iszero(iszero(mload(0x60))) {
                                                        if slt(sub(add(0x60, mload(0x60)), 0x60), 0x20) {
                                                            if sub(mload(0x80), iszero(iszero(mload(0x80)))) { revert(0, 0); } else {
                                                                if gt(returndatasize(), 0xffffffffffffffff) {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x41)
                                                                    if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))), 0xffffffffffffffff)) {
                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                        mstore(0x04, 0x41)
                                                                        mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(returndatasize(), 0x1f))), 0x1f))))
                                                                        mstore(0x0100, returndatasize())
                                                                        returndatacopy(add(mload(0x40), 0x20), 0, returndatasize())
                                                                        if call(gas(), calldataload(0x04), 0, add(mload(0x40), 0x20), mload(mload(0x40)), 0, 0) {
                                                                            if iszero(iszero(mload(mload(0x40)))) {
                                                                                if iszero(iszero(mload(mload(0x40)))) { revert(0, 0); } else {
                                                                                    mstore(0x0140, calldataload(0x24))
                                                                                    log3(mload(0x40), 0x20, 0x3d95e1dd133840fdfe95e9a3b6c9fc44f85019531359313e278c6e358ef5b1e0, 0xfb94d3404c1d3d9d6f08f79e58041d5ea95accfa, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                                    mstore(0x0140, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                                    mstore(0x0144, 0x20)
                                                                                    mstore(0x0164, 0x0f)
                                                                                    mstore(0x0184, 0x7472616e73666572206661696c65640000000000000000000000000000000000)
                                                                                    mstore(0x80, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                                    mstore(0x84, 0x20)
                                                                                    mstore(0xa4, 0x0b)
                                                                                    mstore(0xc4, 0x7a65726f20616d6f756e74000000000000000000000000000000000000000000)
                                                                                    mstore(0x80, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                                    mstore(0x84, 0x20)
                                                                                    mstore(0xa4, 0x09)
                                                                                    mstore(0xc4, 0x6f6e6c7920757365720000000000000000000000000000000000000000000000)
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_4f8632ba() public pure returns (uint256)
            */
            case 0x4f8632ba {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, 0xfb94d3404c1d3d9d6f08f79e58041d5ea95accfa)
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_925b3aad(uint64 arg0, uint64 arg1, uint64 arg2) public payable returns (uint256)
            * @param                arg0 ["uint64", "bytes8", "int64"]
            * @param                arg1 ["uint64", "bytes8", "int64"]
            * @param                arg2 ["uint64", "bytes8", "int64"]
            */
            case 0x925b3aad {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x60) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffff)) { revert(0, 0); } else {
                                if sub(calldataload(0x44), and(calldataload(0x44), 0xffffffffffffffff)) { revert(0, 0); } else {
                                    if sub(caller(), 0x6cd5661646289fb6e65ea5c032310fded797d0a2) {
                                        if iszero(or(iszero(and(calldataload(0x44), 0xffffffffffffffff)), eq(0x64, div(mul(and(calldataload(0x44), 0xffffffffffffffff), 0x64), and(calldataload(0x44), 0xffffffffffffffff))))) {
                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                            mstore(0x04, 0x11)
                                            if gt(and(calldataload(0x24), 0xffffffffffffffff), add(and(calldataload(0x24), 0xffffffffffffffff), mul(and(calldataload(0x44), 0xffffffffffffffff), 0x64))) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x11)
                                                if gt(add(and(calldataload(0x24), 0xffffffffffffffff), mul(and(calldataload(0x44), 0xffffffffffffffff), 0x64)), 0xffffffffffffffff) { revert(mload(0x40), 0x04); } else {
                                                    mstore(0x80, 0xfadaa87100000000000000000000000000000000000000000000000000000000)
                                                    if iszero(iszero(and(calldataload(0x44), 0xffffffffffffffff))) {
                                                        mstore(0xa0, and(calldataload(0x44), 0xffffffffffffffff))
                                                        mstore(0xc0, 0)
                                                        mstore(0x80, 0x40)
                                                        if or(gt(add(mload(0x40), 0x60), 0xffffffffffffffff), lt(add(mload(0x40), 0x60), mload(0x40))) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            mstore(0x40, add(mload(0x40), 0x60))
                                                            mstore(0x0100, 0x0100000000000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x0101, 0x070000000000000000000000000000000000000000000000000000000000)
                                                            if lt(0, mload(mload(0x40))) {
                                                                mstore(0x0144, 0)
                                                                mstore(0xe0, add(sub(add(mload(0x40), mload(mload(0x40))), mload(0x40)), 0x04))
                                                                if or(lt(add(add(mload(0x40), 0x60), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(sub(add(mload(0x40), mload(mload(0x40))), mload(0x40)), 0x24), 0x1f))), add(mload(0x40), 0x60)), gt(add(add(mload(0x40), 0x60), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(sub(add(mload(0x40), mload(mload(0x40))), mload(0x40)), 0x24), 0x1f))), 0xffffffffffffffff)) {
                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                    mstore(0x04, 0x41)
                                                                    mstore(0x40, add(add(mload(0x40), 0x60), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(sub(add(mload(0x40), mload(mload(0x40))), mload(0x40)), 0x24), 0x1f))))
                                                                    if iszero(extcodesize(0x3333333333333333333333333333333333333333)) { revert(0, 0); } else {
                                                                        mstore(0x0160, 0x17938e1300000000000000000000000000000000000000000000000000000000)
                                                                        mstore(0x0164, 0x20)
                                                                        mstore(0x0184, mload(add(mload(0x40), 0x60)))
                                                                        if lt(0, mload(add(mload(0x40), 0x60))) {
                                                                            mstore(0x01e8, 0)
                                                                            call(gas(), 0x3333333333333333333333333333333333333333, 0, mload(0x40), sub(add(add(and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, mload(add(mload(0x40), 0x60)))), add(mload(0x40), 0x04)), 0x40), mload(0x40)), mload(0x40), 0)
                                                                            if iszero(call(gas(), 0x3333333333333333333333333333333333333333, 0, mload(0x40), sub(add(add(and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, mload(add(mload(0x40), 0x60)))), add(mload(0x40), 0x04)), 0x40), mload(0x40)), mload(0x40), 0)) { revert(mload(0x40), returndatasize()); } else {
                                                                                returndatacopy(mload(0x40), 0, returndatasize())
                                                                                if iszero(call(gas(), 0x3333333333333333333333333333333333333333, 0, mload(0x40), sub(add(add(and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, mload(add(mload(0x40), 0x60)))), add(mload(0x40), 0x04)), 0x40), mload(0x40)), mload(0x40), 0)) {
                                                                                    if add(and(calldataload(0x24), 0xffffffffffffffff), mul(and(calldataload(0x44), 0xffffffffffffffff), 0x64)) {
                                                                                        mstore(0x0180, 0x6cd5661646289fb6e65ea5c032310fded797d0a2)
                                                                                        mstore(0x01a0, and(calldataload(0x04), 0xffffffffffffffff))
                                                                                        mstore(0x01c0, and(add(and(calldataload(0x24), 0xffffffffffffffff), mul(and(calldataload(0x44), 0xffffffffffffffff), 0x64)), 0xffffffffffffffff))
                                                                                        mstore(0x0160, 0x60)
                                                                                        if or(gt(add(mload(0x40), 0x80), 0xffffffffffffffff), lt(add(mload(0x40), 0x80), mload(0x40))) {
                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                            mstore(0x04, 0x41)
                                                                                            return(0, 0)
                                                                                            if gt(mload(0x40), 0xffffffffffffffff) { revert(0, 0); } else {
                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                mstore(0x04, 0x41)
                                                                                                mstore(0x80, 0x08c379a000000000000000000000000000000000000000000000000000000000)
                                                                                                mstore(0x84, 0x20)
                                                                                                mstore(0xa4, 0x0d)
                                                                                                mstore(0xc4, 0x6f6e6c792065786368616e676500000000000000000000000000000000000000)
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_d2f7265a() public pure returns (uint256)
            */
            case 0xd2f7265a {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(calldatasize(), 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc), 0) { revert(0, 0); } else {
                        mstore(0x80, 0x6cd5661646289fb6e65ea5c032310fded797d0a2)
                        return(mload(0x40), 0x20)
                    }
                }
            }
            default { revert(0, 0) }
        }
    }
}