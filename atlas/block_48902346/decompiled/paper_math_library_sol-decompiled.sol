// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

/// @title            Decompiled Contract
/// @author           Jonathan Becker <jonathan@jbecker.dev>
/// @custom:version   heimdall-rs v0.9.2
///
/// @notice           This contract was decompiled using the heimdall-rs decompiler.
///                     It was generated directly by tracing the EVM opcodes from this contract.
///                     As a result, it may not compile or even be valid solidity code.
///                     Despite this, it should be obvious what each function does. Overall
///                     logic should have been preserved throughout decompiling.
///
/// @custom:github    You can find the open-source decompiler here:
///                       https://heimdall.rs

contract DecompiledContract {
    
    /// @custom:selector    0x7aac24ba
    /// @custom:signature   Unresolved_7aac24ba(uint256 arg0, uint256 arg1, uint256 arg2, uint256 arg3, uint256 arg4, uint256 arg5) public pure returns (bytes memory)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    /// @param              arg5 ["uint256", "bytes32", "int256"]
    function Unresolved_7aac24ba(uint256 arg0, uint256 arg1, uint256 arg2, uint256 arg3, uint256 arg4, uint256 arg5) public pure returns (bytes memory) {
        if ((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xc0) {
            require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xc0);
            require(!arg2);
            require((!arg0 < 0) & ((arg0 + arg2) < arg2) | ((arg0 < 0) & (!(arg0 + arg2) < arg2)));
            require(arg0 < arg3);
            require(!(arg0 + arg2) < arg3);
            require(((arg0 + arg2) - arg0) < (arg0 + arg2) & (0 > arg0) | (((arg0 + arg2) - arg0) > (arg0 + arg2) & (!0 > arg0)));
            require(!((((arg0 + arg2) - arg0) * arg4) / ((arg0 + arg2) - arg0) == arg4) | (!(arg0 + arg2) - arg0));
            require(0 > (0 + ((((arg0 + arg2) - arg0) * arg4) / 0x0de0b6b3a7640000)));
            require((arg0 + arg2) > arg3);
        }
        return abi.encodePacked(0 + ((((arg0 + arg2) - arg0) * arg4) / 0x0de0b6b3a7640000), 0);
        return abi.encodePacked(0, 0);
    }
}