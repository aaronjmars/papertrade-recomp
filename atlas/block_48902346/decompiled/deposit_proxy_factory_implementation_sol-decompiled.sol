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
    mapping(bytes32 => bytes32) storage_map_a;
    bytes32 store_e;
    address public unresolved_8da5cb5b;
    address public unresolved_d2f7265a;
    mapping(bytes32 => bytes32) storage_map_f;
    address public unresolved_03b802b6;
    
    event Event_4ffd725f();
    event Event_09bdaf5f();
    error CustomError_00000000();
    event Event_3d2489ef();
    
    /// @custom:selector    0xc4d66de8
    /// @custom:signature   Unresolved_c4d66de8(address arg0) public pure
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_c4d66de8(address arg0) public pure {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
    }
    
    /// @custom:selector    0x29710388
    /// @custom:signature   Unresolved_29710388(address arg0) public view returns (bool)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_29710388(address arg0) public view returns (bool) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return !(!bytes1(storage_map_a[var_a]));
    }
    
    /// @custom:selector    0xd600539a
    /// @custom:signature   Unresolved_d600539a(address arg0) public view
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_d600539a(address arg0) public view {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x20);
        require(arg0 - (address(arg0)));
        require(((var_c + 0x40) > 0xffffffffffffffff) | ((var_c + 0x40) < var_c));
        uint256 var_c = var_c + 0x40;
        require(((var_c + 0x0760) < var_c) | ((var_c + 0x0760) > 0xffffffffffffffff));
        var_c = var_c + 0x0760;
        require(((var_c + (uint248(((0x40 + (var_c + 0x20)) - var_c) + 0x1f))) < var_c) | ((var_c + (uint248(((0x40 + (var_c + 0x20)) - var_c) + 0x1f))) > 0xffffffffffffffff));
    }
    
    /// @custom:selector    0x56e8d85b
    /// @custom:signature   Unresolved_56e8d85b(address arg0, address arg1, address arg2) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_56e8d85b(address arg0, address arg1, address arg2) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(arg2 - (address(arg2)));
        require(bytes1(unresolved_d2f7265a), CustomError_40892c33());
        require(!(bytes1(unresolved_d2f7265a >> 0x08)), CustomError_40892c33());
        require(!(bytes1(unresolved_d2f7265a >> 0x08)), CustomError_40892c33());
        require(!(address(arg1)), CustomError_40892c33());
        require(!(address(arg0)), CustomError_40892c33());
        unresolved_d2f7265a = (uint96(unresolved_d2f7265a)) | (address(arg0 << 0x10));
        unresolved_8da5cb5b = (uint96(unresolved_8da5cb5b)) | (address(arg1));
        unresolved_03b802b6 = (uint96(unresolved_03b802b6)) | (address(arg2));
        emit Event_4ffd725f(address(arg1));
        emit Event_09bdaf5f(address(arg2));
        require(!(bytes1(unresolved_d2f7265a >> 0x08)), CustomError_40892c33());
        unresolved_d2f7265a = uint248(unresolved_d2f7265a);
        require(bytes1(unresolved_d2f7265a), CustomError_0dc149f0());
    }
    
    /// @custom:selector    0xc1a9a508
    /// @custom:signature   Unresolved_c1a9a508(address arg0) public view returns (address)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_c1a9a508(address arg0) public view returns (address) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return address(storage_map_a[var_a]);
    }
    
    /// @custom:selector    0x0f71c8bc
    /// @custom:signature   Unresolved_0f71c8bc(address arg0, address arg1) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_0f71c8bc(address arg0, address arg1) public payable {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(msg.sender - (address(store_e)), CustomError_c031a0df());
        require(address(unresolved_8da5cb5b), CustomError_3f733c4f());
        require(!(address(arg0)), CustomError_40892c33());
        require(!(address(unresolved_d2f7265a >> 0x10)), CustomError_40892c33());
        unresolved_d2f7265a = (uint96(unresolved_d2f7265a)) | (address((unresolved_d2f7265a >> 0x10) << 0x10));
        unresolved_8da5cb5b = (uint96(unresolved_8da5cb5b)) | (address(arg0));
        unresolved_03b802b6 = (uint96(unresolved_03b802b6)) | (address(arg1));
        emit Event_4ffd725f(address(arg0));
        emit Event_09bdaf5f(address(arg1));
    }
    
    /// @custom:selector    0xc6f881bc
    /// @custom:signature   Unresolved_c6f881bc(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_c6f881bc(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        unresolved_03b802b6 = (address(arg0)) | (uint96(unresolved_03b802b6));
        emit Event_09bdaf5f(address(arg0));
    }
    
    /// @custom:selector    0xf2fde38b
    /// @custom:signature   Unresolved_f2fde38b(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_f2fde38b(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        require(!(address(arg0)), CustomError_904bc503());
        unresolved_8da5cb5b = (address(arg0)) | (uint96(unresolved_8da5cb5b));
        emit Event_4ffd725f(address(arg0));
    }
    
    /// @custom:selector    0xcbd433f4
    /// @custom:signature   Unresolved_cbd433f4(address arg0) public payable returns (address)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_cbd433f4(address arg0) public payable returns (address) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(!(msg.sender == (address(unresolved_8da5cb5b))), CustomError_27fba80a());
        require(!(msg.sender == (address(unresolved_03b802b6))), CustomError_27fba80a());
        require(!address(unresolved_d2f7265a >> 0x10));
        address var_b = address(arg0);
        require(address(storage_map_f[var_b]));
        return address(storage_map_f[var_b]);
        require(((var_e + 0x40) > 0xffffffffffffffff) | ((var_e + 0x40) < var_e));
        uint256 var_e = var_e + 0x40;
        require(((var_e + 0x0721) > 0xffffffffffffffff) | ((var_e + 0x0721) < var_e));
        assembly { addr := create(0, var_e, (0x40 + (var_e + 0x0721)) - var_e, keccak256(var_j)) }
        require(!245);
        var_b = address(arg0);
        storage_map_f[var_b] = (uint96(storage_map_f[var_b])) | (address(245));
        var_b = address(245);
        storage_map_f[var_b] = (uint248(storage_map_f[var_b])) | 0x01;
        emit Event_3d2489ef(address(arg0), address(245));
        return address(245);
    }
}