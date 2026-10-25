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
    mapping(bytes32 => bytes32) storage_map_g;
    bool public unresolved_6090cf16;
    address public unresolved_d5c539ce;
    address public unresolved_0b826190;
    bytes32 store_h;
    mapping(bytes32 => bytes32) storage_map_c;
    address public unresolved_8da5cb5b;
    address public unresolved_d2f7265a;
    
    event Event_4ffd725f();
    event Event_9d65322d();
    error CustomError_00000000();
    event Event_431c9efc();
    
    /// @custom:selector    0xc0c53b8b
    /// @custom:signature   Unresolved_c0c53b8b(address arg0, address arg1, address arg2) public pure
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_c0c53b8b(address arg0, address arg1, address arg2) public pure {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(arg2 - (address(arg2)));
    }
    
    /// @custom:selector    0x251fb27d
    /// @custom:signature   Unresolved_251fb27d(uint256 arg0, uint256 arg1, uint256 arg2, uint256 arg3, uint256 arg4, uint256 arg5) public payable
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    /// @param              arg5 ["uint256", "bytes32", "int256"]
    function Unresolved_251fb27d(uint256 arg0, uint256 arg1, uint256 arg2, uint256 arg3, uint256 arg4, uint256 arg5) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(0xffffffffffffffff < arg0);
        require(!(arg0 + 0x23) < msg.data.length);
        require(arg0 > 0xffffffffffffffff);
        require(((arg0 + (arg0 << 0x05)) + 0x24) > msg.data.length);
        address var_a = msg.sender;
        require(!bytes1(storage_map_c[var_a]));
        require(msg.data.length > 0xffffffffffffffff);
        require(((var_d + (uint248((0x20 + (0x1f + msg.data.length)) + 0x1f))) < var_d) | ((var_d + (uint248((0x20 + (0x1f + msg.data.length)) + 0x1f))) > 0xffffffffffffffff));
        uint256 var_d = var_d + (uint248((0x20 + (0x1f + msg.data.length)) + 0x1f));
        require(arg0 > 0xffffffffffffffff);
        require(((var_d + (uint248((0x20 + (arg0 << 0x05)) + 0x1f))) < var_d) | ((var_d + (uint248((0x20 + (arg0 << 0x05)) + 0x1f))) > 0xffffffffffffffff));
        var_d = var_d + (uint248((0x20 + (arg0 << 0x05)) + 0x1f));
        require(arg0 > 0xffffffffffffffff);
        var_f = msg.data[4:4];
        require(0 < (arg0));
        require(!(msg.data[(arg0 + 0) + 0x24]) < ((msg.data.length - arg0) + 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff3d));
        require(msg.data[0x84 + (msg.data[(arg0 + 0) + 0x24] + arg0)]);
        require(0 < 0);
        require(var_i == (msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x84]));
        require(0x01);
        require(msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x24] - (address(msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x24])));
        require(!(msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44]) < ((msg.data.length - (0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0))) + 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe1));
        require(msg.data[(0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0)) + (msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44])] > 0xffffffffffffffff);
        require((0x20 + ((0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0)) + (msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44]))) > (msg.data.length - (msg.data[(0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0)) + (msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44])])));
        require(msg.data[(0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0)) + (msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44])] < 0x04);
        require(0x04 > (msg.data[(0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0)) + (msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44])]));
        require(address(msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x24]) == (address(unresolved_d2f7265a >> 0x10)));
        require(address(msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x24]) == (address(unresolved_0b826190)));
        require(address(unresolved_d5c539ce) == (address(msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x24])));
        require(!0);
        require(((var_d + 0x20) < var_d) | ((var_d + 0x20) > 0xffffffffffffffff));
        var_d = var_d + 0x20;
        require(var_d.length);
        require(msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x64] - (msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x64]));
        require(!msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x64]);
        require(0 == 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
        require(msg.data[0x84 + (msg.data[(arg0 + 0) + 0x24] + arg0)]);
        require(0 == 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
        require(msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x24] - (address(msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x24])));
        require(!(msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44]) < ((msg.data.length - (0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0))) + 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe1));
        require(msg.data[(0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0)) + (msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44])] > 0xffffffffffffffff);
        require((0x20 + ((0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0)) + (msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44]))) > (msg.data.length - (msg.data[(0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0)) + (msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44])])));
        (bool success, bytes memory ret0) = address(msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x24]).transfer(0);
        require(!ret0.length);
        require(msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x64] - (msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x64]));
        require(!msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x64]);
        require(0 == 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
        require(msg.data[0x84 + (msg.data[(arg0 + 0) + 0x24] + arg0)]);
        require(0 == 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
        require(ret0.length > 0xffffffffffffffff);
        require(((var_d + (uint248((0x20 + (0x1f + ret0.length)) + 0x1f))) < var_d) | ((var_d + (uint248((0x20 + (0x1f + ret0.length)) + 0x1f))) > 0xffffffffffffffff));
        var_d = var_d + (uint248((0x20 + (0x1f + ret0.length)) + 0x1f));
        require(msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x64] - (msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x64]));
        require(!msg.data[(arg0 + (msg.data[(arg0 + 0) + 0x24])) + 0x64]);
        require(0 == 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
        require(msg.data[0x84 + (msg.data[(arg0 + 0) + 0x24] + arg0)]);
        require(0 == 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
        if (((var_d + 0x60) > 0xffffffffffffffff) | ((var_d + 0x60) < var_d)) {
            var_d = var_d + 0x60;
            if (var_d.length) {
            }
            if (!(uint32(msg.data[0x20 + ((0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0)) + (msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44]))])) == 0x8311582500000000000000000000000000000000000000000000000000000000) {
                if (!(uint32(msg.data[0x20 + ((0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0)) + (msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44]))])) == 0x8311582500000000000000000000000000000000000000000000000000000000) {
                    if (!(uint32(msg.data[0x20 + ((0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0)) + (msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44]))])) == 0x8311582500000000000000000000000000000000000000000000000000000000) {
                    }
                }
            }
            if (!(uint32(msg.data[0x20 + ((0x24 + (msg.data[(arg0 + 0) + 0x24] + arg0)) + (msg.data[(msg.data[(arg0 + 0) + 0x24] + arg0) + 0x44]))])) == 0xec6783f000000000000000000000000000000000000000000000000000000000) {
                require(((var_d + 0x60) > 0xffffffffffffffff) | ((var_d + 0x60) < var_d));
            }
        }
        if (0) {
        }
        emit Event_9d65322d(keccak256(var_f), (arg0), 0, 0, 0);
    }
    
    /// @custom:selector    0x9011e5f9
    /// @custom:signature   Unresolved_9011e5f9(address arg0, uint256 arg1) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    function Unresolved_9011e5f9(address arg0, uint256 arg1) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x40);
        require(arg0 - (address(arg0)));
        require(arg1 - arg1);
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        address var_b = address(arg0);
        storage_map_g[var_b] = (bytes1(arg1)) | (uint248(storage_map_g[var_b]));
        emit Event_431c9efc(address(arg0), arg1);
    }
    
    /// @custom:selector    0x0f71c8bc
    /// @custom:signature   Unresolved_0f71c8bc(address arg0, address arg1) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_0f71c8bc(address arg0, address arg1) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x40);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(msg.sender - (address(store_h)), CustomError_c031a0df());
        require(!(bytes1(unresolved_6090cf16)), CustomError_3f733c4f());
        require(bytes1(unresolved_6090cf16), CustomError_3f733c4f());
        require(!(address(arg0)), CustomError_904bc503());
        unresolved_8da5cb5b = (address(arg0)) | (uint96(unresolved_8da5cb5b));
        unresolved_6090cf16 = 0x01 | (uint248(unresolved_6090cf16));
        emit Event_4ffd725f(address(arg0));
        require(address(arg1), CustomError_904bc503());
        address var_b = address(arg1);
        storage_map_g[var_b] = (uint248(storage_map_g[var_b])) | 0x01;
        emit Event_431c9efc(address(arg1), 0x01);
    }
    
    /// @custom:selector    0x9ccae24e
    /// @custom:signature   Unresolved_9ccae24e(address arg0, address arg1, address arg2, address arg3, address arg4) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg3 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg4 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_9ccae24e(address arg0, address arg1, address arg2, address arg3, address arg4) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xa0);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(arg2 - (address(arg2)));
        require(arg3 - (address(arg3)));
        require(arg4 - (address(arg4)));
        require(bytes1(unresolved_d2f7265a), CustomError_904bc503());
        require(!(bytes1(unresolved_d2f7265a >> 0x08)), CustomError_904bc503());
        require(!(bytes1(unresolved_d2f7265a >> 0x08)), CustomError_904bc503());
        unresolved_d2f7265a = (address(arg0 << 0x10)) | (uint96(unresolved_d2f7265a));
        unresolved_0b826190 = (address(arg1)) | (uint96(unresolved_0b826190));
        unresolved_d5c539ce = (address(arg2)) | (uint96(unresolved_d5c539ce));
        require(!(address(arg3)), CustomError_904bc503());
        unresolved_8da5cb5b = (uint96(unresolved_8da5cb5b)) | (address(arg3));
        unresolved_6090cf16 = (uint248(unresolved_6090cf16)) | 0x01;
        emit Event_4ffd725f(address(arg3));
        require(address(arg4), CustomError_904bc503());
        address var_a = address(arg4);
        storage_map_c[var_a] = (uint248(storage_map_c[var_a])) | 0x01;
        emit Event_431c9efc(address(arg4), 0x01);
        require(!(bytes1(unresolved_d2f7265a >> 0x08)), CustomError_904bc503());
        unresolved_d2f7265a = uint248(unresolved_d2f7265a);
        require(bytes1(unresolved_d2f7265a), CustomError_0dc149f0());
    }
    
    /// @custom:selector    0xf2fde38b
    /// @custom:signature   Unresolved_f2fde38b(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_f2fde38b(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        unresolved_8da5cb5b = (address(arg0)) | (uint96(unresolved_8da5cb5b));
        emit Event_4ffd725f(address(arg0));
    }
    
    /// @custom:selector    0x29e295c5
    /// @custom:signature   Unresolved_29e295c5(address arg0) public view returns (bool)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_29e295c5(address arg0) public view returns (bool) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return !(!bytes1(storage_map_c[var_a]));
    }
}