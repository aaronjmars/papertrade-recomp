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
    uint256 public constant unresolved_82e717f7 = 2;
    
    mapping(bytes32 => bytes32) storage_map_l;
    mapping(bytes32 => bytes32) storage_map_p;
    mapping(bytes32 => bytes32) storage_map_r;
    mapping(bytes32 => bytes32) storage_map_c;
    mapping(bytes32 => bytes32) storage_map_f;
    uint256 public unresolved_900cf0cf;
    address public unresolved_64d62769;
    mapping(bytes32 => bytes32) storage_map_g;
    mapping(bytes32 => bytes32) storage_map_e;
    address public unresolved_1a5f66c3;
    uint256 public unresolved_b77bf600;
    mapping(bytes32 => bytes32) storage_map_b;
    mapping(bytes32 => bytes32) storage_map_n;
    address public unresolved_d98f851a;
    mapping(bytes32 => bytes32) storage_map_q;
    mapping(bytes32 => bytes32) storage_map_o;
    mapping(bytes32 => bytes32) storage_map_d;
    mapping(bytes32 => bytes32) storage_map_k;
    
    event Event_ddfe9ff9();
    event Event_be411f07();
    event Event_4c4e829c();
    error CustomError_00000000();
    
    /// @custom:selector    0x9ace38c2
    /// @custom:signature   Unresolved_9ace38c2(uint256 arg0) public view returns (bytes memory)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_9ace38c2(uint256 arg0) public view returns (bytes memory) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        uint256 var_a = arg0;
        require(!bytes1(storage_map_b[var_a]));
        require(((storage_map_b[var_a] >> 0x01) < 0x20) == (bytes1(storage_map_b[var_a])));
        var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(0 == (bytes1(storage_map_b[var_a])));
        require(0x01 == (bytes1(storage_map_b[var_a])));
        var_a = keccak256(var_a) + 0x02;
        require(0 < (storage_map_b[var_a] >> 0x01));
        require(((var_e + (uint248((((var_e + 0) + 0x20) - var_e) + 0x1f))) < var_e) | ((var_e + (uint248((((var_e + 0) + 0x20) - var_e) + 0x1f))) > 0xffffffffffffffff));
        var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        uint248 var_e = var_e + (uint248((((var_e + 0) + 0x20) - var_e) + 0x1f));
        require(!(bytes1(storage_map_g[var_a])) < 0x03);
        var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        return abi.encodePacked(address(storage_map_c[var_a]), storage_map_d[var_a], 0xc0, address(storage_map_e[var_a]), storage_map_f[var_a], bytes1(storage_map_g[var_a]), var_e.length);
        require(((var_e + (uint248((0 - var_e) + 0x1f))) < var_e) | ((var_e + (uint248((0 - var_e) + 0x1f))) > 0xffffffffffffffff));
    }
    
    /// @custom:selector    0x735631ad
    /// @custom:signature   Unresolved_735631ad(uint256 arg0) public payable
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_735631ad(uint256 arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20, CustomError_a1b035c8());
        require(!(address(msg.sender) == (address(unresolved_d98f851a))), CustomError_a1b035c8());
        require(!(address(msg.sender) == (address(unresolved_1a5f66c3))), CustomError_a1b035c8());
        require(!(address(unresolved_64d62769) == (address(msg.sender))), CustomError_a1b035c8());
        require(!(arg0 < unresolved_b77bf600), CustomError_c5446884());
        uint256 var_b = arg0;
        require(address(storage_map_k[var_b]) - msg.sender, CustomError_c5446884());
        require(!(bytes1(storage_map_l[var_b]) < 0x03), CustomError_82235d53());
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(bytes1(storage_map_l[var_b]), CustomError_82235d53());
        storage_map_l[var_b] = 0x02 | (uint248(storage_map_l[var_b]));
        emit Event_4c4e829c(arg0);
    }
    
    /// @custom:selector    0xc6427474
    /// @custom:signature   Unresolved_c6427474(address arg0, uint256 arg1, uint256 arg2) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    function Unresolved_c6427474(address arg0, uint256 arg1, uint256 arg2) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (address(arg0)));
        require(arg2 > 0xffffffffffffffff);
        require(!(arg2 + 0x23) < msg.data.length);
        require(arg2  > 0xffffffffffffffff);
        require(((arg2 + (arg2)) + 0x24) > msg.data.length, CustomError_a1b035c8());
        require(!(address(msg.sender) == (address(unresolved_d98f851a))), CustomError_a1b035c8());
        require(!(address(msg.sender) == (address(unresolved_1a5f66c3))), CustomError_a1b035c8());
        require(!(address(unresolved_64d62769) == (address(msg.sender))), CustomError_a1b035c8());
        require(unresolved_b77bf600 == 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
        unresolved_b77bf600 = unresolved_b77bf600 + 0x01;
        require(((var_d + 0xc0) < var_d) | ((var_d + 0xc0) > 0xffffffffffffffff));
        uint256 var_d = var_d + 0xc0;
        require(arg2 > 0xffffffffffffffff);
        require(((var_d + (uint248((0x20 + (0x1f + (arg2))) + 0x1f))) < var_d) | ((var_d + (uint248((0x20 + (0x1f + (arg2))) + 0x1f))) > 0xffffffffffffffff));
        var_d = var_d + (uint248((0x20 + (0x1f + (arg2))) + 0x1f));
        uint256 var_f = (arg2);
        require((arg2 + 0x24) + var_f > msg.data.length);
        var_g = msg.data[36:36];
        var_b = unresolved_b77bf600;
        storage_map_n[var_b] = (address(var_d.length)) | (uint96(storage_map_n[var_b]));
        storage_map_o[var_b] = var_g;
        require(var_n > 0xffffffffffffffff);
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(!bytes1(storage_map_p[var_b]));
        require(((storage_map_p[var_b] >> 0x01) < 0x20) == (bytes1(storage_map_p[var_b])));
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require((storage_map_p[var_b] >> 0x01) > 0x1f);
        uint256 var_b = keccak256(var_b) + 0x02;
        require(var_n < 0x20);
        require(keccak256(var_b) + ((var_n + 0x1f) >> 0x05) < (keccak256(var_b) + (((storage_map_p[var_b] >> 0x01) + 0x1f) >> 0x05)));
        require(0x01 == (var_n > 0x1f));
        var_b = keccak256(var_b) + 0x02;
        require(0 < (uint248(var_n)));
        require(uint248(var_n) < (var_n));
        storage_map_n[var_b] = (~(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff >> (bytes1(var_n << 0x03)))) & (var_o);
        storage_map_p[var_b] = (var_n << 0x01) + 0x01;
        storage_map_k[var_b] = (uint96(storage_map_k[var_b])) | (address(var_p));
        storage_map_q[var_b] = var_q;
        require(!(var_r) < 0x03);
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        storage_map_r[var_b] = (bytes1(var_r)) | (uint248(storage_map_r[var_b]));
        require(arg2 > 0xffffffffffffffff);
        require(((var_d + (uint248((0x20 + (0x1f + (arg2))) + 0x1f))) < var_d) | ((var_d + (uint248((0x20 + (0x1f + (arg2))) + 0x1f))) > 0xffffffffffffffff));
        var_d = var_d + (uint248((0x20 + (0x1f + (arg2))) + 0x1f));
        require((arg2 + 0x24) + var_f > msg.data.length);
        var_g = msg.data[36:36];
        require(((var_d + 0x0100) > 0xffffffffffffffff) | ((var_d + 0x0100) < var_d));
        emit Event_be411f07(unresolved_b77bf600, msg.sender, address(arg0), arg1, 0x60, keccak256(var_g), (arg2));
        return unresolved_b77bf600;
        if (var_n) {
        }
    }
    
    /// @custom:selector    0x7b1106de
    /// @custom:signature   Unresolved_7b1106de(uint256 arg0, uint256 arg1) public payable
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    function Unresolved_7b1106de(uint256 arg0, uint256 arg1) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x40, CustomError_a1b035c8());
        require(!(address(msg.sender) == (address(unresolved_d98f851a))), CustomError_a1b035c8());
        require(!(address(msg.sender) == (address(unresolved_1a5f66c3))), CustomError_a1b035c8());
        require(!(address(unresolved_64d62769) == (address(msg.sender))), CustomError_a1b035c8());
        require(!(arg0 < unresolved_b77bf600), CustomError_82235d53());
        uint256 var_b = arg0;
        require(!(bytes1(storage_map_r[var_b]) < 0x03), CustomError_82235d53());
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(bytes1(storage_map_r[var_b]), CustomError_82235d53());
        require(storage_map_q[var_b] - unresolved_900cf0cf, CustomError_e1577073());
        require(msg.sender == (address(storage_map_k[var_b])), CustomError_15fcd675());
        require(!(bytes1(storage_map_p[var_b])), CustomError_15fcd675());
        require(((storage_map_p[var_b] >> 0x01) < 0x20) == (bytes1(storage_map_p[var_b])), CustomError_15fcd675());
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(0 == (bytes1(storage_map_p[var_b])), CustomError_15fcd675());
        require(0x01 == (bytes1(storage_map_p[var_b])), CustomError_15fcd675());
        var_b = keccak256(var_b) + 0x02;
        require(0 < (storage_map_p[var_b] >> 0x01), CustomError_15fcd675());
        require(((var_e + (uint248((((var_e + 0) + 0x20) - var_e) + 0x1f))) < var_e) | ((var_e + (uint248((((var_e + 0) + 0x20) - var_e) + 0x1f))) > 0xffffffffffffffff), CustomError_15fcd675());
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        uint248 var_e = var_e + (uint248((((var_e + 0) + 0x20) - var_e) + 0x1f));
        require(((var_e + 0x0100) > 0xffffffffffffffff) | ((var_e + 0x0100) < var_e), CustomError_15fcd675());
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        var_e = var_e + 0x0100;
        require(keccak256(var_l) - arg1, CustomError_15fcd675());
        storage_map_r[var_b] = (uint248(storage_map_r[var_b])) | 0x01;
        (bool success, bytes memory ret0) = address(storage_map_n[var_b]).transfer(storage_map_o[var_b]);
        require(!ret0.length, CustomError_15fcd675());
        require(0 < var_r, CustomError_15fcd675());
        require(ret0.length > 0xffffffffffffffff, CustomError_4e11f906());
        require(((var_e + (uint248((0 - var_e) + 0x1f))) < var_e) | ((var_e + (uint248((0 - var_e) + 0x1f))) > 0xffffffffffffffff), CustomError_137b4559());
    }
    
    /// @custom:selector    0x7df73e27
    /// @custom:signature   Unresolved_7df73e27(address arg0) public view returns (bool)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_7df73e27(address arg0) public view returns (bool) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(!(address(arg0)) == (address(unresolved_d98f851a)));
        require(!(address(arg0)) == (address(unresolved_1a5f66c3)));
        return !(!(address(unresolved_64d62769)) == (address(arg0)));
        return !(!(address(arg0)) == (address(unresolved_1a5f66c3)));
    }
    
    /// @custom:selector    0x79301c0f
    /// @custom:signature   Unresolved_79301c0f(address arg0, address arg1, address arg2) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_79301c0f(address arg0, address arg1, address arg2) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(arg2 - (address(arg2)));
        require(msg.sender - address(this), CustomError_29c3b7ee());
        require(unresolved_900cf0cf > (unresolved_900cf0cf + 0x01), CustomError_815e1d64());
        unresolved_900cf0cf = unresolved_900cf0cf + 0x01;
        require(!(!address(arg0)), CustomError_815e1d64());
        require(!(!address(arg1)), CustomError_815e1d64());
        require(!(address(arg2)), CustomError_815e1d64());
        require(!(address(arg0) == (address(arg1))), CustomError_815e1d64());
        require(!(address(arg0) == (address(arg2))), CustomError_815e1d64());
        require(address(arg1) == (address(arg2)), CustomError_815e1d64());
        require(!(address(arg0) == address(this)), CustomError_815e1d64());
        require(!(address(arg1) == address(this)), CustomError_815e1d64());
        require(address(arg2) == address(this), CustomError_815e1d64());
        unresolved_d98f851a = (uint96(unresolved_d98f851a)) | (address(arg0));
        unresolved_1a5f66c3 = (uint96(unresolved_1a5f66c3)) | (address(arg1));
        unresolved_64d62769 = (uint96(unresolved_64d62769)) | (address(arg2));
        emit Event_ddfe9ff9(address(arg0), address(arg1), address(arg2), unresolved_900cf0cf + 0x01);
    }
    
    /// @custom:selector    0x27865bb3
    /// @custom:signature   Unresolved_27865bb3(uint256 arg0) public view returns (uint256)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_27865bb3(uint256 arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20, CustomError_500a07ce());
        require(!(arg0 < unresolved_b77bf600), CustomError_500a07ce());
        uint256 var_a = arg0;
        require(!(bytes1(storage_map_b[var_a])), CustomError_500a07ce());
        require(((storage_map_b[var_a] >> 0x01) < 0x20) == (bytes1(storage_map_b[var_a])), CustomError_500a07ce());
        var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(0 == (bytes1(storage_map_b[var_a])), CustomError_500a07ce());
        require(0x01 == (bytes1(storage_map_b[var_a])), CustomError_500a07ce());
        var_a = keccak256(var_a) + 0x02;
        require(0 < (storage_map_b[var_a] >> 0x01), CustomError_500a07ce());
        require(((var_e + (uint248((((var_e + 0) + 0x20) - var_e) + 0x1f))) < var_e) | ((var_e + (uint248((((var_e + 0) + 0x20) - var_e) + 0x1f))) > 0xffffffffffffffff), CustomError_500a07ce());
        var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        uint248 var_e = var_e + (uint248((((var_e + 0) + 0x20) - var_e) + 0x1f));
        require(((var_e + 0x0100) > 0xffffffffffffffff) | ((var_e + 0x0100) < var_e), CustomError_500a07ce());
        var_e = var_e + 0x0100;
        return keccak256(var_l);
        require(((var_e + (uint248((0 - var_e) + 0x1f))) < var_e) | ((var_e + (uint248((0 - var_e) + 0x1f))) > 0xffffffffffffffff), CustomError_500a07ce());
    }
}