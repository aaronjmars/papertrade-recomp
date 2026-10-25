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
            * @custom:signature    Unresolved_6090cf16() public view returns (bool)
            */
            case 0x6090cf16 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, iszero(iszero(and(sload(0x05), 0xff))))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_0b826190() public view returns (address)
            */
            case 0x0b826190 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x01)))
                        return(0x80, 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_251fb27d(uint256 arg0, uint256 arg1, uint256 arg2, uint256 arg3, uint256 arg4, uint256 arg5) public payable
            * @param                arg0 ["uint256", "bytes32", "int256"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            * @param                arg2 ["uint256", "bytes32", "int256"]
            * @param                arg3 ["uint256", "bytes32", "int256"]
            * @param                arg4 ["uint256", "bytes32", "int256"]
            * @param                arg5 ["uint256", "bytes32", "int256"]
            */
            case 0x251fb27d {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if lt(0xffffffffffffffff, calldataload(0x04)) { revert(0, 0); } else {
                            if iszero(slt(add(calldataload(0x04), 0x23), calldatasize())) {
                                if gt(calldataload(add(0x04, calldataload(0x04))), 0xffffffffffffffff) { revert(0, 0); } else {
                                    if gt(add(add(calldataload(0x04), shl(0x05, calldataload(add(0x04, calldataload(0x04))))), 0x24), calldatasize()) {
                                        mstore(0, caller())
                                        mstore(0x20, 0x04)
                                        if iszero(and(sload(sha3(0, 0x40)), 0xff)) {
                                            if gt(calldatasize(), 0xffffffffffffffff) {
                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                mstore(0x04, 0x41)
                                                if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldatasize()))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldatasize()))), 0x1f))), 0xffffffffffffffff)) {
                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                    mstore(0x04, 0x41)
                                                    mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, calldatasize()))), 0x1f))))
                                                    mstore(0x80, calldatasize())
                                                    calldatacopy(add(mload(0x40), 0x20), 0, calldatasize())
                                                    mstore(0xa4, 0)
                                                    if gt(calldataload(add(0x04, calldataload(0x04))), 0xffffffffffffffff) {
                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                        mstore(0x04, 0x41)
                                                        if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, shl(0x05, calldataload(add(0x04, calldataload(0x04))))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, shl(0x05, calldataload(add(0x04, calldataload(0x04))))), 0x1f))), 0xffffffffffffffff)) {
                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                            mstore(0x04, 0x41)
                                                            mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, shl(0x05, calldataload(add(0x04, calldataload(0x04))))), 0x1f))))
                                                            mstore(0xc0, calldataload(add(calldataload(0x04), 0x04)))
                                                            if gt(calldataload(add(calldataload(0x04), 0x04)), 0xffffffffffffffff) {
                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                mstore(0x04, 0x41)
                                                                calldatacopy(add(mload(0x40), 0x20), calldatasize(), add(add(0x20, shl(0x05, calldataload(add(calldataload(0x04), 0x04)))), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0))
                                                                if lt(0, calldataload(add(0x04, calldataload(0x04)))) {
                                                                    if iszero(slt(calldataload(add(add(calldataload(0x04), 0), 0x24)), add(sub(calldatasize(), calldataload(0x04)), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff3d))) {
                                                                        if iszero(iszero(calldataload(add(0x84, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)))))) {
                                                                            if lt(0, 0) {
                                                                                if iszero(lt(0, mload(mload(0x40)))) {
                                                                                    if eq(mload(add(add(0, mload(0x40)), 0x20)), calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x84))) {
                                                                                        if 0x01 {
                                                                                            if sub(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x24)), and(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x24)), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                                                if iszero(slt(calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44)), add(sub(calldatasize(), add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)))), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe1))) {
                                                                                                    if gt(calldataload(add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44)))), 0xffffffffffffffff) { revert(0, 0); } else {
                                                                                                        if sgt(add(0x20, add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44)))), sub(calldatasize(), calldataload(add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44)))))) {
                                                                                                            if lt(calldataload(add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44)))), 0x04) {
                                                                                                                if gt(0x04, calldataload(add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44))))) {
                                                                                                                    if eq(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x24))), and(0xffffffffffffffffffffffffffffffffffffffff, shr(0x10, sload(0)))) {
                                                                                                                        if eq(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x24))), and(sload(0x01), 0xffffffffffffffffffffffffffffffffffffffff)) {
                                                                                                                            if eq(and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x24)))) {
                                                                                                                                if iszero(0) {
                                                                                                                                    if or(lt(add(mload(0x40), 0x20), mload(0x40)), gt(add(mload(0x40), 0x20), 0xffffffffffffffff)) {
                                                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                        mstore(0x04, 0x41)
                                                                                                                                        mstore(0x40, add(mload(0x40), 0x20))
                                                                                                                                        mstore(0xe0, 0)
                                                                                                                                        if mload(mload(0x40)) {
                                                                                                                                            if sub(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x64)), iszero(iszero(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x64))))) { revert(0, 0); } else {
                                                                                                                                                if iszero(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x64))) {
                                                                                                                                                    if eq(0, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) {
                                                                                                                                                        mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                        mstore(0x04, 0x11)
                                                                                                                                                        if iszero(iszero(calldataload(add(0x84, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)))))) {
                                                                                                                                                            if eq(0, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) {
                                                                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                mstore(0x04, 0x11)
                                                                                                                                                                mstore(0x0100, 0x20)
                                                                                                                                                                mstore(0x0120, mload(mload(0x40)))
                                                                                                                                                                if lt(0, mload(mload(0x40))) {
                                                                                                                                                                }
                                                                                                                                                                if sub(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x24)), and(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x24)), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                                                                                                                                                    if iszero(slt(calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44)), add(sub(calldatasize(), add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)))), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe1))) {
                                                                                                                                                                        if gt(calldataload(add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44)))), 0xffffffffffffffff) { revert(0, 0); } else {
                                                                                                                                                                            if sgt(add(0x20, add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44)))), sub(calldatasize(), calldataload(add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44)))))) {
                                                                                                                                                                                calldatacopy(mload(0x40), add(0x20, add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44)))), calldataload(add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44)))))
                                                                                                                                                                                mstore(0x0100, 0)
                                                                                                                                                                                call(gas(), calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x24)), 0, mload(0x40), sub(add(mload(0x40), calldataload(add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44))))), mload(0x40)), 0, 0)
                                                                                                                                                                                if iszero(returndatasize()) {
                                                                                                                                                                                    if iszero(call(gas(), calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x24)), 0, mload(0x40), sub(add(mload(0x40), calldataload(add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44))))), mload(0x40)), 0, 0)) {
                                                                                                                                                                                        if sub(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x64)), iszero(iszero(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x64))))) { revert(0, 0); } else {
                                                                                                                                                                                            if iszero(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x64))) {
                                                                                                                                                                                                codecopy(0, 0x0d06, 0x20)
                                                                                                                                                                                                mstore(0, mload(0))
                                                                                                                                                                                                if eq(0, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) {
                                                                                                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                    mstore(0x04, 0x11)
                                                                                                                                                                                                    if iszero(iszero(calldataload(add(0x84, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)))))) {
                                                                                                                                                                                                        if eq(0, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) {
                                                                                                                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                            mstore(0x04, 0x11)
                                                                                                                                                                                                            if gt(returndatasize(), 0xffffffffffffffff) {
                                                                                                                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                mstore(0x04, 0x41)
                                                                                                                                                                                                                if or(lt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, returndatasize()))), 0x1f))), mload(0x40)), gt(add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, returndatasize()))), 0x1f))), 0xffffffffffffffff)) {
                                                                                                                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                    mstore(0x04, 0x41)
                                                                                                                                                                                                                    mstore(0x40, add(mload(0x40), and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(add(0x20, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0, add(0x1f, returndatasize()))), 0x1f))))
                                                                                                                                                                                                                    mstore(0x0100, returndatasize())
                                                                                                                                                                                                                    returndatacopy(add(mload(0x40), 0x20), 0, returndatasize())
                                                                                                                                                                                                                    if iszero(call(gas(), calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x24)), 0, mload(0x40), sub(add(mload(0x40), calldataload(add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44))))), mload(0x40)), 0, 0)) {
                                                                                                                                                                                                                        if sub(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x64)), iszero(iszero(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x64))))) { revert(0, 0); } else {
                                                                                                                                                                                                                            if iszero(calldataload(add(add(calldataload(0x04), calldataload(add(add(calldataload(0x04), 0), 0x24))), 0x64))) {
                                                                                                                                                                                                                                codecopy(0, 0x0d06, 0x20)
                                                                                                                                                                                                                                mstore(0, mload(0))
                                                                                                                                                                                                                                if eq(0, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) {
                                                                                                                                                                                                                                    mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                                    mstore(0x04, 0x11)
                                                                                                                                                                                                                                    if iszero(iszero(calldataload(add(0x84, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)))))) {
                                                                                                                                                                                                                                        if eq(0, 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) {
                                                                                                                                                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                                            mstore(0x04, 0x11)
                                                                                                                                                                                                                                            mstore(0x0140, 0)
                                                                                                                                                                                                                                            mstore(0x0160, 0x40)
                                                                                                                                                                                                                                            mstore(0x0180, mload(mload(0x40)))
                                                                                                                                                                                                                                            if lt(0, mload(mload(0x40))) { revert(0, 0); } else {
                                                                                                                                                                                                                                            }
                                                                                                                                                                                                                                            mstore(0x0100, 0x42617463684578656375746f723a2073656c6563746f72206e6f7420616c6c6f)
                                                                                                                                                                                                                                            mstore(0x0120, 0x7765640000000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                                            mstore(0xe0, 0x23)
                                                                                                                                                                                                                                            if or(gt(add(mload(0x40), 0x60), 0xffffffffffffffff), lt(add(mload(0x40), 0x60), mload(0x40))) {
                                                                                                                                                                                                                                                mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                                                mstore(0x04, 0x41)
                                                                                                                                                                                                                                                mstore(0x40, add(mload(0x40), 0x60))
                                                                                                                                                                                                                                                if mload(mload(0x40)) {
                                                                                                                                                                                                                                                }
                                                                                                                                                                                                                                            }
                                                                                                                                                                                                                                            if iszero(eq(and(0xffffffff00000000000000000000000000000000000000000000000000000000, and(0xffffffff00000000000000000000000000000000000000000000000000000000, calldataload(add(0x20, add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44))))))), 0x8311582500000000000000000000000000000000000000000000000000000000)) {
                                                                                                                                                                                                                                                if iszero(eq(and(0xffffffff00000000000000000000000000000000000000000000000000000000, and(0xffffffff00000000000000000000000000000000000000000000000000000000, calldataload(add(0x20, add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44))))))), 0x8311582500000000000000000000000000000000000000000000000000000000)) {
                                                                                                                                                                                                                                                    if iszero(eq(and(0xffffffff00000000000000000000000000000000000000000000000000000000, and(0xffffffff00000000000000000000000000000000000000000000000000000000, calldataload(add(0x20, add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44))))))), 0x8311582500000000000000000000000000000000000000000000000000000000)) {
                                                                                                                                                                                                                                                    }
                                                                                                                                                                                                                                                }
                                                                                                                                                                                                                                            }
                                                                                                                                                                                                                                            if iszero(eq(and(0xffffffff00000000000000000000000000000000000000000000000000000000, and(0xffffffff00000000000000000000000000000000000000000000000000000000, calldataload(add(0x20, add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44))))))), 0xec6783f000000000000000000000000000000000000000000000000000000000)) {
                                                                                                                                                                                                                                                if iszero(eq(and(0xffffffff00000000000000000000000000000000000000000000000000000000, and(0xffffffff00000000000000000000000000000000000000000000000000000000, calldataload(add(0x20, add(add(0x24, add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04))), calldataload(add(add(calldataload(add(add(calldataload(0x04), 0), 0x24)), calldataload(0x04)), 0x44))))))), 0xec6783f000000000000000000000000000000000000000000000000000000000)) { revert(0, 0); } else {
                                                                                                                                                                                                                                                }
                                                                                                                                                                                                                                            }
                                                                                                                                                                                                                                            mstore(0, 0x4e487b7100000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                                            mstore(0x04, 0x32)
                                                                                                                                                                                                                                            if 0 { revert(0, 0); } else {
                                                                                                                                                                                                                                            }
                                                                                                                                                                                                                                            mstore(0xe0, calldataload(add(0x04, calldataload(0x04))))
                                                                                                                                                                                                                                            mstore(0x0100, 0)
                                                                                                                                                                                                                                            mstore(0x0120, 0)
                                                                                                                                                                                                                                            mstore(0x0140, 0)
                                                                                                                                                                                                                                            log2(mload(0x40), 0x80, 0x9d65322d939fd0a2d0032c87248c8e9f9b14cc177e27b2c049cb4b0356e5160b, sha3(add(mload(0x40), 0x20), mload(mload(0x40))))
                                                                                                                                                                                                                                            mstore(0x80, 0x17fb206600000000000000000000000000000000000000000000000000000000)
                                                                                                                                                                                                                                        }
                                                                                                                                                                                                                                    }
                                                                                                                                                                                                                                }
                                                                                                                                                                                                                            }
                                                                                                                                                                                                                        }
                                                                                                                                                                                                                    }
                                                                                                                                                                                                                }
                                                                                                                                                                                                            }
                                                                                                                                                                                                        }
                                                                                                                                                                                                    }
                                                                                                                                                                                                }
                                                                                                                                                                                            }
                                                                                                                                                                                        }
                                                                                                                                                                                    }
                                                                                                                                                                                }
                                                                                                                                                                            }
                                                                                                                                                                        }
                                                                                                                                                                    }
                                                                                                                                                                }
                                                                                                                                                            }
                                                                                                                                                        }
                                                                                                                                                    }
                                                                                                                                                }
                                                                                                                                            }
                                                                                                                                        }
                                                                                                                                    }
                                                                                                                                }
                                                                                                                            }
                                                                                                                        }
                                                                                                                    }
                                                                                                                }
                                                                                                            }
                                                                                                        }
                                                                                                    }
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
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
            * @custom:signature    Unresolved_9011e5f9(address arg0, uint256 arg1) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            * @param                arg1 ["uint256", "bytes32", "int256"]
            */
            case 0x9011e5f9 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), iszero(iszero(calldataload(0x24)))) { revert(0, 0); } else {
                                if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0x03))) { revert(0, 0); } else {
                                    mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                    codecopy(0, 0x0ce6, 0x20)
                                    mstore(0, mload(0))
                                    mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                    mstore(0x20, 0x04)
                                    sstore(sha3(0, 0x40), or(and(iszero(iszero(calldataload(0x24))), 0xff), and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00)))
                                    mstore(0x80, iszero(iszero(calldataload(0x24))))
                                    log2(mload(0x40), 0x20, mload(0), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                                }
                            }
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
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x40) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(calldataload(0x24), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                if sub(caller(), and(0xffffffffffffffffffffffffffffffffffffffff, sload(0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103))) { revert(mload(0x40), 0x04); } else {
                                    mstore(0x80, 0xc031a0df00000000000000000000000000000000000000000000000000000000)
                                    if iszero(and(sload(0x05), 0xff)) {
                                        if and(sload(0x05), 0xff) { revert(mload(0x40), 0x04); } else {
                                            mstore(0x80, 0x3f733c4f00000000000000000000000000000000000000000000000000000000)
                                            if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04))) {
                                                sstore(0x03, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x03))))
                                                sstore(0x05, or(0x01, and(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00, sload(0x05))))
                                                codecopy(0, 0x0d26, 0x20)
                                                mstore(0, mload(0))
                                                log2(0, 0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x04)))
                                                if and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff) { revert(0, 0); } else {
                                                    codecopy(0, 0x0ce6, 0x20)
                                                    mstore(0, mload(0))
                                                    mstore(0, and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
                                                    mstore(0x20, 0x04)
                                                    sstore(sha3(0, 0x40), or(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00), 0x01))
                                                    mstore(0x80, 0x01)
                                                    log2(mload(0x40), 0x20, mload(0), and(calldataload(0x24), 0xffffffffffffffffffffffffffffffffffffffff))
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
                                                        sstore(0, or(and(0xffffffffffffffffffffffffffffffffffffffff0000, shl(0x10, calldataload(0x04))), and(0xffffffffffffffffffff0000000000000000000000000000000000000000ffff, sload(0))))
                                                        sstore(0x01, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x24)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x01))))
                                                        sstore(0x02, or(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x44)), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x02))))
                                                        if iszero(and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x64))) {
                                                            sstore(0x03, or(and(sload(0x03), 0xffffffffffffffffffffffff0000000000000000000000000000000000000000), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x64))))
                                                            sstore(0x05, or(and(sload(0x05), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00), 0x01))
                                                            codecopy(0, 0x0d26, 0x20)
                                                            mstore(0, mload(0))
                                                            log2(0, 0, mload(0), and(0xffffffffffffffffffffffffffffffffffffffff, calldataload(0x64)))
                                                            if and(calldataload(0x84), 0xffffffffffffffffffffffffffffffffffffffff) {
                                                                codecopy(0, 0x0ce6, 0x20)
                                                                mstore(0, mload(0))
                                                                mstore(0, and(calldataload(0x84), 0xffffffffffffffffffffffffffffffffffffffff))
                                                                mstore(0x20, 0x04)
                                                                sstore(sha3(0, 0x40), or(and(sload(sha3(0, 0x40)), 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00), 0x01))
                                                                mstore(0x80, 0x01)
                                                                log2(mload(0x40), 0x20, mload(0), and(calldataload(0x84), 0xffffffffffffffffffffffffffffffffffffffff))
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
            * @custom:signature    Unresolved_f2fde38b(address arg0) public payable
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0xf2fde38b {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            if sub(caller(), and(sload(0x03), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                                mstore(0x80, 0x30cd747100000000000000000000000000000000000000000000000000000000)
                                sstore(0x03, or(and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff), and(0xffffffffffffffffffffffff0000000000000000000000000000000000000000, sload(0x03))))
                                codecopy(0, 0x0d26, 0x20)
                                mstore(0, mload(0))
                                log2(0, 0, mload(0), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            }
                        }
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
            * @custom:signature    Unresolved_d5c539ce() public view returns (address)
            */
            case 0xd5c539ce {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0) { revert(0, 0); } else {
                        mstore(0x80, and(sload(0x02), 0xffffffffffffffffffffffffffffffffffffffff))
                        return(mload(0x40), 0x20)
                    }
                }
            }
            
            /*
            * @custom:signature    Unresolved_29e295c5(address arg0) public view returns (bool)
            * @param                arg0 ["address", "uint160", "bytes20", "int160"]
            */
            case 0x29e295c5 {
                if callvalue() { revert(0, 0); } else {
                    if slt(add(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc, calldatasize()), 0x20) {
                        if sub(calldataload(0x04), and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff)) { revert(0, 0); } else {
                            mstore(0, and(calldataload(0x04), 0xffffffffffffffffffffffffffffffffffffffff))
                            mstore(0x20, 0x04)
                            mstore(0x80, iszero(iszero(and(sload(sha3(0, 0x40)), 0xff))))
                            return(mload(0x40), 0x20)
                        }
                    }
                }
            }
            default { revert(0, 0) }
        }
    }
}