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
    mapping(bytes32 => bytes32) storage_map_d;
    uint256 public unresolved_c63c4e9b;
    address public unresolved_8da5cb5b;
    mapping(bytes32 => bytes32) storage_map_b;
    
    event Event_cf0f63b9();
    event Event_25cd0ae9();
    error CustomError_00000000();
    event Event_78f3bc93();
    
    /// @custom:selector    0x2ab0f529
    /// @custom:signature   Unresolved_2ab0f529(uint256 arg0) public view returns (uint256)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_2ab0f529(uint256 arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        uint256 var_a = arg0;
        return storage_map_b[var_a] == 0x01;
    }
    
    /// @custom:selector    0x6cb6a1f7
    /// @custom:signature   Unresolved_6cb6a1f7(uint256 arg0) public view returns (uint256)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_6cb6a1f7(uint256 arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        uint256 var_a = arg0;
        return storage_map_b[var_a];
    }
    
    /// @custom:selector    0x88aa4c12
    /// @custom:signature   Unresolved_88aa4c12(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    function Unresolved_88aa4c12(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable {
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x80);
        require(arg0 - (address(arg0)));
        require(arg2 > 0xffffffffffffffff);
        require(!(arg2 + 0x23) < msg.data.length);
        require(arg2 > 0xffffffffffffffff);
        require(((arg2 + (arg2)) + 0x24) > msg.data.length, CustomError_30cd7471());
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        require(arg2 > 0xffffffffffffffff, CustomError_18d96a80());
        require(((var_d + (uint248((0x20 + (0x1f + (arg2))) + 0x1f))) < var_d) | ((var_d + (uint248((0x20 + (0x1f + (arg2))) + 0x1f))) > 0xffffffffffffffff), CustomError_18d96a80());
        uint256 var_d = var_d + (uint248((0x20 + (0x1f + (arg2))) + 0x1f));
        uint256 var_a = (arg2);
        require((0x24 + arg2) + var_a > msg.data.length, CustomError_18d96a80());
        var_e = msg.data[36:36];
        require(((var_d + 0xa0) > 0xffffffffffffffff) | ((var_d + 0xa0) < var_d), CustomError_18d96a80());
        var_b = keccak256(var_e);
        require(!storage_map_d[var_b], CustomError_18d96a80());
        require(storage_map_d[var_b] == 0x01, CustomError_18d96a80());
        require(block.timestamp < storage_map_d[var_b], CustomError_f800799b());
        require(msg.value - arg1, CustomError_aa7feadc());
        var_b = keccak256(var_e);
        storage_map_d[var_b] = 0x01;
        (bool success, bytes memory ret0) = address(arg0).transfer(arg1);
        require(!ret0.length, CustomError_15fcd675());
        require(0 < var_p, CustomError_15fcd675());
    }
    
    /// @custom:selector    0x584b153e
    /// @custom:signature   Unresolved_584b153e(uint256 arg0) public view returns (bool)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_584b153e(uint256 arg0) public view returns (bool) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        uint256 var_a = arg0;
        require(storage_map_b[var_a] > 0x01);
        return !(!block.timestamp < storage_map_b[var_a]);
        return !(!storage_map_b[var_a] > 0x01);
    }
    
    /// @custom:selector    0x13bc9f20
    /// @custom:signature   Unresolved_13bc9f20(uint256 arg0) public view returns (bool)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_13bc9f20(uint256 arg0) public view returns (bool) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        uint256 var_a = arg0;
        require(storage_map_b[var_a] > 0x01);
        return !(block.timestamp < storage_map_b[var_a]);
        return !(!storage_map_b[var_a] > 0x01);
    }
    
    /// @custom:selector    0x8a99d586
    /// @custom:signature   Unresolved_8a99d586(uint256 arg0) public payable
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_8a99d586(uint256 arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20, CustomError_29c3b7ee());
        require(msg.sender - address(this), CustomError_29c3b7ee());
        unresolved_c63c4e9b = arg0;
        emit Event_25cd0ae9(arg0);
    }
    
    /// @custom:selector    0xa6cc2c8c
    /// @custom:signature   Unresolved_a6cc2c8c(uint256 arg0, uint256 arg1, uint256 arg2) public pure
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    function Unresolved_a6cc2c8c(uint256 arg0, uint256 arg1, uint256 arg2) public pure {
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x80);
        require(arg0 > 0xffffffffffffffff);
        require(arg0 > 0xffffffffffffffff);
        require(arg1 > 0xffffffffffffffff);
        require(arg1 > 0xffffffffffffffff);
        require(arg2 > 0xffffffffffffffff);
    }
    
    /// @custom:selector    0xc4d252f5
    /// @custom:signature   Unresolved_c4d252f5(uint256 arg0) public payable
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_c4d252f5(uint256 arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20, CustomError_30cd7471());
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        uint256 var_b = arg0;
        require(!storage_map_d[var_b], CustomError_18d96a80());
        require(0x01 == storage_map_d[var_b], CustomError_18d96a80());
        var_b = arg0;
        storage_map_d[var_b] = 0;
        emit Event_cf0f63b9(arg0);
    }
    
    /// @custom:selector    0x8b07f62b
    /// @custom:signature   Unresolved_8b07f62b(uint256 arg0, uint256 arg1, uint256 arg2) public pure
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    function Unresolved_8b07f62b(uint256 arg0, uint256 arg1, uint256 arg2) public pure {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x80);
        require(arg0 > 0xffffffffffffffff);
        require(arg0 > 0xffffffffffffffff);
        require(arg1 > 0xffffffffffffffff);
        require(arg1 > 0xffffffffffffffff);
        require(arg2 > 0xffffffffffffffff);
    }
    
    /// @custom:selector    0xec2a5b45
    /// @custom:signature   Unresolved_ec2a5b45(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public pure returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    function Unresolved_ec2a5b45(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public pure returns (uint256) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x80);
        require(arg0 - (address(arg0)));
        require(arg2 > 0xffffffffffffffff);
        require(!(arg2 + 0x23) < msg.data.length);
        require(arg2 > 0xffffffffffffffff);
        require(((arg2 + (arg2)) + 0x24) > msg.data.length);
        require(arg2 > 0xffffffffffffffff);
        require(((var_c + (uint248((0x20 + (0x1f + (arg2))) + 0x1f))) < var_c) | ((var_c + (uint248((0x20 + (0x1f + (arg2))) + 0x1f))) > 0xffffffffffffffff));
        uint256 var_c = var_c + (uint248((0x20 + (0x1f + (arg2))) + 0x1f));
        uint256 var_d = (arg2);
        require((0x24 + arg2) + var_d > msg.data.length);
        var_e = msg.data[36:36];
        require(((var_c + 0xa0) > 0xffffffffffffffff) | ((var_c + 0xa0) < var_c));
        return keccak256(var_e);
    }
    
    /// @custom:selector    0x04d2cd0e
    /// @custom:signature   Unresolved_04d2cd0e(uint256 arg0, uint256 arg1, uint256 arg2) public pure
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    function Unresolved_04d2cd0e(uint256 arg0, uint256 arg1, uint256 arg2) public pure {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x80);
        require(arg0 > 0xffffffffffffffff);
        require(arg0 > 0xffffffffffffffff);
        require(arg1 > 0xffffffffffffffff);
        require(arg1 > 0xffffffffffffffff);
        require(arg2 > 0xffffffffffffffff);
    }
    
    /// @custom:selector    0xb0e58bc9
    /// @custom:signature   Unresolved_b0e58bc9(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    function Unresolved_b0e58bc9(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable returns (uint256) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x80);
        require(arg0 - (address(arg0)));
        require(arg2 > 0xffffffffffffffff);
        require(!(arg2 + 0x23) < msg.data.length);
        require(arg2 > 0xffffffffffffffff);
        require(((arg2 + (arg2)) + 0x24) > msg.data.length, CustomError_30cd7471());
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        require(arg2 > 0xffffffffffffffff, CustomError_9b382476());
        require(((var_d + (uint248((0x20 + (0x1f + (arg2))) + 0x1f))) < var_d) | ((var_d + (uint248((0x20 + (0x1f + (arg2))) + 0x1f))) > 0xffffffffffffffff), CustomError_9b382476());
        uint256 var_d = var_d + (uint248((0x20 + (0x1f + (arg2))) + 0x1f));
        uint256 var_a = (arg2);
        require((0x24 + arg2) + var_a > msg.data.length, CustomError_9b382476());
        var_e = msg.data[36:36];
        require(((var_d + 0xa0) > 0xffffffffffffffff) | ((var_d + 0xa0) < var_d), CustomError_9b382476());
        var_b = keccak256(var_e);
        require(storage_map_d[var_b], CustomError_9b382476());
        require(block.timestamp > (block.timestamp + unresolved_c63c4e9b));
        var_b = keccak256(var_e);
        storage_map_d[var_b] = block.timestamp + unresolved_c63c4e9b;
        var_b = keccak256(var_e);
        emit Event_78f3bc93(keccak256(var_e), address(arg0), arg1, 0x80, arg3, storage_map_d[var_b], (arg2));
        return keccak256(var_e);
    }
}