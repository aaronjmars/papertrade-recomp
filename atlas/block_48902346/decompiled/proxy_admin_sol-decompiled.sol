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
    address public unresolved_8da5cb5b;
    
    event Event_4ffd725f();
    error CustomError_00000000();
    
    /// @custom:selector    0x7eff275e
    /// @custom:signature   Unresolved_7eff275e(address arg0, address arg1) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_7eff275e(address arg0, address arg1) public payable returns (uint256) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        require(!address(arg0).code.length);
        address var_b = address(arg1);
        (bool success, bytes memory ret0) = address(arg0).Unresolved_8f283970(var_b); // call
        return ;
        require(var_c > 0xffffffffffffffff);
    }
    
    /// @custom:selector    0x9623609d
    /// @custom:signature   Unresolved_9623609d(address arg0, address arg1, uint256 arg2) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    function Unresolved_9623609d(address arg0, address arg1, uint256 arg2) public payable returns (uint256) {
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(arg2 > 0xffffffffffffffff);
        require(!(arg2 + 0x23) < msg.data.length);
        require(arg2 > 0xffffffffffffffff);
        require(((arg2 + (arg2)) + 0x24) > msg.data.length, CustomError_30cd7471());
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        require(!address(arg0).code.length);
        address var_b = address(arg1);
        (bool success, bytes memory ret0) = address(arg0).{ value: msg.value }Unresolved_4f1ef286(var_b); // call
        return ;
        require(var_g > 0xffffffffffffffff);
        require(0);
        return ;
    }
    
    /// @custom:selector    0xf2fde38b
    /// @custom:signature   Unresolved_f2fde38b(address arg0) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_f2fde38b(address arg0) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        require(!(address(arg0)), CustomError_49e27cff());
        unresolved_8da5cb5b = (address(arg0)) | (uint96(unresolved_8da5cb5b));
        emit Event_4ffd725f(address(arg0));
        return ;
    }
    
    /// @custom:selector    0x99a88ec4
    /// @custom:signature   Unresolved_99a88ec4(address arg0, address arg1) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_99a88ec4(address arg0, address arg1) public payable returns (uint256) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        require(!address(arg0).code.length);
        address var_b = address(arg1);
        (bool success, bytes memory ret0) = address(arg0).Unresolved_4f1ef286(var_b); // call
        return ;
        require(var_e > 0xffffffffffffffff);
        require(0);
        return ;
    }
}